import os
from dotenv import load_dotenv
load_dotenv()


def _i(k, d):
    try:
        return int(os.getenv(k, d))
    except ValueError:
        return d


def _f(k, d):
    try:
        return float(os.getenv(k, d))
    except ValueError:
        return d


class Settings:
    APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN") or ""
    APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID") or "compass/crawler-google-places"
    DATABASE_URL = os.getenv("DATABASE_URL") or ""
    DATABASE_PATH = os.getenv("DATABASE_PATH") or "lead_finder.db"
    BACKEND_API_KEY = os.getenv("BACKEND_API_KEY") or ""
    ALLOWED_ORIGINS = [o.strip() for o in (os.getenv("ALLOWED_ORIGINS") or "").split(",") if o.strip()]
    ADMIN_EMAILS = [e.strip().lower() for e in (os.getenv("ADMIN_EMAILS") or "").split(",") if e.strip()]
    ALLOW_REGISTRATION = (os.getenv("ALLOW_REGISTRATION", "true").lower() == "true")
    RATE_LIMIT_PER_MIN = _i("RATE_LIMIT_PER_MIN", 240)
    JOB_WORKERS = _i("JOB_WORKERS", 2)
    INSPECT_WORKERS = _i("INSPECT_WORKERS", 8)          # spec: 5-20
    PAGE_DELAY_SECS = _f("PAGE_DELAY_SECS", 2.0)        # spec: 1 request / 2 s per domain
    PAGE_TIMEOUT_SECS = _i("PAGE_TIMEOUT_SECS", 15)
    SITE_HARD_TIMEOUT_SECS = _i("SITE_HARD_TIMEOUT_SECS", 45)
    PER_QUERY_LIMIT = _i("PER_QUERY_LIMIT", 20)
    APIFY_TIMEOUT_SECS = _i("APIFY_TIMEOUT_SECS", 180)
    COST_PER_CANDIDATE = _f("COST_PER_CANDIDATE", 0.002)   # estimate only; verify Apify pricing
    ENVIRONMENT = (os.getenv("ENVIRONMENT") or "development").lower()
    ABUSE_CONTACT = os.getenv("ABUSE_CONTACT") or ""   # email/URL shown in the crawler User-Agent
    ROBOTS_ENABLED = (os.getenv("ROBOTS_ENABLED", "true").lower() == "true")

    @property
    def live_enabled(self):
        return bool(self.APIFY_API_TOKEN)


settings = Settings()

DEFAULT_LIMITS = {"max_lead_count": "200", "daily_cap": "500", "candidate_factor": "15",
                  "job_cost_cap_usd": "5.0", "cache_days": "30", "min_lead_count": "1"}
