import hashlib, io, threading, time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from .core import auth, db, detect, jobs, schema
from .core.config import settings, DEFAULT_LIMITS
from .core.seed_data import COUNTRIES, NICHES
from .core.xlsx import build_xlsx
from .schemas import Creds, Feedback, JobCreate, KeywordIn, LimitIn, NicheToggle, SignatureIn, SuppressIn


@asynccontextmanager
async def lifespan(app):
    if settings.ENVIRONMENT == "production":
        if not settings.BACKEND_API_KEY:
            raise RuntimeError("BACKEND_API_KEY must be set when ENVIRONMENT=production")
        if not db.PG:
            print("WARNING: production is running on SQLite; data will be lost on redeploy. Set DATABASE_URL.", flush=True)
        if not settings.ABUSE_CONTACT:
            print("WARNING: ABUSE_CONTACT is not set; the crawler User-Agent has no contact.", flush=True)
    schema.init_db()
    jobs.runner.recover()
    yield


app = FastAPI(title="CodeCelix Lead Finder API", version="2.0.0", lifespan=lifespan)
if settings.ALLOWED_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"])

_hits, _rl = defaultdict(deque), threading.Lock()


def _ip(request):
    return (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?")).split(",")[0].strip()


@app.exception_handler(jobs.AppError)
async def app_error(request, e):
    return JSONResponse({"detail": str(e), "code": e.code}, status_code=e.status)


@app.exception_handler(auth.AuthError)
async def auth_error(request, e):
    return JSONResponse({"detail": str(e)}, status_code=e.status)


@app.middleware("http")
async def guard(request: Request, call_next):
    p = request.url.path
    if p.startswith("/api") and p != "/api/health":
        if settings.BACKEND_API_KEY and request.headers.get("x-api-key") != settings.BACKEND_API_KEY:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        t, q = time.time(), _hits[_ip(request)]
        with _rl:
            while q and q[0] < t - 60: q.popleft()
            if len(q) >= settings.RATE_LIMIT_PER_MIN:
                return JSONResponse({"detail": "Too many requests"}, status_code=429)
            q.append(t)
    return await call_next(request)


def _token(authorization):
    return authorization[7:] if authorization and authorization.lower().startswith("bearer ") else None


def current_user(authorization: str = Header(default=None)):
    u = auth.user_from_token(_token(authorization))
    if not u:
        raise HTTPException(401, "Please sign in")
    return u


def admin_user(u=Depends(current_user)):
    if u["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return u


def own_job(jid: str, u):
    j = db.one("SELECT * FROM search_jobs WHERE id=? AND user_id=?", (jid, u["id"]))
    if not j:
        raise HTTPException(404, "Job not found")
    return j


# ---------- public ----------
@app.get("/api/health")
def health():
    return {"status": "ok", "database": "PostgreSQL" if db.PG else "SQLite", "live_discovery_configured": settings.live_enabled}


@app.post("/api/auth/register")
def register(c: Creds, request: Request):
    auth.register(c.email, c.password)
    token, user = auth.login(c.email, c.password, _ip(request))
    return {"token": token, "user": user}


@app.post("/api/auth/login")
def login(c: Creds, request: Request):
    token, user = auth.login(c.email, c.password, _ip(request))
    return {"token": token, "user": user}


@app.post("/api/auth/logout")
def logout(authorization: str = Header(default=None)):
    auth.logout(_token(authorization))
    return {"ok": True}


@app.get("/api/auth/me")
def me(u=Depends(current_user)):
    return {"user": u, "live_available": settings.live_enabled}


# ---------- markets ----------
@app.get("/api/markets")
def markets(u=Depends(current_user)):
    rows = db.rows("SELECT country, niche FROM country_niches WHERE enabled=1 ORDER BY country, niche")
    out = []
    for cc, name in COUNTRIES.items():
        out.append({"code": cc, "name": name, "niches": [{"code": r["niche"], "name": NICHES.get(r["niche"], r["niche"])} for r in rows if r["country"] == cc]})
    return {"countries": [c for c in out if c["niches"]], "live_available": settings.live_enabled,
            "limits": {"min": int(jobs.limit("min_lead_count")), "max": int(jobs.limit("max_lead_count"))}}


@app.get("/api/markets/{cc}/cities")
def cities(cc: str, q: str = Query("", max_length=60), admin1: str = Query("", max_length=60), limit: int = Query(500, ge=1, le=2000), u=Depends(current_user)):
    if cc not in COUNTRIES:
        raise HTTPException(400, "Unsupported country")
    where, a = ["country=?"], [cc]
    if q: where.append("LOWER(name) LIKE ?"); a.append("%" + q.lower() + "%")
    if admin1: where.append("admin1=?"); a.append(admin1)
    items = db.rows(f"SELECT id, name, admin1 FROM cities WHERE {' AND '.join(where)} ORDER BY admin1, name LIMIT ?", a + [limit])
    return {"items": items, "admin1": [r["admin1"] for r in db.rows("SELECT DISTINCT admin1 FROM cities WHERE country=? ORDER BY admin1", (cc,))]}


@app.get("/api/estimate")
def est(country: str, niche: str, lead_count: int = Query(50, ge=1, le=200), u=Depends(current_user)):
    return jobs.estimate(country, niche, lead_count)


# ---------- jobs ----------
@app.post("/api/jobs", status_code=202)
def create_job(b: JobCreate, idempotency_key: str = Header(default=None), u=Depends(current_user)):
    jid, new = jobs.validate_and_create(u, b.model_dump(), (idempotency_key or None))
    if new:
        jobs.runner.submit(jid)
    j = own_job(jid, u)
    return {"id": jid, "status": j["status"], "estimate": jobs.estimate(b.country, b.niche, b.lead_count)}


@app.get("/api/jobs")
def list_jobs(limit: int = Query(50, ge=1, le=200), u=Depends(current_user)):
    return {"items": [jobs.job_view(j) for j in db.rows("SELECT * FROM search_jobs WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (u["id"], limit))]}


@app.get("/api/jobs/{jid}")
def get_job(jid: str, u=Depends(current_user)):
    return jobs.job_view(own_job(jid, u))


@app.post("/api/jobs/{jid}/cancel")
def cancel_job(jid: str, u=Depends(current_user)):
    own_job(jid, u)
    return {"cancelled": bool(jobs.cancel(jid))}


@app.post("/api/jobs/{jid}/resume")
def resume_job(jid: str, u=Depends(current_user)):
    own_job(jid, u)
    return {"resumed": bool(jobs.resume(jid))}


@app.post("/api/jobs/{jid}/rerun", status_code=202)
def rerun(jid: str, u=Depends(current_user)):
    j = jobs.job_view(own_job(jid, u))
    nid, _ = jobs.validate_and_create(u, {"country": j["country"], "niche": j["niche"], "city_ids": j["city_ids"], "lead_count": j["lead_count"],
                                          "filters": j["filters"], "mode": j["mode"]})
    jobs.runner.submit(nid)
    return {"id": nid, "status": "QUEUED"}


@app.get("/api/jobs/{jid}/leads")
def job_leads(jid: str, hot: bool = False, chatbot: str = "", wa_type: str = "", sort: str = "hot", q: str = Query("", max_length=80), u=Depends(current_user)):
    own_job(jid, u)
    return {"items": jobs.list_leads(u, jid, hot=hot, chatbot=chatbot or None, wa_type=wa_type or None, sort=sort, q=q or None)}


@app.get("/api/jobs/{jid}/export")
def export(jid: str, format: str = "csv", u=Depends(current_user)):
    j = own_job(jid, u)
    leads = jobs.list_leads(u, jid, sort="hot", limit_=5000)
    jobs.mark_exported([l["id"] for l in leads])
    name = f"codecelix-leads-{j['country']}-{j['niche']}-{jid[:8]}"
    if format == "xlsx":
        data = build_xlsx(jobs.EXPORT_COLS, jobs.export_rows(leads))
        return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={name}.xlsx"})
    if format != "csv":
        raise HTTPException(400, "format must be csv or xlsx")
    return Response(jobs.to_csv(leads), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={name}.csv"})


# ---------- leads ----------
def own_lead(lid, u):
    r = db.one("SELECT jl.id FROM job_leads jl JOIN search_jobs sj ON sj.id=jl.job_id WHERE jl.id=? AND sj.user_id=?", (lid, u["id"]))
    if not r:
        raise HTTPException(404, "Lead not found")


@app.post("/api/leads/{lid}/feedback")
def feedback(lid: str, f: Feedback, u=Depends(current_user)):
    own_lead(lid, u)
    if f.value not in ("CORRECT", "WRONG_WHATSAPP", "WRONG_CHATBOT", "NOT_RELEVANT"):
        raise HTTPException(400, "Invalid feedback value")
    db.execute("UPDATE job_leads SET feedback=? WHERE id=?", (f.value, lid))
    return {"feedback": f.value}


@app.post("/api/leads/{lid}/save")
def save(lid: str, u=Depends(current_user)):
    own_lead(lid, u); db.execute("UPDATE job_leads SET saved=1 WHERE id=?", (lid,)); return {"saved": True}


@app.delete("/api/leads/{lid}/save")
def unsave(lid: str, u=Depends(current_user)):
    own_lead(lid, u); db.execute("UPDATE job_leads SET saved=0 WHERE id=?", (lid,)); return {"saved": False}


@app.get("/api/saved")
def saved(u=Depends(current_user)):
    return {"items": jobs.list_leads(u, saved=True, limit_=1000)}


@app.get("/api/stats")
def stats(u=Depends(current_user)):
    return jobs.stats(u)


# ---------- admin ----------
@app.get("/api/admin/config")
def admin_config(a=Depends(admin_user)):
    return {"country_niches": db.rows("SELECT * FROM country_niches ORDER BY country, niche"),
            "keywords": db.rows("SELECT * FROM niche_keywords ORDER BY niche, region, id"),
            "signatures": db.rows("SELECT * FROM chatbot_signatures ORDER BY scope, vendor, id"),
            "limits": db.rows("SELECT * FROM app_limits ORDER BY key"), "suppressed": db.scalar("SELECT COUNT(*) FROM suppression"),
            "users": db.scalar("SELECT COUNT(*) FROM users")}


@app.put("/api/admin/country-niches")
def put_cn(b: NicheToggle, a=Depends(admin_user)):
    if b.country not in COUNTRIES or b.niche not in NICHES:
        raise HTTPException(400, "Unknown country or niche")
    if db.one("SELECT 1 AS x FROM country_niches WHERE country=? AND niche=?", (b.country, b.niche)):
        db.execute("UPDATE country_niches SET enabled=? WHERE country=? AND niche=?", (1 if b.enabled else 0, b.country, b.niche))
    else:
        db.execute("INSERT INTO country_niches(country,niche,enabled) VALUES(?,?,?)", (b.country, b.niche, 1 if b.enabled else 0))
    return {"ok": True}


@app.put("/api/admin/niche-keywords")
def put_kw(b: KeywordIn, a=Depends(admin_user)):
    if b.niche not in NICHES or b.region not in ("ANY", "GULF"):
        raise HTTPException(400, "Invalid niche or region")
    if b.id:
        db.execute("UPDATE niche_keywords SET niche=?,region=?,lang=?,keyword=?,enabled=? WHERE id=?", (b.niche, b.region, b.lang, b.keyword, int(b.enabled), b.id))
    else:
        db.execute("INSERT INTO niche_keywords(niche,region,lang,keyword,enabled) VALUES(?,?,?,?,?)", (b.niche, b.region, b.lang, b.keyword, int(b.enabled)))
    return {"ok": True}


@app.delete("/api/admin/niche-keywords/{kid}")
def del_kw(kid: int, a=Depends(admin_user)):
    db.execute("DELETE FROM niche_keywords WHERE id=?", (kid,)); return {"ok": True}


@app.put("/api/admin/chatbot-signatures")
def put_sig(b: SignatureIn, a=Depends(admin_user)):
    if b.kind not in ("AI_BOT", "LIVE_CHAT", "UNKNOWN_WIDGET") or b.scope not in ("chatbot", "whatsapp"):
        raise HTTPException(400, "Invalid kind or scope")
    if b.id:
        db.execute("UPDATE chatbot_signatures SET vendor=?,kind=?,scope=?,pattern=?,enabled=? WHERE id=?", (b.vendor, b.kind, b.scope, b.pattern.lower(), int(b.enabled), b.id))
    else:
        db.execute("INSERT INTO chatbot_signatures(vendor,kind,scope,pattern,enabled) VALUES(?,?,?,?,?)", (b.vendor, b.kind, b.scope, b.pattern.lower(), int(b.enabled)))
    return {"ok": True}


@app.delete("/api/admin/chatbot-signatures/{sid}")
def del_sig(sid: int, a=Depends(admin_user)):
    db.execute("DELETE FROM chatbot_signatures WHERE id=?", (sid,)); return {"ok": True}


@app.put("/api/admin/limits")
def put_limit(b: LimitIn, a=Depends(admin_user)):
    if b.key not in DEFAULT_LIMITS or b.value < 0 or (b.key == "max_lead_count" and b.value > 200):
        raise HTTPException(400, "Invalid limit")
    db.execute("UPDATE app_limits SET value=? WHERE key=?", (str(b.value), b.key)); return {"ok": True}


@app.post("/api/admin/suppression")
def suppress(b: SuppressIn, a=Depends(admin_user)):
    v = b.value.strip().lower()
    norm = detect.canonical_domain(v) or "".join(ch for ch in v if ch.isdigit())
    if not norm:
        raise HTTPException(400, "Enter a domain or phone number")
    h = hashlib.sha256(norm.encode()).hexdigest()
    if not db.one("SELECT 1 AS x FROM suppression WHERE hash=?", (h,)):
        db.execute("INSERT INTO suppression(hash,added_at) VALUES(?,?)", (h, db.now()))
    return {"ok": True}


@app.get("/api/admin/cost")
def cost(a=Depends(admin_user)):
    return {"by_day": db.rows("SELECT SUBSTR(created_at,1,10) AS day, COUNT(*) AS jobs, SUM(cost_usd) AS cost_usd, SUM(accepted_count) AS leads FROM search_jobs GROUP BY SUBSTR(created_at,1,10) ORDER BY day DESC LIMIT 30"),
            "total_usd": db.scalar("SELECT COALESCE(SUM(cost_usd),0) FROM search_jobs"), "note": "Estimated from candidates x COST_PER_CANDIDATE; check your Apify bill for actuals."}
