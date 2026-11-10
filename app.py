import hmac
import os
import re
import secrets
import sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from database import close_db, db, init

CATEGORIES = ("Associado", "Fundador", "Convidado", "Simpatizante")
STATES = [
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
]
CLUB_FIELDS = [
    ("name", "Nome do clube"),
    ("initials", "Sigla"),
    ("address", "Endereço"),
    ("district", "Bairro"),
    ("city", "Cidade"),
    ("uf", "UF"),
    ("phone", "Telefone"),
    ("email", "E-mail"),
    ("fee", "Mensalidade (R$)"),
]


class FormError(ValueError):
    pass


def field(name, limit=200):
    value = request.form.get(name, "").strip()
    if not value or len(value) > limit:
        raise FormError("Confira os campos obrigatórios e o tamanho do texto.")
    return value


def choice(name, options):
    value = field(name)
    if value not in options:
        raise FormError("Selecione uma opção válida.")
    return value


def email():
    value = field("email").lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise FormError("Informe um e-mail válido.")
    return value


def birth():
    value = field("birth")
    try:
        birthday = date.fromisoformat(value)
    except ValueError:
        raise FormError("Informe uma data de nascimento válida.")
    if birthday > date.today():
        raise FormError("O nascimento deve ser hoje ou em uma data anterior.")
    return birthday.isoformat()


def instant(key):
    try:
        return datetime.strptime(field(key), "%Y-%m-%dT%H:%M").isoformat(
            timespec="minutes"
        )
    except ValueError:
        raise FormError("Confira a data e o horário.")


def new_password():
    value = request.form.get("password", "")
    if not 8 <= len(value) <= 128:
        raise FormError("Use uma senha de 8 a 128 caracteres.")
    return generate_password_hash(value)


def require(*roles):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.user:
                return redirect(url_for("login"))
            if g.user["role"] not in roles or g.user["status"] != "ativo":
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorate


def one(sql, args=()):
    row = db().execute(sql, args).fetchone()
    if row is None:
        abort(404)
    return row


def rows(sql, args=()):
    return db().execute(sql, args).fetchall()


def create_app(instance_path=None):
    app = Flask(__name__, instance_path=instance_path)
    folder = Path(app.instance_path)
    folder.mkdir(parents=True, exist_ok=True)
    key = folder / "session.key"
    if not key.exists():
        key.write_bytes(secrets.token_bytes(32))
    app.config.update(
        SECRET_KEY=key.read_bytes(),
        DATABASE=folder / "clubes.sqlite",
        MAX_CONTENT_LENGTH=65536,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    app.teardown_appcontext(close_db)
    init(app)
    app.jinja_env.filters["when"] = lambda s: datetime.fromisoformat(s).strftime(
        "%d/%m/%Y · %H:%M"
    )
    app.jinja_env.filters["money"] = lambda v: f"R$ {v // 100},{v % 100:02d}"
    app.jinja_env.filters["period"] = lambda v: f"{v[5:7]}/{v[:4]}"
    app.jinja_env.globals.update(
        categories=CATEGORIES, states=STATES, club_fields=CLUB_FIELDS
    )

    @app.before_request
    def identify():
        g.user = (
            db()
            .execute("SELECT * FROM users WHERE id=?", (session.get("uid"),))
            .fetchone()
        )
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(24)
        if request.method == "POST" and not hmac.compare_digest(
            request.form.get("csrf", "").encode(), session["csrf"].encode()
        ):
            abort(400)

    @app.route("/")
    def home():
        city = request.args.get("cidade", "")
        clubs = rows(
            "SELECT * FROM clubs WHERE ?='' OR city=? ORDER BY city,name", (city, city)
        )
        return render_template(
            "home.html",
            clubs=clubs,
            city=city,
            cities=rows("SELECT DISTINCT city FROM clubs ORDER BY city"),
        )

    @app.route("/clubes/<int:cid>")
    def club(cid):
        item = one("SELECT * FROM clubs WHERE id=?", (cid,))
        internal = (
            g.user
            and g.user["status"] == "ativo"
            and (g.user["role"] == "super" or g.user["club"] == cid)
        )
        events = rows(
            """SELECT * FROM events WHERE club=? AND (audience='Público' OR ?)
                         AND starts>=? ORDER BY starts""",
            (cid, bool(internal), date.today().isoformat()),
        )
        bookings = rows(
            """SELECT starts,ends FROM bookings WHERE club=? AND status='Aprovada'
                           AND ends>=? ORDER BY starts""",
            (cid, datetime.now().isoformat(timespec="minutes")),
        )
        return render_template("club.html", club=item, events=events, bookings=bookings)

    @app.route("/entrar", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            user = (
                db()
                .execute(
                    "SELECT * FROM users WHERE email=?",
                    (request.form.get("email", "").strip(),),
                )
                .fetchone()
            )
            if user and check_password_hash(
                user["password"], request.form.get("password", "")
            ):
                session.clear()
                session["uid"] = user["id"]
                return redirect(url_for("panel"))
            flash("E-mail ou senha incorretos.", "erro")
        return render_template("login.html")

    @app.post("/sair")
    def logout():
        session.clear()
        return redirect(url_for("home"))

    @app.route("/cadastro", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            try:
                cid = field("club")
                one("SELECT id FROM clubs WHERE id=?", (cid,))
                cpf = re.sub(r"[.\s-]", "", field("cpf"))
                if not re.fullmatch(r"[0-9]{11}", cpf):
                    raise FormError("Informe os 11 dígitos do CPF.")
                data = (
                    cid,
                    field("name"),
                    email(),
                    new_password(),
                    choice("category", CATEGORIES[2:]),
                    cpf,
                    field("address"),
                    field("district"),
                    field("city"),
                    choice("uf", STATES),
                    field("phone"),
                    field("sex"),
                    field("civil"),
                    birth(),
                    request.form.get("interests", "")[:300],
                )
                with db():
                    db().execute(
                        """INSERT INTO users(club,name,email,password,role,status,category,cpf,address,
                        district,city,uf,phone,sex,civil,birth,interests) VALUES(?,?,?,?,'associado','pendente',
                        ?,?,?,?,?,?,?,?,?,?,?)""",
                        data,
                    )
                flash("Cadastro enviado. Entre para acompanhar a aprovação.")
                return redirect(url_for("login"))
            except FormError as e:
                flash(str(e), "erro")
            except sqlite3.IntegrityError:
                flash("Já existe cadastro com esse e-mail ou CPF no clube.", "erro")
        return render_template(
            "signup.html", clubs=rows("SELECT * FROM clubs ORDER BY name")
        )

    @app.get("/painel")
    def panel():
        if not g.user:
            return redirect(url_for("login"))
        if g.user["status"] != "ativo":
            return render_template("pending.html")
        role, cid, uid = (g.user[k] for k in ("role", "club", "id"))
        if role == "super":
            cid = (
                request.args.get("clube", type=int)
                or one("SELECT min(id) AS id FROM clubs")["id"]
            )
        item = one("SELECT * FROM clubs WHERE id=?", (cid,))
        manager = role in ("super", "presidente")
        member = role == "associado"
        ctx = {
            "club": item,
            "manager": manager,
            "member": member,
            "finance": role in ("super", "tesoureiro"),
            "clubs": rows("SELECT * FROM clubs ORDER BY name")
            if role == "super"
            else [],
            "month": date.today().strftime("%Y-%m"),
        }
        if manager:
            ctx["members"] = rows(
                """SELECT * FROM users WHERE club=? AND role='associado'
                                     ORDER BY status='pendente' DESC,name""",
                (cid,),
            )
        if manager or member:
            ctx["tickets"] = rows(
                """SELECT t.*,u.name FROM tickets t JOIN users u ON u.id=t.member
                                     WHERE u.club=? AND (? OR u.id=?) ORDER BY t.id DESC""",
                (cid, manager, uid),
            )
            ctx["bookings"] = rows(
                """SELECT b.*,u.name FROM bookings b JOIN users u ON u.id=b.member
                                      WHERE b.club=? AND (? OR u.id=?) ORDER BY starts DESC""",
                (cid, manager, uid),
            )
        if member:
            ctx["deps"] = rows(
                "SELECT * FROM dependents WHERE member=? ORDER BY name", (uid,)
            )
        if ctx["finance"] or member:
            ctx["dues"] = rows(
                """SELECT d.*,u.name FROM dues d JOIN users u ON u.id=d.member
                                  WHERE u.club=? AND (? OR u.id=?) ORDER BY period DESC,u.name""",
                (cid, ctx["finance"], uid),
            )
        return render_template("panel.html", **ctx)

    @app.post("/painel/<int:cid>/<action>")
    @require("super", "presidente", "tesoureiro", "associado")
    def change(cid, action):
        role, uid = g.user["role"], g.user["id"]
        if role != "super" and g.user["club"] != cid:
            abort(403)
        item = one("SELECT * FROM clubs WHERE id=?", (cid,))
        access = {
            "super": {
                "novo-clube",
                "clube",
                "equipe",
                "socio",
                "evento",
                "decidir",
                "responder",
                "gerar",
                "pagar",
            },
            "presidente": {"clube", "socio", "evento", "decidir", "responder"},
            "tesoureiro": {"gerar", "pagar"},
            "associado": {"dependente", "reserva", "mensagem"},
        }
        if action not in access[role]:
            abort(403)
        try:
            with db():
                db().execute("BEGIN IMMEDIATE")
                message = apply_change(action, item, uid)
            flash(message)
        except FormError as e:
            flash(str(e), "erro")
        except sqlite3.IntegrityError:
            flash("Registro duplicado. Confira a sigla ou o e-mail informado.", "erro")
        section = {
            "socio": "socios",
            "evento": "eventos",
            "reserva": "salao",
            "decidir": "salao",
            "mensagem": "mensagens",
            "responder": "mensagens",
            "gerar": "mensalidades",
            "pagar": "mensalidades",
            "dependente": "dependentes",
        }.get(action, "gestao")
        return redirect(url_for("panel", clube=cid, aba=section))

    return app


def apply_change(action, club, uid):
    con, cid = db(), club["id"]
    if action in ("clube", "novo-clube"):
        try:
            fee = Decimal(field("fee").replace(",", "."))
            if (
                not fee.is_finite()
                or not 0 <= fee <= 999999
                or fee * 100 != int(fee * 100)
            ):
                raise InvalidOperation
        except InvalidOperation:
            raise FormError("Informe um valor válido, com até duas casas decimais.")
        data = (
            field("name"),
            field("initials", 12).upper(),
            field("address"),
            field("district"),
            field("city"),
            choice("uf", STATES),
            field("phone"),
            email(),
            int(fee * 100),
        )
        if action == "clube":
            con.execute(
                "UPDATE clubs SET name=?,initials=?,address=?,district=?,city=?,uf=?,phone=?,email=?,fee=? WHERE id=?",
                (*data, cid),
            )
        else:
            con.execute(
                "INSERT INTO clubs(name,initials,address,district,city,uf,phone,email,fee) VALUES(?,?,?,?,?,?,?,?,?)",
                data,
            )
        return "Clube salvo."
    if action == "equipe":
        con.execute(
            "INSERT INTO users(club,name,email,password,role) VALUES(?,?,?,?,?)",
            (
                cid,
                field("name"),
                email(),
                new_password(),
                choice("role", ("presidente", "tesoureiro")),
            ),
        )
        return "Acesso da equipe criado."
    if action == "socio":
        mid = field("id")
        one(
            "SELECT id FROM users WHERE id=? AND club=? AND role='associado'",
            (mid, cid),
        )
        con.execute(
            "UPDATE users SET status=?,category=? WHERE id=?",
            (
                choice("status", ("ativo", "recusado")),
                choice("category", CATEGORIES),
                mid,
            ),
        )
        return "Situação do sócio atualizada."
    if action == "evento":
        con.execute(
            "INSERT INTO events(club,name,starts,audience,target) VALUES(?,?,?,?,?)",
            (
                cid,
                field("name"),
                instant("starts"),
                choice("audience", ("Público", "Associados")),
                field("target"),
            ),
        )
        return "Evento publicado na página do clube."
    if action == "dependente":
        con.execute(
            "INSERT INTO dependents(member,name,birth,relation) VALUES(?,?,?,?)",
            (uid, field("name"), birth(), field("relation")),
        )
        return "Dependente cadastrado."
    if action == "mensagem":
        con.execute(
            "INSERT INTO tickets(member,kind,body,created) VALUES(?,?,?,?)",
            (
                uid,
                choice("kind", ("Solicitação", "Reclamação")),
                field("body", 2000),
                date.today().isoformat(),
            ),
        )
        return "Mensagem enviada à presidência."
    if action == "responder":
        tid = field("id")
        one(
            "SELECT t.id FROM tickets t JOIN users u ON u.id=t.member WHERE t.id=? AND u.club=?",
            (tid, cid),
        )
        con.execute(
            "UPDATE tickets SET reply=? WHERE id=?", (field("reply", 2000), tid)
        )
        return "Resposta disponível para o sócio."
    if action in ("reserva", "decidir"):
        if action == "reserva":
            start, end = instant("starts"), instant("ends")
            if start < datetime.now().isoformat(timespec="minutes") or end <= start:
                raise FormError(
                    "Escolha um início futuro e um término posterior ao início."
                )
        else:
            bid = field("id")
            booking = one("SELECT * FROM bookings WHERE id=? AND club=?", (bid, cid))
            if booking["status"] != "Pendente":
                raise FormError("Esta reserva já foi analisada.")
            status = choice("status", ("Aprovada", "Recusada"))
            if status == "Recusada":
                con.execute("UPDATE bookings SET status=? WHERE id=?", (status, bid))
                return "Reserva recusada."
            start, end = booking["starts"], booking["ends"]
        if con.execute(
            """SELECT 1 FROM bookings WHERE club=? AND status='Aprovada'
                          AND starts<? AND ends>?""",
            (cid, end, start),
        ).fetchone():
            raise FormError("O salão já está reservado nesse período.")
        if action == "reserva":
            con.execute(
                """INSERT INTO bookings(club,member,purpose,starts,ends,status)
                           VALUES(?,?,?,?,?,'Pendente')""",
                (cid, uid, field("purpose"), start, end),
            )
            return "Pedido de reserva enviado à presidência."
        con.execute("UPDATE bookings SET status=? WHERE id=?", (status, bid))
        return "Reserva aprovada e incluída na agenda."
    if action == "gerar":
        period = field("period")
        if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", period):
            raise FormError("Informe o mês de referência.")
        count = con.execute(
            """INSERT INTO dues(member,period,amount)
                               SELECT id,?,? FROM users WHERE club=? AND role='associado' AND status='ativo'
                               ON CONFLICT(member,period) DO NOTHING""",
            (period, club["fee"], cid),
        ).rowcount
        return f"Mensalidades geradas: {count}."
    if action == "pagar":
        did = field("id")
        one(
            "SELECT d.id FROM dues d JOIN users u ON u.id=d.member WHERE d.id=? AND u.club=?",
            (did, cid),
        )
        con.execute(
            "UPDATE dues SET paid=? WHERE id=? AND paid IS NULL",
            (date.today().isoformat(), did),
        )
        return "Pagamento registrado."


if __name__ == "__main__":
    from waitress import serve

    app = create_app()
    port = int(os.environ.get("PORT", "8000"))
    print(f"Clubes: http://127.0.0.1:{port}", flush=True)
    print(
        (Path(app.instance_path) / "acesso-demo.txt").read_text(encoding="utf-8"),
        flush=True,
    )
    serve(app, host=os.environ.get("CLUBES_HOST", "127.0.0.1"), port=port)
