"""DiscoveryProvider adapters. Swap providers by adding an adapter with the same search() contract."""
import hashlib, json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from .config import settings
from .fetcher import FetchResult


class DiscoveryError(Exception):
    def __init__(self, msg, status=502, retryable=False):
        super().__init__(msg)
        self.status, self.retryable = status, retryable


def to_candidate(raw, city, source):
    name = (raw.get("title") or raw.get("name") or "").strip()
    if not name:
        return None
    return {"name": name, "place_id": raw.get("placeId") or raw.get("place_id"), "address": raw.get("address"),
            "city": raw.get("city") or city, "phone": raw.get("phone") or raw.get("phoneUnformatted"),
            "website": (raw.get("website") or "").strip() or None, "maps_url": raw.get("url") or raw.get("maps_url"),
            "rating": raw.get("totalScore") or raw.get("rating"), "source": source}


class ApifyProvider:
    name = "apify_google_maps"
    is_demo = False

    def search(self, query, location, limit, city=""):
        if not settings.live_enabled:
            raise DiscoveryError("APIFY_API_TOKEN is not configured on the backend.", 503)
        actor = settings.APIFY_ACTOR_ID.replace("/", "~")
        url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?timeout={settings.APIFY_TIMEOUT_SECS}"
        body = {"searchStringsArray": [query], "locationQuery": location, "maxCrawledPlacesPerSearch": limit, "language": "en",
                "scrapePlaceDetailPage": False, "maxReviews": 0, "maxImages": 0, "scrapeContacts": False, "includeWebResults": False}
        req = Request(url, data=json.dumps(body).encode(), method="POST",
                      headers={"Content-Type": "application/json", "Authorization": f"Bearer {settings.APIFY_API_TOKEN}"})
        try:
            with urlopen(req, timeout=settings.APIFY_TIMEOUT_SECS + 15) as r:
                data = json.loads(r.read().decode())
        except HTTPError as e:
            if e.code == 429:
                raise DiscoveryError("Apify rate limit reached.", 429, retryable=True)
            if e.code in (401, 402, 403):
                raise DiscoveryError("Apify rejected the credentials or the plan/credit limit was reached.", 502)
            raise DiscoveryError(f"Apify returned HTTP {e.code}.", 502, retryable=e.code >= 500)
        except (URLError, TimeoutError, OSError):
            raise DiscoveryError("Could not reach Apify (network error or timeout).", 504, retryable=True)
        except ValueError:
            raise DiscoveryError("Apify returned an unreadable response.")
        if not isinstance(data, list):
            raise DiscoveryError("Unexpected Apify response shape.")
        return [c for c in (to_candidate(x, city, self.name) for x in data[:limit]) if c]


# ---- Demo provider: fictional businesses + fixture pages, clearly flagged, no network ----
_VARIANTS = ["manual", "manual", "bot", "nowa", "nosite", "blocked", "automated", "probable", "text", "manual"]
PAGES = {
    "manual": '<html><body><a href="/contact">Contact</a><a href="https://wa.me/{num}?text=Hi">Chat on WhatsApp</a></body></html>',
    "bot": '<html><body><a href="https://wa.me/{num}">WhatsApp</a><script src="https://embed.tawk.to/abc/1"></script></body></html>',
    "automated": '<html><body><a href="https://wa.me/{num}?text=START_BOT">WhatsApp</a><script src="https://cdn.wati.io/w.js"></script></body></html>',
    "nowa": '<html><body><a href="/about">About</a><p>Call us on the office line.</p></body></html>',
    "probable": '<html><body><p>Visit our office today. We are open daily.</p><a href="/x">Services</a></body></html>',
    "text": '<html><body><p>WhatsApp: {pretty}</p><a href="/about">About</a></body></html>',
    "blocked": "<html><title>Just a moment...</title>cf-challenge</html>",
}


class DemoProvider:
    name = "demo"
    is_demo = True

    def search(self, query, location, limit, city=""):
        out = []
        qh = int(hashlib.sha256(query.encode()).hexdigest()[:6], 16)
        for i in range(limit):
            seed = qh + i * 7919
            variant = _VARIANTS[seed % len(_VARIANTS)]
            slug = f"demo-{city.lower().replace(' ', '')}-{qh % 997}-{i}"
            num = 500000000 + (seed % 99999999)
            out.append({"name": f"[DEMO] {city or 'City'} {query.title()} {qh % 997}-{i}", "place_id": f"demo_{slug}",
                        "address": f"Fictional address {i}, {city}", "city": city,
                        "phone": f"+971{num}" if variant != "nowa" else "+97145550170",
                        "website": None if variant == "nosite" else f"https://{slug}.demo.invalid/{variant}/{num}",
                        "maps_url": None, "rating": None, "source": "demo"})
        return out


def demo_fetcher(url):
    """Serves fixture pages for demo candidates; anything else is 'down'."""
    try:
        host, rest = url.split("://", 1)[1].split("/", 1)
        variant, num = (rest.split("/") + ["0"])[:2]
    except (ValueError, IndexError):
        return FetchResult("down", reason="bad demo url")
    if not host.endswith(".demo.invalid") or variant not in PAGES:
        return FetchResult("down", reason="not a demo page")
    html = PAGES[variant].format(num="971" + num, pretty=f"+971 {num[:2]} {num[2:5]} {num[5:]}")
    if variant == "blocked":
        return FetchResult("ok", 200, html, url)
    return FetchResult("ok", 200, html, url)
