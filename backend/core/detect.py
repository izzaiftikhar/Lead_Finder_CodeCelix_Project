"""Deterministic detection rules (no LLM). Pure functions over page text + signature rows."""
import re
from urllib.parse import unquote_plus, urlparse
from .phones import normalize_phone

SOCIAL_HOSTS = ("facebook.com", "instagram.com", "linktr.ee", "wa.me", "twitter.com", "x.com", "linkedin.com", "tiktok.com",
                "youtube.com", "beacons.ai", "t.me", "api.whatsapp.com", "wa.link", "bit.ly", "snapchat.com")
PARKED_MARKERS = ("domain is for sale", "buy this domain", "this domain is parked", "domain parking", "sedoparking",
                  "hugedomains", "this domain may be for sale", "parked free", "domain has expired")
BLOCK_MARKERS = ("just a moment...", "attention required! | cloudflare", "g-recaptcha", "hcaptcha", "cf-challenge", "captcha-delivery")

WA_LINK = re.compile(r"(?:wa\.me/|api\.whatsapp\.com/send/?\?[^\s\"'<>]*?phone=|whatsapp://send/?\?[^\s\"'<>]*?phone=|web\.whatsapp\.com/send/?\?[^\s\"'<>]*?phone=)\+?(\d{8,15})", re.I)
PLUGIN_NUM = [
    re.compile(r"joinchat[^>]{0,400}?data-phone=[\"']?\+?(\d{8,15})", re.I | re.S),
    re.compile(r"data-phone=[\"']\+?(\d{8,15})[\"'][^>]{0,200}joinchat", re.I | re.S),
    re.compile(r"(?:getbutton|chaty|elfsight)[^<]{0,600}?[\"'](?:whatsapp|number|phone)[\"']\s*:\s*[\"']\+?(\d{8,15})", re.I | re.S),
    re.compile(r"[\"']whatsapp[\"']\s*:\s*[\"']\+?(\d{8,15})[\"']", re.I),
]
PHONE_RE = re.compile(r"\+?\d[\d\s().\-]{6,16}\d")
WA_WORD = re.compile(r"whats\s?app|واتس\s?اب|واتساب", re.I)
WA_AUTOMATION_TEXT = re.compile(r"whats\s?app\s+(chat\s?bot|ai\s+assistant|bot)|(ai|24/7)\s+(chat\s?bot|whats\s?app\s+assistant)|24/7\s+bot", re.I)
GENERIC_WIDGET = re.compile(r"""(?:id|class)\s*=\s*["'][^"']*(?:livechat|chat-widget|chatbot|chat-bot|chatwidget)[^"']*["']""", re.I)
TAGS = re.compile(r"<script.*?</script>|<style.*?</style>|<[^>]+>", re.I | re.S)


def host_of(url):
    try:
        h = (urlparse(url if "://" in url else "http://" + url).hostname or "").lower()
    except ValueError:
        return ""
    return h[4:] if h.startswith("www.") else h


def is_social(url):
    h = host_of(url)
    return any(h == s or h.endswith("." + s) for s in SOCIAL_HOSTS)


def canonical_domain(url):
    if not url or is_social(url):
        return None
    h = host_of(url)
    return h or None


def is_parked(html):
    low = (html or "").lower()
    return any(m in low for m in PARKED_MARKERS) or (len(low) < 400 and "<a" not in low and "<script" not in low and "<img" not in low)


def is_blocked_page(html):
    low = (html or "").lower()
    return any(m in low for m in BLOCK_MARKERS) and len(low) < 20000


def wa_from_url(url, country):
    m = WA_LINK.search(unquote_plus(url or ""))
    if m:
        e, k = normalize_phone("+" + m.group(1), country)
        if e:
            return e
    return None


def extract_whatsapp(pages, country):
    """pages: [(url, html)] in priority order. Returns dict or None. First match wins (Rule 2 order)."""
    for url, html in pages:                                 # 1. direct links
        m = WA_LINK.search(unquote_plus(html or ""))
        if m:
            e, _ = normalize_phone("+" + m.group(1), country)
            if e:
                return {"number": e, "rule": "link", "source_url": url, "matched": m.group(0)[:120]}
    for url, html in pages:                                 # 2. floating-button plugin config
        for rx in PLUGIN_NUM:
            m = rx.search(html or "")
            if m:
                e, _ = normalize_phone("+" + m.group(1), country)
                if e:
                    return {"number": e, "rule": "plugin", "source_url": url, "matched": m.group(0)[:120]}
    for url, html in pages:                                 # 3. "WhatsApp" within 60 chars of a number
        text = TAGS.sub(" ", html or "")
        for wm in WA_WORD.finditer(text):
            window = text[max(0, wm.start() - 60): wm.end() + 60]
            for pm in PHONE_RE.finditer(window):
                e, kind = normalize_phone(pm.group(), country)
                if e:
                    return {"number": e, "rule": "text", "source_url": url, "matched": window.strip()[:120]}
    return None


def match_signatures(blob_lower, signatures, scope):
    for s in signatures:
        if s["scope"] == scope and s.get("enabled", 1) and s["pattern"].lower() in blob_lower:
            return {"vendor": s["vendor"], "kind": s["kind"], "pattern": s["pattern"]}
    return None


def classify_chatbot(blob, signatures, inspection_ok):
    """Tri-state. NO only when inspection completed. Returns (value, vendor, kind, evidence)."""
    if not inspection_ok:
        return "UNKNOWN", None, None, None
    low = (blob or "").lower()
    hit = match_signatures(low, signatures, "chatbot")
    if hit:
        return "YES", hit["vendor"], hit["kind"], hit["pattern"]
    g = GENERIC_WIDGET.search(blob or "")
    if g:
        return "YES", None, "UNKNOWN_WIDGET", g.group(0)[:100]
    return "NO", None, None, None


def classify_wa_type(wa, blob, signatures, fully_inspected):
    """Returns (type, confidence, evidence). Inference from public signals only; never a live test."""
    if not wa or wa["status"] != "CONFIRMED" or not fully_inspected:
        return "UNKNOWN", 0.0, None
    low = (blob or "").lower()
    hit = match_signatures(low, signatures, "whatsapp")
    if hit:
        return "AUTOMATED", 0.9, hit["vendor"]
    if "text=start_bot" in low:
        return "AUTOMATED", 0.8, "start_bot link"
    if WA_AUTOMATION_TEXT.search(TAGS.sub(" ", blob or "")):
        return "AUTOMATED", 0.6, "site text mentions a WhatsApp bot/assistant"
    return "MANUAL", 0.7, "no bot signal found (not a live test)"


def overall_confidence(wa_status, wa_type_conf, chatbot, has_website, render="static"):
    c = {"CONFIRMED": 0.45, "PROBABLE": 0.2}.get(wa_status, 0.0)
    c += {"YES": 0.25, "NO": 0.15 if render == "static" else 0.25, "UNKNOWN": 0.0}[chatbot]
    c += 0.1 if has_website else 0.0
    c += 0.2 * (wa_type_conf or 0)
    return round(min(c, 1.0), 2)


def is_hot(wa_status, wa_type, chatbot):
    return wa_status == "CONFIRMED" and wa_type == "MANUAL" and chatbot == "NO"
