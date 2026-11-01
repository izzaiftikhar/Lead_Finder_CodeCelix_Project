import json
from concurrent.futures import ThreadPoolExecutor
from .classify import classify_lead
from .config import settings, INDUSTRIES
from .discovery import apify_search, normalize, dedupe, DiscoveryError
from .inspect_site import fetch_homepage
from . import db


def build_lead(rec, country, html, fetch_status, final_url):
    c = classify_lead(rec.get("phone"), rec.get("website"), html, fetch_status,
                      evidence_texts=[rec.get("phone") or ""], source_url=final_url or rec.get("website"))
    ev = {"whatsapp": c["whatsapp"], "chatbot": c["chatbot"], "website_fetch": fetch_status,
          "provider": rec["source"], "maps_url": rec.get("maps_url"),
          "rule": "HOT = WhatsApp CONFIRMED and chatbot NOT_DETECTED"}
    return {**rec, "country": country, "whatsapp_number": c["whatsapp"]["number"],
            "whatsapp_state": c["whatsapp"]["state"], "chatbot_state": c["chatbot"]["state"],
            "chatbot_vendor": c["chatbot"]["vendor"], "is_hot": 1 if c["hot"] else 0, "lead_score": c["score"],
            "evidence": json.dumps(ev), "is_demo": 0}


def live_search(country, city, niche, limit, searcher=apify_search, fetcher=fetch_homepage):
    limit = min(limit, settings.MAX_LIVE_RESULTS)
    query = INDUSTRIES[niche]
    loc = f"{city}, {country}" if country != "UAE" else f"{city}, United Arab Emirates"
    raw = searcher(query, loc, limit)
    recs = dedupe([r for r in (normalize(x, niche, city) for x in raw) if r])
    with ThreadPoolExecutor(max_workers=8) as ex:
        fetched = list(ex.map(lambda r: fetcher(r.get("website")), recs))
    ids = []
    for r, (st, html, final) in zip(recs, fetched):
        i, _ = db.upsert_lead(build_lead(r, country, html, st, final))
        ids.append(i)
    return ids, len(raw), len(recs)
