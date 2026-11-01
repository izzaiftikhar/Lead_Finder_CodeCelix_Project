import json
from . import db
from .config import DEFAULT_LIMITS
from .seed_data import MATRIX, KEYWORDS, CITIES, SIGNATURES

DDL = [
 "CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user', created_at TEXT NOT NULL)",
 "CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at TEXT NOT NULL)",
 "CREATE TABLE IF NOT EXISTS country_niches(country TEXT NOT NULL, niche TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(country, niche))",
 "CREATE TABLE IF NOT EXISTS cities(id {pk}, country TEXT NOT NULL, admin1 TEXT, name TEXT NOT NULL, lat REAL, lng REAL, population INTEGER, UNIQUE(country, name, admin1))",
 "CREATE TABLE IF NOT EXISTS niche_keywords(id {pk}, niche TEXT NOT NULL, region TEXT NOT NULL, lang TEXT NOT NULL, keyword TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, UNIQUE(niche, region, keyword))",
 "CREATE TABLE IF NOT EXISTS chatbot_signatures(id {pk}, vendor TEXT NOT NULL, kind TEXT NOT NULL, scope TEXT NOT NULL, pattern TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, UNIQUE(vendor, scope, pattern))",
 "CREATE TABLE IF NOT EXISTS app_limits(key TEXT PRIMARY KEY, value TEXT NOT NULL)",
 "CREATE TABLE IF NOT EXISTS suppression(hash TEXT PRIMARY KEY, added_at TEXT NOT NULL)",
 """CREATE TABLE IF NOT EXISTS businesses(id TEXT PRIMARY KEY, canonical_domain TEXT UNIQUE, place_id TEXT UNIQUE, name TEXT NOT NULL,
    country TEXT NOT NULL, city TEXT, niche TEXT NOT NULL, phone_e164 TEXT, phone_raw TEXT, address TEXT, maps_url TEXT, rating REAL,
    source TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 0, first_seen_at TEXT NOT NULL)""",
 """CREATE TABLE IF NOT EXISTS inspections(id TEXT PRIMARY KEY, business_id TEXT NOT NULL, inspector_version TEXT, status TEXT NOT NULL,
    has_website INTEGER, website_url TEXT, wa_number_e164 TEXT, wa_status TEXT, wa_type TEXT, wa_type_confidence REAL, wa_source_url TEXT,
    chatbot_value TEXT, chatbot_vendor TEXT, chatbot_kind TEXT, email TEXT, signals TEXT, confidence REAL, evidence_uri TEXT, checked_at TEXT NOT NULL)""",
 """CREATE TABLE IF NOT EXISTS search_jobs(id TEXT PRIMARY KEY, user_id TEXT NOT NULL, idempotency_key TEXT, country TEXT NOT NULL, niche TEXT NOT NULL,
    city_ids TEXT NOT NULL, lead_count INTEGER NOT NULL CHECK(lead_count BETWEEN 1 AND 200), filters TEXT NOT NULL, mode TEXT NOT NULL DEFAULT 'live',
    status TEXT NOT NULL, accepted_count INTEGER NOT NULL DEFAULT 0, candidates_seen INTEGER NOT NULL DEFAULT 0, inspected_count INTEGER NOT NULL DEFAULT 0,
    cursor INTEGER NOT NULL DEFAULT 0, shortfall TEXT, message TEXT, cost_usd REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT,
    UNIQUE(user_id, idempotency_key))""",
 "CREATE TABLE IF NOT EXISTS job_candidates(job_id TEXT NOT NULL, dedupe_key TEXT NOT NULL, outcome TEXT, PRIMARY KEY(job_id, dedupe_key))",
 """CREATE TABLE IF NOT EXISTS job_leads(id TEXT PRIMARY KEY, job_id TEXT NOT NULL, business_id TEXT NOT NULL, inspection_id TEXT NOT NULL,
    hot_lead INTEGER NOT NULL DEFAULT 0, confidence REAL, feedback TEXT, saved INTEGER NOT NULL DEFAULT 0, exported_at TEXT, created_at TEXT NOT NULL,
    UNIQUE(job_id, business_id))""",
 "CREATE INDEX IF NOT EXISTS idx_jl_job ON job_leads(job_id)",
 "CREATE INDEX IF NOT EXISTS idx_insp_biz ON inspections(business_id, checked_at)",
 "CREATE INDEX IF NOT EXISTS idx_biz_mkt ON businesses(country, niche)",
]


def init_db():
    pk = "SERIAL PRIMARY KEY" if db.PG else "INTEGER PRIMARY KEY AUTOINCREMENT"
    for s in DDL:
        db.execute(s.format(pk=pk) if "{pk}" in s else s)
    seed()


def _exists(sql, a):
    return db.one(sql, a) is not None


def seed():
    for cc, niches in MATRIX.items():
        for n in niches:
            if not _exists("SELECT 1 AS x FROM country_niches WHERE country=? AND niche=?", (cc, n)):
                db.execute("INSERT INTO country_niches(country,niche,enabled) VALUES(?,?,1)", (cc, n))
    for (niche, region, lang), kws in KEYWORDS.items():
        for k in kws:
            if not _exists("SELECT 1 AS x FROM niche_keywords WHERE niche=? AND region=? AND keyword=?", (niche, region, k)):
                db.execute("INSERT INTO niche_keywords(niche,region,lang,keyword,enabled) VALUES(?,?,?,?,1)", (niche, region, lang, k))
    for cc, groups in CITIES.items():
        for admin1, names in groups.items():
            for n in names:
                if not _exists("SELECT 1 AS x FROM cities WHERE country=? AND name=? AND admin1=?", (cc, n, admin1)):
                    db.execute("INSERT INTO cities(country,admin1,name) VALUES(?,?,?)", (cc, admin1, n))
    for vendor, kind, scope, pats in SIGNATURES:
        for p in pats:
            if not _exists("SELECT 1 AS x FROM chatbot_signatures WHERE vendor=? AND scope=? AND pattern=?", (vendor, scope, p)):
                db.execute("INSERT INTO chatbot_signatures(vendor,kind,scope,pattern,enabled) VALUES(?,?,?,?,1)", (vendor, kind, scope, p))
    for k, v in DEFAULT_LIMITS.items():
        if not _exists("SELECT 1 AS x FROM app_limits WHERE key=?", (k,)):
            db.execute("INSERT INTO app_limits(key,value) VALUES(?,?)", (k, v))


def limit(key):
    r = db.one("SELECT value FROM app_limits WHERE key=?", (key,))
    return float(r["value"]) if r else float(DEFAULT_LIMITS[key])
