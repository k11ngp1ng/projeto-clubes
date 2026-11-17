import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from app import create_app
from database import db


class FluxosDoClube(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.password = "senha-de-teste"
        with patch.dict("os.environ", {"CLUBES_DEMO_PASSWORD": self.password}):
            self.app = create_app(str(Path(temp.name).resolve()))
        self.app.testing = True
        self.client = self.app.test_client()

    def post(self, path, **data):
        self.client.get("/")
        with self.client.session_transaction() as session:
            data["csrf"] = session["csrf"]
        return self.client.post(path, data=data, follow_redirects=True)

    def login(self, email):
        response = self.post("/entrar", email=email, password=self.password)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("incorretos", response.get_data(as_text=True))

    def scalar(self, query):
        with self.app.app_context():
            return db().execute(query).fetchone()[0]

    def test_aprovacao_mensalidade_e_isolamento(self):
        response = self.post(
            "/cadastro",
            club="1",
            name="Teste",
            email="teste@example.test",
            password=self.password,
            category="Convidado",
            cpf="00000000001",
            address="Rua Exemplo",
            district="Centro",
            city="Foz do Iguaçu",
            uf="PR",
            phone="4500000000",
            sex="Outro",
            civil="Outro",
            birth="2000-01-01",
        )
        self.assertIn("Cadastro enviado", response.get_data(as_text=True))
        self.login("teste@example.test")
        self.assertIn(
            "Aguardando aprovação", self.client.get("/painel").get_data(as_text=True)
        )
        self.assertEqual(self.post("/painel/1/reserva").status_code, 403)
        mid = self.scalar("SELECT id FROM users WHERE email='teste@example.test'")
        self.login("presidente@csq.test")
        self.assertEqual(self.post("/painel/1/socio", id=mid).status_code, 403)
        self.assertEqual(self.post("/painel/3/socio", id=mid).status_code, 404)
        self.login("presidente@cdc.test")
        self.post("/painel/1/socio", id=mid, category="Convidado", status="ativo")
        self.login("teste@example.test")
        self.assertIn(
            "Sem direito a voto", self.client.get("/painel").get_data(as_text=True)
        )
        self.post(
            "/painel/1/dependente",
            name="Dep Teste",
            birth="2015-01-01",
            relation="Filho",
        )
        self.assertEqual(self.scalar("SELECT count(*) FROM dependents"), 1)
        self.post("/painel/1/mensagem", kind="Reclamação", body="Chuveiro quebrado")
        self.login("presidente@cdc.test")
        self.post("/painel/1/responder", id="1", reply="Reparo agendado")
        self.login("tesoureiro@cdc.test")
        for _ in range(2):
            self.post("/painel/1/gerar", period="2040-01")
        self.assertEqual(
            self.scalar("SELECT count(*) FROM dues WHERE period='2040-01'"), 2
        )
        did = self.scalar(
            f"SELECT id FROM dues WHERE member={mid} AND period='2040-01'"
        )
        self.post("/painel/1/pagar", id=did)
        self.login("teste@example.test")
        self.assertIn("Paga em", self.client.get("/painel").get_data(as_text=True))
        self.assertIn(
            "Reparo agendado",
            self.client.get("/painel?aba=mensagens").get_data(as_text=True),
        )

    def test_conflito_entre_dias_e_visibilidade_dos_eventos(self):
        first = (date.today() + timedelta(days=7)).isoformat()
        last = (date.today() + timedelta(days=8)).isoformat()
        self.login("socio@cdc.test")
        for start, end in [
            (first + "T12:00", last + "T09:00"),
            (last + "T08:00", last + "T11:00"),
        ]:
            self.post(
                "/painel/1/reserva", purpose="Confraternização", starts=start, ends=end
            )
        self.login("presidente@cdc.test")
        self.post("/painel/1/decidir", id=1, status="Aprovada")
        response = self.post("/painel/1/decidir", id=2, status="Aprovada")
        self.assertIn("já está reservado", response.get_data(as_text=True))
        self.assertEqual(
            self.scalar("SELECT count(*) FROM bookings WHERE status='Aprovada'"), 1
        )
        self.post(
            "/painel/1/evento",
            name="Encontro interno",
            starts=first + "T10:00",
            audience="Associados",
            target="Sócios",
        )
        self.login("socio@cdc.test")
        self.assertIn(
            "Encontro interno", self.client.get("/clubes/1").get_data(as_text=True)
        )
        self.post("/sair")
        public = self.client.get("/clubes/1").get_data(as_text=True)
        self.assertNotIn("Encontro interno", public)
        self.assertIn("Salão reservado", public)
        self.assertNotIn("Confraternização", public)

    def test_app_integrado_com_presidencia_e_tesouraria(self):
        mobile = self.app.test_client()
        start = mobile.get("/api/inicio").json
        self.assertEqual(len(start["clubs"]), 4)
        headers = {"X-CSRF-Token": start["csrf"]}
        account = dict(email="mobile@example.test", password=self.password)
        form = dict(**account, club="1", category="Convidado", name="Sócio Mobile",
                    cpf="00000000002", birth="2000-01-01", city="Foz do Iguaçu",
                    address="Rua A", district="Centro", uf="PR", phone="4500000000",
                    sex="Outro", civil="Outro", interests="Pesca")
        self.assertEqual(mobile.post("/api/cadastro", json=form).status_code, 400)
        self.assertEqual(mobile.get("/api/painel").status_code, 401)
        self.assertEqual(mobile.post("/api/cadastro", json=form, headers=headers).status_code, 201)
        self.assertEqual(mobile.post("/api/cadastro", json=form, headers=headers).status_code, 409)
        login = mobile.post("/api/entrar", json=account, headers=headers)
        headers["X-CSRF-Token"] = login.json["csrf"]
        self.assertEqual(mobile.get("/api/painel").json["status"], "pendente")
        self.assertEqual(mobile.post("/api/reservas", json={}, headers=headers).status_code, 403)
        mid = self.scalar("SELECT id FROM users WHERE email='mobile@example.test'")
        self.login("presidente@cdc.test")
        self.post("/painel/1/socio", id=mid, category="Convidado", status="ativo")
        panel = mobile.get("/api/painel").json
        self.assertEqual(panel["status"], "ativo")
        self.assertFalse(panel["vote"])
        self.assertEqual(panel["dues"], [])  # A cobrança do fundador é privada.
        first = (date.today() + timedelta(days=3)).isoformat()
        last = (date.today() + timedelta(days=4)).isoformat()
        booking = dict(purpose="Feijoada", starts=first + "T18:00", ends=last + "T10:00")
        self.assertEqual(mobile.post("/api/reservas", json=booking, headers=headers).status_code, 201)
        self.post("/painel/1/decidir", id=1, status="Aprovada")
        conflict = mobile.post("/api/reservas", json=booking, headers=headers)
        self.assertEqual(conflict.status_code, 400)
        self.assertIn("já está reservado", conflict.json["message"])
        ticket = dict(kind="Reclamação", body="Lâmpada queimada", member="1", club="3")
        self.assertEqual(mobile.post("/api/mensagens", json=ticket, headers=headers).status_code, 201)
        self.post("/painel/1/responder", id=1, reply="Troca agendada")
        self.login("tesoureiro@cdc.test")
        self.post("/painel/1/gerar", period="2040-01")
        did = self.scalar(f"SELECT id FROM dues WHERE member={mid}")
        self.post("/painel/1/pagar", id=did)
        panel = mobile.get("/api/painel").json
        self.assertEqual(panel["tickets"][0]["reply"], "Troca agendada")
        self.assertEqual(panel["bookings"][0]["status"], "Aprovada")
        self.assertEqual(panel["dues"], [dict(amount=5000, paid=date.today().isoformat(), period="2040-01")])
        self.login("presidente@cdc.test")
        self.post("/painel/1/socio", id=mid, category="Convidado", status="recusado")
        self.assertEqual(mobile.get("/api/painel").json["tickets"], [])
        self.assertEqual(mobile.post("/api/mensagens", json=ticket, headers=headers).status_code, 403)

    def test_gestao_geral(self):
        self.login("admin@clubes.test")
        self.assertEqual(self.client.get("/painel?aba=gestao").status_code, 200)
        data = {
            "name": "Clube Teste",
            "initials": "CTT",
            "address": "Rua Dois",
            "district": "Centro",
            "city": "Guaíra",
            "uf": "PR",
            "phone": "4500000000",
            "email": "contato@ctt.test",
            "fee": "75,50",
        }
        self.post("/painel/1/novo-clube", **data)
        cid = self.scalar("SELECT id FROM clubs WHERE initials='CTT'")
        self.post(
            f"/painel/{cid}/equipe",
            name="Presidente",
            role="presidente",
            email="presidente@ctt.test",
            password=self.password,
        )
        self.login("presidente@ctt.test")
        self.post(f"/painel/{cid}/clube", **dict(data, fee="80,00"))
        self.assertEqual(
            self.scalar("SELECT fee FROM clubs WHERE initials='CTT'"), 8000
        )
        self.assertEqual(self.post("/painel/1/clube", **data).status_code, 403)
