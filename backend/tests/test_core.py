import json, os, sys, tempfile, unittest, zipfile, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
os.environ["PAGE_DELAY_SECS"] = "0"
from backend.core import auth, db, detect, jobs, schema, inspector, providers
from backend.core.fetcher import FetchResult
from backend.core.phones import normalize_phone
from backend.core.xlsx import build_xlsx

schema.init_db()
SIGS = db.rows("SELECT vendor,kind,scope,pattern,enabled FROM chatbot_signatures")


def fx(pages):
    """fetcher over dict url->(status, html)"""
    def f(url):
        st, html = pages.get(url.rstrip("/"), ("down", ""))
        return FetchResult(st, 200 if st == "ok" else 0, html, url)
    return f


def run(cand, pages, country="AE"):
    return inspector.inspect(cand, country, fx(pages), SIGS)


class Phones(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_phone("050 276 7550", "AE"), ("+971502767550", "mobile"))
        self.assertEqual(normalize_phone("04 555 0170", "AE")[1], "landline")
        self.assertEqual(normalize_phone("+44 7911 123456", "GB")[1], "mobile")
        self.assertEqual(normalize_phone("(415) 555-2671", "US")[1], "mobile_or_fixed")
        self.assertEqual(normalize_phone("123", "AE")[1], "invalid")


class DetectionLab(unittest.TestCase):
    """Fixture pages with fixed expected output (mini version of the spec's test lab)."""
    C = {"name": "X", "phone": "+971 50 111 2222", "website": "https://x.ae"}

    def test_wa_link_manual_no_bot_is_hot(self):
        r = run(self.C, {"https://x.ae": ("ok", '<a href="https://wa.me/971501112222">hi</a><p>' + "x" * 500)})
        self.assertEqual((r["wa_status"], r["wa_type"], r["chatbot_value"], r["hot"]), ("CONFIRMED", "MANUAL", "NO", True))
        self.assertEqual(r["wa_number_e164"], "+971501112222")

    def test_contact_page_link(self):
        r = run(self.C, {"https://x.ae": ("ok", '<a href="/contact-us">c</a>' + "x" * 500),
                         "https://x.ae/contact-us": ("ok", '<a href="https://api.whatsapp.com/send?phone=971503334444">w</a>')})
        self.assertEqual(r["wa_number_e164"], "+971503334444")
        self.assertTrue(r["wa_source_url"].endswith("/contact-us"))

    def test_joinchat_plugin(self):
        r = run(self.C, {"https://x.ae": ("ok", '<div class="joinchat" data-phone="971505556666"></div>' + "x" * 500)})
        self.assertEqual((r["wa_status"], r["wa_number_e164"]), ("CONFIRMED", "+971505556666"))

    def test_text_near_number(self):
        r = run(self.C, {"https://x.ae": ("ok", "<p>WhatsApp: +971 55 777 8888</p>" + "x" * 500)})
        self.assertEqual((r["wa_status"], r["wa_number_e164"]), ("CONFIRMED", "+971557778888"))

    def test_arabic_text(self):
        r = run(self.C, {"https://x.ae": ("ok", "<p>واتساب 0551239999</p>" + "x" * 500)})
        self.assertEqual(r["wa_status"], "CONFIRMED")

    def test_chatbot_vendor_blocks_hot(self):
        r = run(self.C, {"https://x.ae": ("ok", '<a href="https://wa.me/971501112222">w</a><script src="//code.tidio.co/k.js"></script>')})
        self.assertEqual((r["chatbot_value"], r["chatbot_vendor"], r["hot"]), ("YES", "Tidio", False))

    def test_generic_widget_heuristic(self):
        r = run(self.C, {"https://x.ae": ("ok", '<div id="my-chatbot-frame"></div><a href="https://wa.me/971501112222">w</a>')})
        self.assertEqual((r["chatbot_value"], r["chatbot_kind"]), ("YES", "UNKNOWN_WIDGET"))

    def test_automated_whatsapp(self):
        r = run(self.C, {"https://x.ae": ("ok", '<a href="https://wa.me/971501112222?text=START_BOT">w</a><script src="https://cdn.wati.io/a.js">')})
        self.assertEqual((r["wa_type"], r["hot"]), ("AUTOMATED", False))

    def test_probable_only_mobile(self):
        r = run(self.C, {"https://x.ae": ("ok", "<p>office hours</p><a href='/a'>a</a>" + "x" * 500)})
        self.assertEqual((r["wa_status"], r["wa_type"], r["hot"]), ("PROBABLE", "UNKNOWN", False))

    def test_landline_no_whatsapp(self):
        r = run({**self.C, "phone": "04 555 0170"}, {"https://x.ae": ("ok", "<p>hi</p><a href='/a'>a</a>" + "x" * 500)})
        self.assertIsNone(r["wa_number_e164"])

    def test_blocked_is_unknown_never_no(self):
        r = run(self.C, {"https://x.ae": ("blocked", "")})
        self.assertEqual((r["status"], r["chatbot_value"], r["hot"]), ("BLOCKED", "UNKNOWN", False))
        r = run(self.C, {"https://x.ae": ("timeout", "")})
        self.assertEqual((r["status"], r["chatbot_value"]), ("TIMEOUT", "UNKNOWN"))

    def test_cloudflare_challenge_page(self):
        r = run(self.C, {"https://x.ae": ("ok", "<html><title>Just a moment...</title>cf-challenge</html>")})
        self.assertEqual((r["status"], r["chatbot_value"]), ("BLOCKED", "UNKNOWN"))

    def test_social_only_and_parked_and_dead(self):
        self.assertFalse(run({**self.C, "website": "https://instagram.com/x"}, {})["has_website"])
        self.assertFalse(run(self.C, {"https://x.ae": ("ok", "<html>This domain is for sale</html>")})["has_website"])
        r = run(self.C, {})
        self.assertEqual((r["has_website"], r["status"]), (0, "NO_WEBSITE"))

    def test_wa_me_as_website_field(self):
        r = run({**self.C, "website": "https://wa.me/971509998888"}, {})
        self.assertEqual((r["wa_status"], r["wa_number_e164"], r["has_website"]), ("CONFIRMED", "+971509998888", 0))

    def test_hot_rule_table(self):
        self.assertTrue(detect.is_hot("CONFIRMED", "MANUAL", "NO"))
        for args in [("PROBABLE", "UNKNOWN", "NO"), ("CONFIRMED", "AUTOMATED", "NO"), ("CONFIRMED", "MANUAL", "YES"), ("CONFIRMED", "MANUAL", "UNKNOWN")]:
            self.assertFalse(detect.is_hot(*args))

    def test_canonical_domain(self):
        self.assertEqual(detect.canonical_domain("https://www.Foo.com/x"), "foo.com")
        self.assertIsNone(detect.canonical_domain("https://facebook.com/foo"))

    def test_ssrf_blocked(self):
        from backend.core.fetcher import fetch_page
        self.assertEqual(fetch_page("http://127.0.0.1:1/").status, "blocked")
        self.assertEqual(fetch_page("http://169.254.169.254/").status, "blocked")


class Matrix(unittest.TestCase):
    def setUp(self):
        self.u = auth.register(f"u{os.urandom(3).hex()}@example.com", "correct-horse-battery")

    def body(self, **k):
        c = db.one("SELECT id FROM cities WHERE country='AE' AND name='Dubai'")["id"]
        return {"country": "AE", "niche": "REAL_ESTATE", "city_ids": [c], "lead_count": 10, "mode": "demo", **k}

    def test_all_28_combos(self):
        from backend.core.seed_data import COUNTRIES, NICHES, MATRIX
        allowed = 0
        for cc in COUNTRIES:
            cid = db.one("SELECT id FROM cities WHERE country=?", (cc,))["id"]
            for n in NICHES:
                try:
                    jobs.validate_and_create(self.u, {"country": cc, "niche": n, "city_ids": [cid], "lead_count": 10, "mode": "demo"})
                    ok = True
                except jobs.AppError as e:
                    self.assertEqual(e.code, "NICHE_NOT_ALLOWED_FOR_COUNTRY"); ok = False
                self.assertEqual(ok, n in MATRIX[cc], (cc, n)); allowed += ok
        self.assertEqual(allowed, sum(len(v) for v in MATRIX.values()))

    def test_city_outside_country(self):
        uk = db.one("SELECT id FROM cities WHERE country='GB'")["id"]
        with self.assertRaises(jobs.AppError) as cm: jobs.validate_and_create(self.u, self.body(city_ids=[uk]))
        self.assertEqual(cm.exception.code, "CITY_NOT_IN_COUNTRY")

    def test_bad_counts_and_cities(self):
        for bad in (0, 201, "5", None, True):
            with self.assertRaises(jobs.AppError): jobs.validate_and_create(self.u, self.body(lead_count=bad))
        with self.assertRaises(jobs.AppError): jobs.validate_and_create(self.u, self.body(city_ids=[]))

    def test_idempotency_and_quota(self):
        a, new = jobs.validate_and_create(self.u, self.body(), "k1")
        b, new2 = jobs.validate_and_create(self.u, self.body(), "k1")
        self.assertEqual(a, b); self.assertFalse(new2)
        db.execute("UPDATE app_limits SET value='15' WHERE key='daily_cap'")
        try:
            with self.assertRaises(jobs.AppError) as cm: jobs.validate_and_create(self.u, self.body(lead_count=10))
            self.assertEqual(cm.exception.status, 429)
        finally:
            db.execute("UPDATE app_limits SET value='500' WHERE key='daily_cap'")

    def test_live_requires_key(self):
        from backend.core.config import settings
        old, settings.APIFY_API_TOKEN = settings.APIFY_API_TOKEN, ""
        try:
            with self.assertRaises(jobs.AppError) as cm: jobs.validate_and_create(self.u, self.body(mode="live"))
        finally:
            settings.APIFY_API_TOKEN = old
        self.assertEqual(cm.exception.code, "LIVE_NOT_CONFIGURED")


class Runner(unittest.TestCase):
    def setUp(self):
        self.u = auth.register(f"r{os.urandom(3).hex()}@example.com", "correct-horse-battery")

    def make(self, n, cities=("Dubai",), niche="REAL_ESTATE", cc="AE", filters=None):
        ids = [db.one("SELECT id FROM cities WHERE country=? AND name=?", (cc, c))["id"] for c in cities]
        jid, _ = jobs.validate_and_create(self.u, {"country": cc, "niche": niche, "city_ids": ids, "lead_count": n, "mode": "demo", "filters": filters or {}})
        jobs.run_job(jid)
        return db.one("SELECT * FROM search_jobs WHERE id=?", (jid,))

    def test_exact_n_completed_no_dupes(self):
        j = self.make(10)
        self.assertEqual((j["status"], j["accepted_count"]), ("COMPLETED", 10))
        ls = jobs.list_leads(self.u, j["id"])
        self.assertEqual(len(ls), 10)
        self.assertEqual(len({l["whatsapp"]["number"] for l in ls}), 10)
        self.assertTrue(all(l["whatsapp"]["number"] and l["whatsapp"]["status"] == "CONFIRMED" for l in ls))
        self.assertTrue(all(l["is_demo"] for l in ls))

    def test_filters_applied(self):
        j = self.make(5, filters={"no_chatbot_only": True, "manual_whatsapp_only": True, "website_required": True})
        for l in jobs.list_leads(self.u, j["id"]):
            self.assertEqual((l["chatbot"]["value"], l["whatsapp"]["type"], l["website"]["has_website"]), ("NO", "MANUAL", True))
        for l in jobs.list_leads(self.u, j["id"], hot=True):
            self.assertTrue(l["hot_lead"])

    def test_partial_with_shortfall(self):
        j = self.make(200, cities=("Dubai",))        # demo queries are finite -> cannot reach 200
        self.assertEqual(j["status"], "PARTIAL")
        self.assertLess(j["accepted_count"], 200)
        sf = json.loads(j["shortfall"])
        self.assertIn("breakdown", sf); self.assertIn(" of 200 found", j["message"])
        self.assertLessEqual(j["accepted_count"], j["lead_count"])

    def test_probable_allowed_when_toggle_off(self):
        j = self.make(40, filters={"whatsapp_confirmed_only": False})
        self.assertTrue(any(l["whatsapp"]["status"] == "PROBABLE" for l in jobs.list_leads(self.u, j["id"])))

    def test_cache_and_exclude_exported(self):
        j1 = self.make(5)
        ids = [l["id"] for l in jobs.list_leads(self.u, j1["id"])]
        n_insp = db.scalar("SELECT COUNT(*) FROM inspections")
        j2 = self.make(5, filters={"exclude_previously_exported": False})
        failed = db.scalar("SELECT COUNT(*) FROM inspections WHERE status IN ('BLOCKED','TIMEOUT')")
        self.assertLessEqual(db.scalar("SELECT COUNT(*) FROM inspections") - n_insp, failed)  # only uncacheable failures re-inspected
        jobs.mark_exported(ids)
        j3 = self.make(5)
        b1 = {l["whatsapp"]["number"] for l in jobs.list_leads(self.u, j1["id"])}
        b3 = {l["whatsapp"]["number"] for l in jobs.list_leads(self.u, j3["id"])}
        self.assertFalse(b1 & b3)

    def test_cancel_and_resume(self):
        ids = [db.one("SELECT id FROM cities WHERE country='AE' AND name='Dubai'")["id"]]
        jid, _ = jobs.validate_and_create(self.u, {"country": "AE", "niche": "CLINICS", "city_ids": ids, "lead_count": 12, "mode": "demo"})
        self.assertEqual(jobs.cancel(jid), 1)
        jobs.run_job(jid)
        self.assertEqual(db.one("SELECT status,accepted_count FROM search_jobs WHERE id=?", (jid,))["status"], "CANCELLED")
        db.execute("UPDATE search_jobs SET status='QUEUED' WHERE id=?", (jid,))        # what resume() does before submit
        jobs.run_job(jid)
        j = db.one("SELECT * FROM search_jobs WHERE id=?", (jid,))
        self.assertEqual((j["status"], j["accepted_count"]), ("COMPLETED", 12))

    def test_crash_resume_no_double_leads(self):
        ids = [db.one("SELECT id FROM cities WHERE country='AE' AND name='Dubai'")["id"]]
        jid, _ = jobs.validate_and_create(self.u, {"country": "AE", "niche": "REAL_ESTATE", "city_ids": ids, "lead_count": 15, "mode": "demo"})
        jobs.run_job(jid)
        db.execute("UPDATE search_jobs SET status='RUNNING', finished_at=NULL WHERE id=?", (jid,))   # simulate crash after completion write
        jobs.run_job(jid)
        self.assertEqual(db.scalar("SELECT COUNT(*) FROM job_leads WHERE job_id=?", (jid,)), 15)

    def test_user_isolation(self):
        j = self.make(5)
        other = auth.register(f"o{os.urandom(3).hex()}@example.com", "correct-horse-battery")
        self.assertEqual(jobs.list_leads(other, j["id"]), [])

    def test_provider_failure_marks_failed(self):
        class Bad:
            is_demo = False
            def search(self, *a, **k): raise providers.DiscoveryError("boom", 502)
        old = jobs.provider_factory
        jobs.provider_factory = lambda m: Bad()
        try:
            j = self.make(5)
        finally:
            jobs.provider_factory = old
        self.assertEqual(j["status"], "FAILED"); self.assertIn("boom", j["message"])

    def test_exports(self):
        j = self.make(5)
        ls = jobs.list_leads(self.u, j["id"])
        ls[0]["business_name"] = "=HYPERLINK(\"x\")"
        csv_text = jobs.to_csv(ls)
        self.assertIn("'=HYPERLINK", csv_text); self.assertTrue(csv_text.splitlines()[0].lstrip("\ufeff").startswith("Business name"))
        z = zipfile.ZipFile(io.BytesIO(build_xlsx(jobs.EXPORT_COLS, jobs.export_rows(ls))))
        self.assertIn(b"'=HYPERLINK", z.read("xl/worksheets/sheet1.xml"))

    def test_estimate(self):
        e = jobs.estimate("AE", "REAL_ESTATE", 50)
        self.assertTrue(e["minutes_p50"] >= 1 and e["minutes_p90"] > e["minutes_p50"])


class Auth(unittest.TestCase):
    def test_flow(self):
        e = f"a{os.urandom(3).hex()}@example.com"
        u = auth.register(e, "long-enough-pass")
        with self.assertRaises(auth.AuthError): auth.register(e, "long-enough-pass")
        with self.assertRaises(auth.AuthError): auth.register("bad", "long-enough-pass")
        with self.assertRaises(auth.AuthError): auth.register("z@example.com", "short")
        with self.assertRaises(auth.AuthError) as cm: auth.login(e, "wrong-password!!")
        self.assertEqual(cm.exception.status, 401)
        tok, pub = auth.login(e, "long-enough-pass")
        self.assertEqual(auth.user_from_token(tok)["email"], e)
        auth.logout(tok); self.assertIsNone(auth.user_from_token(tok)); self.assertIsNone(auth.user_from_token("junk"))
        self.assertNotIn(tok, str(db.rows("SELECT * FROM sessions")))   # only hashes stored
        self.assertTrue(auth.hash_password("x").startswith("pbkdf2$"))

    def test_first_user_admin(self):
        auth.register(f"f{os.urandom(3).hex()}@example.com", "long-enough-pass")
        self.assertEqual(db.one("SELECT role FROM users ORDER BY created_at LIMIT 1")["role"], "admin")


if __name__ == "__main__":
    unittest.main(verbosity=2)
