import os
import secrets
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


def db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def close_db(_error):
    if "db" in g:
        g.pop("db").close()


def init(app):
    folder = Path(app.instance_path)
    folder.mkdir(exist_ok=True, parents=True)
    with app.app_context():
        con = db()
        con.executescript(
            Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        )
        with con:
            con.execute("BEGIN IMMEDIATE")
            if con.execute("SELECT 1 FROM clubs LIMIT 1").fetchone():
                return
            password = os.environ.get("CLUBES_DEMO_PASSWORD") or secrets.token_urlsafe(
                10
            )
            hashed = generate_password_hash(password)
            con.execute(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,'super')",
                ("Administrador geral", "admin@clubes.test", hashed),
            )
            clubs = [
                ("Clube das Cataratas", "CDC", "Foz do Iguaçu", "Vila Yolanda"),
                ("Associação do Iguaçu", "ADI", "Foz do Iguaçu", "Centro"),
                ("Clube Sete Quedas", "CSQ", "Guaíra", "Vila Velha"),
                ("Clube do Paraná", "CDP", "Guaíra", "Centro"),
            ]
            for i, (name, initials, city, district) in enumerate(clubs, 1):
                slug = initials.lower()
                con.execute(
                    "INSERT INTO clubs VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        i,
                        name,
                        initials,
                        f"Rua do Clube, {i}00",
                        district,
                        city,
                        "PR",
                        f"(45) 3000-000{i}",
                        f"contato@{slug}.test",
                        5000,
                    ),
                )
                for role, label in [
                    ("presidente", "Presidência"),
                    ("tesoureiro", "Tesouraria"),
                ]:
                    con.execute(
                        "INSERT INTO users(club,name,email,password,role) VALUES(?,?,?,?,?)",
                        (i, label, f"{role}@{slug}.test", hashed, role),
                    )
            member = con.execute(
                """INSERT INTO users(club,name,email,password,role,category)
                                    VALUES(1,'Alex Demo','socio@cdc.test',?,'associado','Fundador')""",
                (hashed,),
            ).lastrowid
            today = date.today()
            con.execute(
                "INSERT INTO dues(member,period,amount) VALUES(?,?,5000)",
                (member, today.strftime("%Y-%m")),
            )
            for i, name, audience, target in [
                (1, "Café da tarde", "Público", "Famílias da comunidade"),
                (2, "Jantar do clube", "Associados", "Sócios do clube"),
                (3, "Feijoada beneficente", "Público", "Comunidade local"),
            ]:
                start = datetime.combine(
                    today + timedelta(days=i * 7), time(16)
                ).isoformat(timespec="minutes")
                con.execute(
                    "INSERT INTO events(club,name,starts,audience,target) VALUES(?,?,?,?,?)",
                    (i, name, start, audience, target),
                )
            folder.joinpath("acesso-demo.txt").write_text(
                f"Senha inicial das contas fictícias: {password}\n", encoding="utf-8"
            )
