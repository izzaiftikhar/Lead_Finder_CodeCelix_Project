"""Search jobs: validation, background yield loop, estimate, lead queries, exports."""
import csv, hashlib, io, json, math, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from . import db, detect, inspector
from .config import settings
from .fetcher import fetch_page
from .phones import normalize_phone
from .providers import ApifyProvider, DemoProvider, DiscoveryError, demo_fetcher
from .schema import limit
from .seed_data import COUNTRIES, GULF, NICHES

ACTIVE = ("QUEUED", "RUNNING")
DEFAULT_FILTERS = {"whatsapp_confirmed_only": True, "no_chatbot_only": False, "manual_whatsapp_only": False,
                   "website_required": False, "exclude_previously_exported": True}


class AppError(Exception):
    def __init__(self, code, msg, status=400):
        super().__init__(msg)
        self.code, self.status = code, status


# ---- test hooks ----
provider_factory = lambda mode: DemoProvider() if mode == "demo" else ApifyProvider()
fetcher_factory = lambda mode: demo_fetcher if mode == "demo" else fetch_page


# ---------------- validation / creation ----------------
def validate_and_create(user, body, idem_key=None):
    cc, niche, mode = body.get("country"), body.get("niche"), body.get("mode", "live")
    if mode not in ("live", "demo"):
        raise AppError("BAD_MODE", "mode must be live or demo")
    if mode == "live" and not settings.live_enabled:
        raise AppError("LIVE_NOT_CONFIGURED", "Live discovery is not configured (APIFY_API_TOKEN missing). Use demo mode.", 503)
    if cc not in COUNTRIES:
        raise AppError("COUNTRY_NOT_SUPPORTED", "Unsupported country")
    if not db.one("SELECT 1 AS x FROM country_niches WHERE country=? AND niche=? AND enabled=1", (cc, niche)):
        raise AppError("NICHE_NOT_ALLOWED_FOR_COUNTRY", f"{niche} is not available in {COUNTRIES[cc]}")
    n, lo, hi = body.get("lead_count"), int(limit("min_lead_count")), int(limit("max_lead_count"))
    if not isinstance(n, int) or isinstance(n, bool) or not lo <= n <= hi:
        raise AppError("BAD_LEAD_COUNT", f"lead_count must be an integer between {lo} and {hi}")
    if body.get("all_cities"):
        ids = [r["id"] for r in db.rows("SELECT id FROM cities WHERE country=?", (cc,))]
    else:
        ids = body.get("city_ids")
        if not isinstance(ids, list) or not ids or not all(isinstance(i, int) for i in ids):
            raise AppError("NO_CITIES", "Select at least one city")
        ids = sorted(set(ids))
        found = db.rows(f"SELECT id FROM cities WHERE country=? AND id IN ({','.join('?' * len(ids))})", [cc] + ids)
        if len(found) != len(ids):
            raise AppError("CITY_NOT_IN_COUNTRY", "One or more cities do not belong to the selected country")
    f = {**DEFAULT_FILTERS, **{k: bool(v) for k, v in (body.get("filters") or {}).items() if k in DEFAULT_FILTERS}}
    if idem_key:
        ex = db.one("SELECT * FROM search_jobs WHERE user_id=? AND idempotency_key=?", (user["id"], idem_key))
        if ex:
            return ex["id"], False
    cap = int(limit("daily_cap"))
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    used = db.scalar("SELECT COALESCE(SUM(lead_count),0) FROM search_jobs WHERE user_id=? AND created_at>=?", (user["id"], since))
    if used + n > cap:
        raise AppError("QUOTA_EXCEEDED", f"Daily lead quota reached ({int(used)}/{cap} requested in the last 24h)", 429)
    if mode == "live" and db.scalar("SELECT COUNT(*) FROM search_jobs WHERE user_id=? AND status IN ('QUEUED','RUNNING') AND mode='live'", (user["id"],)) >= 2:
        raise AppError("TOO_MANY_JOBS", "You already have 2 live jobs running", 429)
    jid = db.uid()
    db.execute("INSERT INTO search_jobs(id,user_id,idempotency_key,country,niche,city_ids,lead_count,filters,mode,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
               (jid, user["id"], idem_key, cc, niche, json.dumps(ids), n, json.dumps(f), mode, "QUEUED", db.now()))
    return jid, True


def job_view(j):
    j = dict(j)
    for k in ("city_ids", "filters", "shortfall"):
        j[k] = json.loads(j[k]) if j.get(k) else None
    j.pop("user_id", None); j.pop("idempotency_key", None)
    return j


# ---------------- estimate ----------------
def _prior_yield(cc, niche):
    if niche in ("B2B_AGENCIES", "SAAS"):
        return 0.12
    if cc in GULF:
        return 0.5
    return 0.2 if niche == "CLINICS" else 0.25


def estimate(cc, niche, n):
    h = db.one("SELECT SUM(accepted_count) AS a, SUM(candidates_seen) AS c FROM search_jobs WHERE country=? AND niche=? AND status IN ('COMPLETED','PARTIAL') AND mode='live' AND candidates_seen>0", (cc, niche))
    y = (h["a"] / h["c"]) if h and h["c"] and h["a"] else _prior_yield(cc, niche)
    y = max(y, 0.03)
    cand = min(n / y, limit("candidate_factor") * n)
    per = 1.5 + settings.PAGE_DELAY_SECS * 2 / max(settings.INSPECT_WORKERS, 1)
    p50 = max(1, math.ceil(cand * per / 60))
    return {"minutes_p50": p50, "minutes_p90": max(p50 + 1, math.ceil(p50 * 1.8)), "expected_yield": round(y, 2),
            "basis": "past jobs" if h and h["c"] else "prior estimate"}


# ---------------- runner ----------------
def _queries(job, cities):
    gulf = job["country"] in GULF
    kws = db.rows("SELECT keyword, lang FROM niche_keywords WHERE niche=? AND enabled=1 AND (region='ANY' OR (region='GULF' AND ?=1)) ORDER BY id", (job["niche"], 1 if gulf else 0))
    out = []
    for kw in kws:                      # interleave cities per keyword so partial runs spread across the selection
        for c in cities:
            loc = f"{c['name']}, {c['admin1']}, {COUNTRIES[job['country']]}" if job["country"] in ("US", "GB") else f"{c['name']}, {COUNTRIES[job['country']]}"
            out.append((kw["keyword"], loc, c["name"]))
    return out


def _keys(c):
    k = set()
    if c.get("place_id"): k.add("gp:" + c["place_id"])
    d = detect.canonical_domain(c.get("website"))
    if d: k.add("dm:" + d)
    if not k:
        k.add("nm:" + "".join(ch for ch in c["name"].lower() if ch.isalnum()) + "|" + "".join(ch for ch in (c.get("phone") or "") if ch.isdigit()))
    return k


def _suppressed(c):
    hs = set()
    d = detect.canonical_domain(c.get("website"))
    if d: hs.add(hashlib.sha256(d.encode()).hexdigest())
    digits = "".join(ch for ch in (c.get("phone") or "") if ch.isdigit())
    if digits: hs.add(hashlib.sha256(digits.encode()).hexdigest())
    return bool(hs) and any(db.one("SELECT 1 AS x FROM suppression WHERE hash=?", (h,)) for h in hs)


def _upsert_business(c, job, is_demo):
    dom = detect.canonical_domain(c.get("website"))
    row = (db.one("SELECT id FROM businesses WHERE place_id=?", (c["place_id"],)) if c.get("place_id") else None) or \
          (db.one("SELECT id FROM businesses WHERE canonical_domain=?", (dom,)) if dom else None)
    e164, _ = normalize_phone(c.get("phone"), job["country"])
    if row:
        return row["id"]
    bid = db.uid()
    db.execute("INSERT INTO businesses(id,canonical_domain,place_id,name,country,city,niche,phone_e164,phone_raw,address,maps_url,rating,source,is_demo,first_seen_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (bid, dom, c.get("place_id"), c["name"], job["country"], c.get("city"), job["niche"], e164, c.get("phone"), c.get("address"),
                c.get("maps_url"), c.get("rating"), c["source"], 1 if is_demo else 0, db.now()))
    return bid


def _cached_inspection(bid):
    since = (datetime.now(timezone.utc) - timedelta(days=int(limit("cache_days")))).isoformat()
    r = db.one("SELECT * FROM inspections WHERE business_id=? AND checked_at>=? AND status IN ('OK','NO_WEBSITE') ORDER BY checked_at DESC LIMIT 1", (bid, since))
    return r


def _store_inspection(bid, rec):
    iid = db.uid()
    db.execute("INSERT INTO inspections(id,business_id,inspector_version,status,has_website,website_url,wa_number_e164,wa_status,wa_type,wa_type_confidence,wa_source_url,chatbot_value,chatbot_vendor,chatbot_kind,email,signals,confidence,evidence_uri,checked_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (iid, bid, rec["inspector_version"], rec["status"], rec["has_website"], rec["website_url"], rec["wa_number_e164"], rec["wa_status"], rec["wa_type"],
                rec["wa_type_confidence"], rec["wa_source_url"], rec["chatbot_value"], rec["chatbot_vendor"], rec["chatbot_kind"], rec["email"],
                json.dumps(rec["signals"]), rec["confidence"], None, db.now()))
    return iid


def decide(insp, filters):
    """insp: dict with inspection columns. Returns (accepted, reason)."""
    if not insp["wa_number_e164"]:
        return False, "no_whatsapp"
    if filters["whatsapp_confirmed_only"] and insp["wa_status"] != "CONFIRMED":
        return False, "no_whatsapp" if insp["wa_status"] is None else "whatsapp_not_confirmed"
    if filters["website_required"] and not insp["has_website"]:
        return False, "no_website"
    if filters["no_chatbot_only"] and insp["chatbot_value"] != "NO":
        return False, "filter_chatbot"
    if filters["manual_whatsapp_only"] and insp["wa_type"] != "MANUAL":
        return False, "filter_manual"
    return True, None


def _signatures():
    return db.rows("SELECT vendor,kind,scope,pattern,enabled FROM chatbot_signatures WHERE enabled=1")


def _status(jid):
    return db.scalar("SELECT status FROM search_jobs WHERE id=?", (jid,), default="")


def run_job(jid):
    job = db.one("SELECT * FROM search_jobs WHERE id=?", (jid,))
    if not job or job["status"] not in ACTIVE:
        return
    db.execute("UPDATE search_jobs SET status='RUNNING', started_at=COALESCE(started_at,?) WHERE id=? AND status IN ('QUEUED','RUNNING')", (db.now(), jid))
    try:
        _run(job)
    except Exception as e:  # noqa: crash -> FAILED with message; resume possible
        db.execute("UPDATE search_jobs SET status='FAILED', message=?, finished_at=? WHERE id=? AND status='RUNNING'", (f"Unexpected error: {type(e).__name__}", db.now(), jid))


def _bump(jid, **kv):
    sets = ",".join(f"{k}={k}+?" for k in kv)
    db.execute(f"UPDATE search_jobs SET {sets} WHERE id=?", list(kv.values()) + [jid])


def _run(job):
    jid, n, mode = job["id"], job["lead_count"], job["mode"]
    filters = {**DEFAULT_FILTERS, **json.loads(job["filters"])}
    ids = json.loads(job["city_ids"])
    cities = db.rows(f"SELECT id,name,admin1 FROM cities WHERE id IN ({','.join('?' * len(ids))}) ORDER BY id", ids)
    queries = _queries(job, cities)
    provider, fetcher, sigs = provider_factory(mode), fetcher_factory(mode), _signatures()
    cand_cap = int(limit("candidate_factor") * n)
    cost_cap = limit("job_cost_cap_usd")
    seen = set()
    for r in db.rows("SELECT dedupe_key FROM job_candidates WHERE job_id=?", (jid,)):
        seen.add(r["dedupe_key"])
    seen_wa = {r["wa_number_e164"] for r in db.rows("SELECT i.wa_number_e164 FROM job_leads jl JOIN inspections i ON i.id=jl.inspection_id WHERE jl.job_id=?", (jid,))}
    exported = {r["business_id"] for r in db.rows("SELECT jl.business_id FROM job_leads jl JOIN search_jobs sj ON sj.id=jl.job_id WHERE sj.user_id=? AND jl.exported_at IS NOT NULL", (job["user_id"],))} if filters["exclude_previously_exported"] else set()
    counts = {k: 0 for k in ("no_website", "no_whatsapp", "whatsapp_not_confirmed", "filter_chatbot", "filter_manual", "duplicate", "previously_exported", "inspection_failed", "suppressed")}
    cur = db.one("SELECT * FROM search_jobs WHERE id=?", (jid,))
    prev = json.loads(cur["shortfall"] or "{}").get("breakdown", {}) if cur["shortfall"] else {}
    for k, v in prev.items(): counts[k] = counts.get(k, 0) + v
    stop_reason = None
    qi = cur["cursor"]
    while True:
        cur = db.one("SELECT status,accepted_count,candidates_seen,cost_usd FROM search_jobs WHERE id=?", (jid,))
        if cur["status"] != "RUNNING":
            return                                   # cancelled elsewhere
        if cur["accepted_count"] >= n:
            break
        if qi >= len(queries): stop_reason = "no more candidates in the selected cities"; break
        if cur["candidates_seen"] >= cand_cap: stop_reason = "candidate limit reached"; break
        if cur["cost_usd"] >= cost_cap: stop_reason = "job cost cap reached"; break
        q, loc, cname = queries[qi]
        raw, attempt = None, 0
        while raw is None:
            try:
                raw = provider.search(q, loc, min(settings.PER_QUERY_LIMIT, cand_cap - cur["candidates_seen"]) or 1, city=cname)
            except DiscoveryError as e:
                attempt += 1
                if e.retryable and attempt <= 2:
                    time.sleep(2 ** attempt * (0 if mode == "demo" else 1)); continue
                db.execute("UPDATE search_jobs SET status='FAILED', message=?, finished_at=? WHERE id=? AND status='RUNNING'", (f"Discovery failed: {e}", db.now(), jid))
                return
        qi += 1
        fresh = []
        for c in raw:
            ks = _keys(c)
            if ks & seen:
                counts["duplicate"] += 1; continue
            seen |= ks
            if _suppressed(c):
                counts["suppressed"] += 1; continue
            for k in ks:
                db.execute("INSERT INTO job_candidates(job_id,dedupe_key,outcome) VALUES(?,?,NULL)", (jid, k)) if not db.one("SELECT 1 AS x FROM job_candidates WHERE job_id=? AND dedupe_key=?", (jid, k)) else None
            fresh.append(c)
        db.execute("UPDATE search_jobs SET cursor=?, candidates_seen=candidates_seen+?, cost_usd=cost_usd+? WHERE id=?",
                   (qi, len(fresh), 0 if mode == "demo" else round(len(raw) * settings.COST_PER_CANDIDATE, 4), jid))
        _process(job, fresh, filters, fetcher, sigs, counts, seen_wa, exported, n)
        db.execute("UPDATE search_jobs SET shortfall=? WHERE id=?", (json.dumps({"breakdown": counts}), jid))
    acc = db.scalar("SELECT accepted_count FROM search_jobs WHERE id=?", (jid,))
    if acc >= n:
        db.execute("UPDATE search_jobs SET status='COMPLETED', message=?, finished_at=? WHERE id=? AND status='RUNNING'", (f"{acc} of {n} leads found", db.now(), jid))
    else:
        bd = {k: v for k, v in counts.items() if v}
        msg = f"{acc} of {n} found: {stop_reason or 'search ended'}."
        if job["country"] not in GULF or job["niche"] in ("B2B_AGENCIES", "SAAS"):
            msg += " Few businesses in this market publish WhatsApp numbers; partial results are common."
        db.execute("UPDATE search_jobs SET status='PARTIAL', message=?, shortfall=?, finished_at=? WHERE id=? AND status='RUNNING'",
                   (msg, json.dumps({"breakdown": counts, "reason": stop_reason, "shown": bd}), db.now(), jid))


def _process(job, cands, filters, fetcher, sigs, counts, seen_wa, exported, n):
    jid, is_demo = job["id"], job["mode"] == "demo"
    if not cands:
        return
    prepared = []
    for c in cands:
        bid = _upsert_business(c, job, is_demo)
        prepared.append((c, bid, _cached_inspection(bid)))
    todo = [(c, bid) for c, bid, ci in prepared if ci is None]
    results = {}
    ex = ThreadPoolExecutor(max_workers=max(1, min(settings.INSPECT_WORKERS, len(todo) or 1)))
    futs = {ex.submit(inspector.inspect, c, job["country"], fetcher, sigs): (c, bid) for c, bid in todo}
    try:
        for f in as_completed(futs):
            results[futs[f][1]] = f.result()
            if _status(jid) != "RUNNING":
                return
    finally:
        ex.shutdown(wait=True, cancel_futures=True)
    for c, bid, cached in prepared:
        if db.scalar("SELECT accepted_count FROM search_jobs WHERE id=?", (jid,)) >= n:
            break
        if cached is not None:
            iid, insp = cached["id"], cached
        else:
            rec = results[bid]
            iid, insp = _store_inspection(bid, rec), {**rec}
        db.execute("UPDATE search_jobs SET inspected_count=inspected_count+1 WHERE id=?", (jid,))
        if insp["status"] in ("BLOCKED", "TIMEOUT"):
            counts["inspection_failed"] += 1
        ok, reason = decide(insp, filters)
        if ok and insp["wa_number_e164"] in seen_wa:
            counts["duplicate"] += 1; continue
        if ok and bid in exported:
            counts["previously_exported"] += 1; continue
        if not ok:
            counts[reason if reason in counts else "no_whatsapp"] += 1; continue
        if db.one("SELECT 1 AS x FROM job_leads WHERE job_id=? AND business_id=?", (jid, bid)):
            counts["duplicate"] += 1; continue
        hot = detect.is_hot(insp["wa_status"], insp["wa_type"], insp["chatbot_value"])
        db.execute("INSERT INTO job_leads(id,job_id,business_id,inspection_id,hot_lead,confidence,created_at) VALUES(?,?,?,?,?,?,?)",
                   (db.uid(), jid, bid, iid, 1 if hot else 0, insp["confidence"], db.now()))
        seen_wa.add(insp["wa_number_e164"])
        db.execute("UPDATE search_jobs SET accepted_count=accepted_count+1 WHERE id=?", (jid,))


class Runner:
    def __init__(self):
        self.pool = ThreadPoolExecutor(max_workers=max(1, settings.JOB_WORKERS))
        self.pending = set()
        self.lock = threading.Lock()

    def submit(self, jid):
        with self.lock:
            if jid in self.pending:
                return
            self.pending.add(jid)
        def go():
            try: run_job(jid)
            finally:
                with self.lock: self.pending.discard(jid)
        self.pool.submit(go)

    def recover(self):
        """Worker crash/restart: re-queue unfinished jobs from DB state. Unique constraints prevent duplicate leads."""
        for r in db.rows("SELECT id FROM search_jobs WHERE status IN ('QUEUED','RUNNING')"):
            self.submit(r["id"])


runner = Runner()


def cancel(jid):
    return db.execute("UPDATE search_jobs SET status='CANCELLED', message='Cancelled by user', finished_at=? WHERE id=? AND status IN ('QUEUED','RUNNING')", (db.now(), jid))


def resume(jid):
    n = db.execute("UPDATE search_jobs SET status='QUEUED', message=NULL, finished_at=NULL WHERE id=? AND status IN ('CANCELLED','FAILED','PARTIAL')", (jid,))
    if n:
        runner.submit(jid)
    return n


# ---------------- reads ----------------
LEAD_SQL = """SELECT jl.id, jl.job_id, jl.hot_lead, jl.confidence, jl.feedback, jl.saved, jl.exported_at, jl.created_at,
  b.name AS business_name, b.country, b.city, b.niche, b.phone_raw, b.phone_e164, b.address, b.maps_url, b.rating, b.is_demo, b.source,
  i.has_website, i.website_url, i.wa_number_e164, i.wa_status, i.wa_type, i.wa_type_confidence, i.wa_source_url, i.chatbot_value, i.chatbot_vendor,
  i.chatbot_kind, i.email, i.signals, i.status AS inspection_status, i.checked_at, i.evidence_uri
  FROM job_leads jl JOIN businesses b ON b.id=jl.business_id JOIN inspections i ON i.id=jl.inspection_id JOIN search_jobs sj ON sj.id=jl.job_id"""


def lead_view(r):
    return {"id": r["id"], "job_id": r["job_id"], "business_name": r["business_name"], "niche": r["niche"], "country": r["country"], "city": r["city"],
            "website": {"url": r["website_url"], "has_website": bool(r["has_website"])},
            "whatsapp": {"number": r["wa_number_e164"], "status": r["wa_status"], "type": r["wa_type"], "type_confidence": r["wa_type_confidence"], "source_url": r["wa_source_url"]},
            "chatbot": {"value": r["chatbot_value"], "vendor": r["chatbot_vendor"], "kind": r["chatbot_kind"]},
            "hot_lead": bool(r["hot_lead"]), "phone": r["phone_e164"] or r["phone_raw"], "email": r["email"], "address": r["address"], "maps_url": r["maps_url"],
            "confidence": r["confidence"], "evidence_url": r["evidence_uri"], "checked_at": r["checked_at"], "inspection_status": r["inspection_status"],
            "signals": json.loads(r["signals"]) if r["signals"] else {}, "feedback": r["feedback"], "saved": bool(r["saved"]), "exported_at": r["exported_at"],
            "is_demo": bool(r["is_demo"]), "source": r["source"], "rating": r["rating"]}


SORTS = {"confidence": "jl.confidence DESC", "name": "b.name", "newest": "jl.created_at DESC", "hot": "jl.hot_lead DESC, jl.confidence DESC"}


def list_leads(user, job_id=None, saved=False, hot=None, chatbot=None, wa_type=None, sort="hot", q=None, limit_=500):
    where, a = ["sj.user_id=?"], [user["id"]]
    if job_id: where.append("jl.job_id=?"); a.append(job_id)
    if saved: where.append("jl.saved=1")
    if hot: where.append("jl.hot_lead=1")
    if chatbot in ("YES", "NO", "UNKNOWN"): where.append("i.chatbot_value=?"); a.append(chatbot)
    if wa_type in ("MANUAL", "AUTOMATED", "UNKNOWN"): where.append("i.wa_type=?"); a.append(wa_type)
    if q: where.append("LOWER(b.name) LIKE ?"); a.append("%" + q.lower() + "%")
    return [lead_view(r) for r in db.rows(f"{LEAD_SQL} WHERE {' AND '.join(where)} ORDER BY {SORTS.get(sort, SORTS['hot'])} LIMIT ?", a + [limit_])]


EXPORT_COLS = ["Business name", "Niche", "Country", "City", "Website", "Has website", "WhatsApp number", "WhatsApp status", "WhatsApp type",
               "Website chatbot", "Chatbot detail", "Hot lead", "Phone", "Email", "Address", "Maps URL", "Confidence", "Evidence URL", "Checked at", "Demo data"]


def export_rows(leads):
    out = []
    for l in leads:
        cb = l["chatbot"]
        out.append([l["business_name"], l["niche"], l["country"], l["city"], l["website"]["url"] or "No website", "Yes" if l["website"]["has_website"] else "No",
                    l["whatsapp"]["number"], l["whatsapp"]["status"], l["whatsapp"]["type"], cb["value"],
                    " / ".join(x for x in (cb["vendor"], cb["kind"]) if x), "Yes" if l["hot_lead"] else "No", l["phone"], l["email"], l["address"],
                    l["maps_url"], l["confidence"], l["evidence_url"], l["checked_at"], "Yes (fictional)" if l["is_demo"] else "No"])
    return out


def to_csv(leads):
    from .xlsx import safe
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(EXPORT_COLS)
    for r in export_rows(leads):
        w.writerow([safe(v) for v in r])
    return "\ufeff" + out.getvalue()


def mark_exported(ids):
    for i in ids:
        db.execute("UPDATE job_leads SET exported_at=COALESCE(exported_at,?) WHERE id=?", (db.now(), i))


def stats(user):
    uid = user["id"]
    base = "FROM job_leads jl JOIN search_jobs sj ON sj.id=jl.job_id JOIN inspections i ON i.id=jl.inspection_id WHERE sj.user_id=?"
    c = lambda extra="": db.scalar(f"SELECT COUNT(*) {base} {extra}", (uid,))
    return {"total_leads": c(), "hot_leads": c("AND jl.hot_lead=1"), "whatsapp_confirmed": c("AND i.wa_status='CONFIRMED'"),
            "whatsapp_manual": c("AND i.wa_type='MANUAL'"), "whatsapp_automated": c("AND i.wa_type='AUTOMATED'"),
            "chatbot_yes": c("AND i.chatbot_value='YES'"), "saved": c("AND jl.saved=1"),
            "jobs": db.scalar("SELECT COUNT(*) FROM search_jobs WHERE user_id=?", (uid,)),
            "jobs_active": db.scalar("SELECT COUNT(*) FROM search_jobs WHERE user_id=? AND status IN ('QUEUED','RUNNING')", (uid,)),
            "by_niche": db.rows(f"SELECT sj.niche AS label, COUNT(*) AS n {base} GROUP BY sj.niche ORDER BY n DESC", (uid,)),
            "recent_jobs": [job_view(j) for j in db.rows("SELECT * FROM search_jobs WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (uid,))]}
