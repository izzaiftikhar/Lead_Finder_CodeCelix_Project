"""Apify Google Maps discovery via REST (no SDK needed) + normalization + dedup."""
import json, re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .config import settings


class DiscoveryError(Exception):
    def __init__(self, msg, status=502):
        super().__init__(msg)
        self.status = status


def apify_search(query, location, limit):
    if not settings.live_enabled:
        raise DiscoveryError("APIFY_API_TOKEN is not configured on the backend.", 503)
    actor = settings.APIFY_ACTOR_ID.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?timeout={settings.APIFY_TIMEOUT_SECS}"
    body = {"searchStringsArray": [query], "locationQuery": location, "maxCrawledPlacesPerSearch": limit,
            "language": "en", "scrapePlaceDetailPage": False, "maxReviews": 0, "maxImages": 0,
            "scrapeContacts": False, "includeWebResults": False}
    req = Request(url, data=json.dumps(body).encode(), method="POST",
                  headers={"Content-Type": "application/json", "Authorization": f"Bearer {settings.APIFY_API_TOKEN}"})
    try:
        with urlopen(req, timeout=settings.APIFY_TIMEOUT_SECS + 15) as r:
            data = json.loads(r.read().decode())
    except HTTPError as e:
        if e.code == 429:
            raise DiscoveryError("Apify rate limit reached. Try again shortly.", 429)
        if e.code in (401, 403):
            raise DiscoveryError("Apify rejected the credentials or plan limits (check token/credits).", 502)
        raise DiscoveryError(f"Apify returned HTTP {e.code}.")
    except (URLError, TimeoutError, OSError):
        raise DiscoveryError("Could not reach Apify (network error or timeout).", 504)
    except ValueError:
        raise DiscoveryError("Apify returned an unreadable response.")
    if not isinstance(data, list):
        raise DiscoveryError("Unexpected Apify response shape.")
    return data[:limit]


def normalize(raw, niche, city_hint):
    name = (raw.get("title") or raw.get("name") or "").strip()
    if not name:
        return None
    site = (raw.get("website") or "").strip() or None
    return {
        "provider_place_id": raw.get("placeId") or raw.get("provider_place_id"),
        "business_name": name,
        "city": raw.get("city") or city_hint,
        "address": raw.get("address"),
        "niche": niche,
        "website": site,
        "phone": raw.get("phone") or raw.get("phoneUnformatted"),
        "category": raw.get("categoryName") or raw.get("category"),
        "rating": raw.get("totalScore") or raw.get("rating"),
        "reviews_count": raw.get("reviewsCount") or raw.get("reviews_count"),
        "maps_url": raw.get("url") or raw.get("google_maps_url"),
        "source": "apify_google_maps",
    }


def dedupe_key(rec):
    if rec.get("provider_place_id"):
        return "gp:" + rec["provider_place_id"]
    digits = re.sub(r"\D", "", rec.get("phone") or "")
    return "nm:" + re.sub(r"[^a-z0-9]", "", rec["business_name"].lower()) + "|" + digits


def dedupe(records):
    seen, out = set(), []
    for r in records:
        k = dedupe_key(r)
        if k not in seen:
            seen.add(k)
            out.append({**r, "dedupe_key": k})
    return out
