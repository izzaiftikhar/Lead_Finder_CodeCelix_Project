"""Website inspection (tier 1: static HTTP fetch). Produces an immutable inspection record dict."""
import re, time
from urllib.parse import urljoin
from . import detect
from .config import settings
from .phones import normalize_phone, is_whatsapp_capable

VERSION = "http-1"
LINK_RE = re.compile(r"""href\s*=\s*["']([^"'#]+)["']""", re.I)
CONTACT_HINT = re.compile(r"contact|about|اتصل|تواصل|من-نحن|عن-ا", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _pick_pages(base_url, html, limit=4):
    host = detect.host_of(base_url)
    out = []
    for h in LINK_RE.findall(html or ""):
        if h.lower().startswith(("mailto:", "tel:", "javascript:")) or not CONTACT_HINT.search(h):
            continue
        u = urljoin(base_url, h)
        if detect.host_of(u) == host and u.rstrip("/") != base_url.rstrip("/") and u not in out:
            out.append(u)
        if len(out) >= limit:
            break
    if not out:
        out.append(urljoin(base_url, "/contact"))
    return out


def _result(status, has_site, site_url, wa, wa_type, wa_conf, cb, signals, phone, email, render="static"):
    chatbot, vendor, kind, _ = cb
    wa_status = wa["status"] if wa else None
    return {"inspector_version": VERSION, "status": status, "has_website": 1 if has_site else 0, "website_url": site_url,
            "wa_number_e164": wa["number"] if wa else None, "wa_status": wa_status, "wa_type": wa_type,
            "wa_type_confidence": wa_conf, "wa_source_url": wa.get("source_url") if wa else None,
            "chatbot_value": chatbot, "chatbot_vendor": vendor, "chatbot_kind": kind, "email": email,
            "signals": {**signals, "render": render}, "evidence_uri": None,
            "confidence": detect.overall_confidence(wa_status, wa_conf, chatbot, has_site, render),
            "hot": detect.is_hot(wa_status, wa_type, chatbot)}


def inspect(cand, country, fetcher, signatures, filters_confirmed_only=True):
    """cand: normalized candidate. fetcher(url)->FetchResult. Always returns a record; never raises."""
    signals = {"pages": [], "notes": []}
    site = (cand.get("website") or "").strip() or None
    wa = None
    # A wa.me link given as the business's website is a business-published WhatsApp number.
    if site and detect.host_of(site) in ("wa.me", "api.whatsapp.com", "wa.link"):
        n = detect.wa_from_url(site, country)
        if n:
            wa = {"status": "CONFIRMED", "number": n, "source_url": site, "rule": "link"}
        site = None
    elif site and detect.is_social(site):
        signals["notes"].append("website field is a social/link-in-bio page: treated as no website")
        site = None

    status, has_site, fully, blob = "NO_WEBSITE", False, False, ""
    pages_for_wa = []
    if site:
        t0 = time.time()
        first = fetcher(site)
        signals["pages"].append({"url": site, "status": first.status, "code": first.code})
        if first.status == "ok" and detect.is_blocked_page(first.html):
            status, has_site = "BLOCKED", True
            signals["notes"].append("bot challenge page")
        elif first.status == "ok" and detect.is_parked(first.html):
            signals["notes"].append("domain looks parked")
            status, has_site = "NO_WEBSITE", False
        elif first.status == "ok":
            has_site, status, fully = True, "OK", True
            base = first.final_url or site
            pages_for_wa.append((base, first.html))
            for u in _pick_pages(base, first.html):
                if time.time() - t0 > settings.SITE_HARD_TIMEOUT_SECS or len(pages_for_wa) >= 5:
                    signals["notes"].append("site time budget reached")
                    break
                time.sleep(settings.PAGE_DELAY_SECS)
                r = fetcher(u)
                signals["pages"].append({"url": u, "status": r.status, "code": r.code})
                if r.status == "ok" and not detect.is_blocked_page(r.html):
                    pages_for_wa.append((r.final_url or u, r.html))
            blob = "\n".join(h for _, h in pages_for_wa)
        elif first.status in ("blocked", "disallowed"):
            status, has_site = "BLOCKED", True
            signals["notes"].append(first.reason)
        elif first.status == "timeout":
            status, has_site = "TIMEOUT", True
        else:
            status, has_site = "NO_WEBSITE", False
            signals["notes"].append(f"site unreachable ({first.reason})")

    if pages_for_wa and not wa:
        f = detect.extract_whatsapp(pages_for_wa, country)
        if f:
            wa = {"status": "CONFIRMED", **f}
            signals["whatsapp_evidence"] = {"rule": f["rule"], "matched": f["matched"], "source_url": f["source_url"]}
    if not wa:  # Rule 4: mobile number from discovery, no WhatsApp mention -> PROBABLE
        e, kind = normalize_phone(cand.get("phone"), country)
        if e and is_whatsapp_capable(kind):
            wa = {"status": "PROBABLE", "number": e, "source_url": None, "rule": "mobile-only"}

    wa_type, wa_conf, wa_ev = detect.classify_wa_type(wa, blob, signatures, fully)
    if wa_ev:
        signals["wa_type_evidence"] = wa_ev
    cb = detect.classify_chatbot(blob, signatures, fully)
    if cb[3]:
        signals["chatbot_evidence"] = cb[3]
    email = None
    m = EMAIL_RE.search(blob) if blob else None
    if m and not m.group().lower().endswith((".png", ".jpg", ".webp", ".svg")):
        email = m.group()[:120]
    return _result(status, has_site, site, wa, wa_type, wa_conf, cb, signals, cand.get("phone"), email)
