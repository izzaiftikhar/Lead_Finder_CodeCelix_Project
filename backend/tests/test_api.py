import os, sys, tempfile, time, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "api.db")
os.environ["BACKEND_API_KEY"] = ""
os.environ["PAGE_DELAY_SECS"] = "0"
try:
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.core.config import settings
    from backend.core import db, schema
except (ImportError, RuntimeError):
    TestClient = None


@unittest.skipIf(TestClient is None, "fastapi/httpx not installed")
class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.APIFY_API_TOKEN = ""
        schema.init_db()
        # test_core shares this DB when both run in one process: drop its leftover queued jobs so startup recovery
        # does not queue them ahead of ours, and make sure the account below really is the admin.
        db.execute("UPDATE search_jobs SET status='CANCELLED' WHERE status IN ('QUEUED','RUNNING')")
        cls.cm = TestClient(app); cls.c = cls.cm.__enter__()
        r = cls.c.post("/api/auth/register", json={"email": "admin@example.com", "password": "correct-horse-battery"})
        cls.H = {"Authorization": "Bearer " + r.json()["token"]}
        db.execute("UPDATE users SET role='admin' WHERE email='admin@example.com'")
        r = cls.c.post("/api/auth/register", json={"email": "user2@example.com", "password": "correct-horse-battery"})
        cls.H2 = {"Authorization": "Bearer " + r.json()["token"]}

    @classmethod
    def tearDownClass(cls): cls.cm.__exit__(None, None, None)

    def city(self, cc="AE"):
        return self.c.get(f"/api/markets/{cc}/cities", headers=self.H).json()["items"][0]["id"]

    def test_health_and_auth_required(self):
        self.assertEqual(self.c.get("/api/health").json()["status"], "ok")
        self.assertEqual(self.c.get("/api/markets").status_code, 401)
        self.assertEqual(self.c.post("/api/auth/login", json={"email": "admin@example.com", "password": "nope-nope-nope"}).status_code, 401)
        self.assertEqual(self.c.get("/api/auth/me", headers=self.H).json()["user"]["role"], "admin")

    def test_markets_matrix_and_cities(self):
        m = {c["code"]: [n["code"] for n in c["niches"]] for c in self.c.get("/api/markets", headers=self.H).json()["countries"]}
        self.assertEqual(m["AE"], ["CLINICS", "REAL_ESTATE"])
        self.assertIn("SAAS", m["GB"]); self.assertNotIn("REAL_ESTATE", m["GB"])
        self.assertTrue(len(self.c.get("/api/markets/US/cities?q=chi", headers=self.H).json()["items"]) >= 1)

    def test_validation_400(self):
        body = {"country": "GB", "niche": "REAL_ESTATE", "city_ids": [self.city("GB")], "lead_count": 10, "mode": "demo"}
        r = self.c.post("/api/jobs", json=body, headers=self.H); self.assertEqual((r.status_code, r.json()["code"]), (400, "NICHE_NOT_ALLOWED_FOR_COUNTRY"))
        body = {"country": "AE", "niche": "CLINICS", "city_ids": [self.city("GB")], "lead_count": 10, "mode": "demo"}
        self.assertEqual(self.c.post("/api/jobs", json=body, headers=self.H).json()["code"], "CITY_NOT_IN_COUNTRY")
        body["city_ids"] = [self.city("AE")]; body["lead_count"] = 500
        self.assertEqual(self.c.post("/api/jobs", json=body, headers=self.H).json()["code"], "BAD_LEAD_COUNT")

    def test_live_without_key(self):
        body = {"country": "AE", "niche": "CLINICS", "city_ids": [self.city("AE")], "lead_count": 10, "mode": "live"}
        self.assertEqual(self.c.post("/api/jobs", json=body, headers=self.H).status_code, 503)

    def test_full_job_flow_isolation_export(self):
        body = {"country": "AE", "niche": "REAL_ESTATE", "city_ids": [self.city("AE")], "lead_count": 8, "mode": "demo"}
        r = self.c.post("/api/jobs", json=body, headers={**self.H, "Idempotency-Key": "abc"}); self.assertEqual(r.status_code, 202)
        jid = r.json()["id"]
        self.assertEqual(self.c.post("/api/jobs", json=body, headers={**self.H, "Idempotency-Key": "abc"}).json()["id"], jid)
        for _ in range(100):
            j = self.c.get(f"/api/jobs/{jid}", headers=self.H).json()
            if j["status"] not in ("QUEUED", "RUNNING"): break
            time.sleep(0.2)
        self.assertEqual((j["status"], j["accepted_count"]), ("COMPLETED", 8))
        leads = self.c.get(f"/api/jobs/{jid}/leads", headers=self.H).json()["items"]
        self.assertEqual(len(leads), 8); self.assertTrue(all(l["whatsapp"]["number"] for l in leads))
        self.assertEqual(self.c.get(f"/api/jobs/{jid}", headers=self.H2).status_code, 404)           # isolation
        self.assertEqual(self.c.get(f"/api/jobs/{jid}/leads", headers=self.H2).status_code, 404)
        lid = leads[0]["id"]
        self.assertEqual(self.c.post(f"/api/leads/{lid}/feedback", json={"value": "CORRECT"}, headers=self.H).json()["feedback"], "CORRECT")
        self.assertEqual(self.c.post(f"/api/leads/{lid}/feedback", json={"value": "BAD"}, headers=self.H).status_code, 400)
        self.assertEqual(self.c.post(f"/api/leads/{lid}/save", headers=self.H2).status_code, 404)
        self.assertTrue(self.c.post(f"/api/leads/{lid}/save", headers=self.H).json()["saved"])
        self.assertEqual(len(self.c.get("/api/saved", headers=self.H).json()["items"]), 1)
        csv = self.c.get(f"/api/jobs/{jid}/export?format=csv", headers=self.H); self.assertIn("Business name", csv.text)
        x = self.c.get(f"/api/jobs/{jid}/export?format=xlsx", headers=self.H); self.assertEqual(x.content[:2], b"PK")
        self.assertGreaterEqual(self.c.get("/api/stats", headers=self.H).json()["total_leads"], 8)
        self.assertEqual(self.c.get("/api/stats", headers=self.H2).json()["total_leads"], 0)
        self.assertEqual(self.c.post(f"/api/jobs/{jid}/rerun", headers=self.H).status_code, 202)

    def test_admin_rbac(self):
        self.assertEqual(self.c.get("/api/admin/config", headers=self.H2).status_code, 403)
        self.assertIn("signatures", self.c.get("/api/admin/config", headers=self.H).json())
        self.assertEqual(self.c.put("/api/admin/country-niches", json={"country": "AE", "niche": "SAAS", "enabled": False}, headers=self.H).status_code, 200)
        self.assertEqual(self.c.put("/api/admin/limits", json={"key": "max_lead_count", "value": 999}, headers=self.H).status_code, 400)


if __name__ == "__main__":
    unittest.main()
