"""Rule-based, evidence-based classification. No LLM. Pure functions, stdlib only."""
import re
from urllib.parse import unquote_plus

WA_LINK = re.compile(r"(?:wa\.me/|api\.whatsapp\.com/send\?[^\s\"'<>]*?phone=|whatsapp://send\?[^\s\"'<>]*?phone=|web\.whatsapp\.com/send\?[^\s\"'<>]*?phone=)\+?(\d{7,15})", re.I)

CHATBOT_VENDORS = {
    "Intercom": ["widget.intercom.io", "window.intercom", "intercom-container"],
    "Tidio": ["code.tidio.co", "tidiochatapi"],
    "Zendesk": ["static.zdassets.com", "zopim"],
    "Drift": ["js.driftt.com", "drift-widget"],
    "Crisp": ["client.crisp.chat", "window.$crisp"],
    "LiveChat": ["cdn.livechatinc.com", "window.__lc"],
    "Tawk.to": ["embed.tawk.to", "tawk_api"],
    "Freshchat": ["wchat.freshchat.com", "fcwidget"],
    "HubSpot Chat": ["js.usemessages.com", "hubspotconversations"],
    "ManyChat": ["widget.manychat.com"],
    "JivoChat": ["code.jivosite.com", "jivo_api"],
    "Chatbase": ["chatbase.co/embed", "chatbase.co/chatbot-iframe"],
    "Botpress": ["cdn.botpress.cloud"],
    "Landbot": ["cdn.landbot.io", "landbot.io"],
    "Voiceflow": ["cdn.voiceflow.com"],
}
WA_AUTOMATION = ["wati.io", "interakt.shop", "aisensy.com", "gallabox.com", "respond.io", "botmaker.com", "start_bot"]

WA_STATES = ("CONFIRMED", "PROBABLE", "UNKNOWN", "NOT_DETECTED")
CHATBOT_STATES = ("DETECTED", "NOT_DETECTED", "UNKNOWN", "UNREACHABLE")


def normalize_phone(raw):
    """Normalize UAE-style numbers to E.164. Returns (e164|None, kind) kind: mobile|landline|invalid."""
    if not raw:
        return None, "invalid"
    d = re.sub(r"[^\d+]", "", str(raw))
    if d.startswith("+"):
        d = d[1:]
    elif d.startswith("00"):
        d = d[2:]
    elif d.startswith("0"):
        d = "971" + d[1:]
    if not d.startswith("971"):
        return ("+" + d if 8 <= len(d) <= 15 else None), ("invalid" if not 8 <= len(d) <= 15 else "foreign")
    n = d[3:]
    if re.fullmatch(r"5\d{8}", n):
        return "+971" + n, "mobile"
    if re.fullmatch(r"[2-4679]\d{7}", n):
        return "+971" + n, "landline"
    return None, "invalid"


def classify_whatsapp(phone, evidence_texts, source_url=None):
    """evidence_texts: strings from provider data / website HTML. Returns dict with state, number, reason, matched."""
    blob = " ".join(unquote_plus(str(t)) for t in (evidence_texts or []))
    m = WA_LINK.search(blob)
    if m:
        e164, kind = normalize_phone(m.group(1))
        if e164:
            return {"state": "CONFIRMED", "number": e164, "matched": m.group(0)[:120], "source_url": source_url,
                    "reason": "Direct WhatsApp link found on the business's own page."}
    e164, kind = normalize_phone(phone)
    if e164 and kind == "mobile":
        return {"state": "PROBABLE", "number": e164, "matched": None, "source_url": None,
                "reason": "Valid UAE mobile number listed, but no WhatsApp link was found to confirm it."}
    if not phone and not m:
        return {"state": "UNKNOWN", "number": None, "matched": None, "source_url": None,
                "reason": "No phone number or WhatsApp link available."}
    return {"state": "NOT_DETECTED", "number": e164, "matched": None, "source_url": None,
            "reason": f"Listed number is not a mobile ({kind}) and no WhatsApp link was found."}


def classify_chatbot(html, fetch_status, source_url=None):
    """fetch_status: 'ok' | 'no_website' | 'failed'."""
    if fetch_status == "no_website":
        return {"state": "UNKNOWN", "vendor": None, "matched": None, "source_url": None,
                "reason": "No website to inspect."}
    if fetch_status != "ok":
        return {"state": "UNREACHABLE", "vendor": None, "matched": None, "source_url": source_url,
                "reason": "Website could not be fetched; chatbot status cannot be determined."}
    low = (html or "").lower()
    for vendor, pats in CHATBOT_VENDORS.items():
        for p in pats:
            if p in low:
                return {"state": "DETECTED", "vendor": vendor, "matched": p, "source_url": source_url,
                        "reason": f"{vendor} signature '{p}' found in page source."}
    for p in WA_AUTOMATION:
        if p in low:
            return {"state": "DETECTED", "vendor": "WhatsApp automation", "matched": p, "source_url": source_url,
                    "reason": f"WhatsApp automation signature '{p}' found."}
    return {"state": "NOT_DETECTED", "vendor": None, "matched": None, "source_url": source_url,
            "reason": "Homepage fetched; no known chatbot signature in static HTML. Widgets injected only via "
                      "late JavaScript or on other pages may be missed."}


def is_hot_lead(wa_state, chatbot_state):
    return wa_state == "CONFIRMED" and chatbot_state == "NOT_DETECTED"


def score(wa_state, chatbot_state, has_website, has_phone):
    s = {"CONFIRMED": 55, "PROBABLE": 30, "UNKNOWN": 5, "NOT_DETECTED": 0}[wa_state]
    s += {"NOT_DETECTED": 35, "UNKNOWN": 10, "UNREACHABLE": 8, "DETECTED": 0}[chatbot_state]
    s += 5 if has_website else 0
    s += 5 if has_phone else 0
    return min(s, 100)


def classify_lead(phone, website, html, fetch_status, evidence_texts=(), source_url=None):
    wa = classify_whatsapp(phone, [*evidence_texts, html or ""], source_url)
    cb = classify_chatbot(html, fetch_status, source_url)
    return {"whatsapp": wa, "chatbot": cb, "hot": is_hot_lead(wa["state"], cb["state"]),
            "score": score(wa["state"], cb["state"], bool(website), bool(phone))}
