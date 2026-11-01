
import re
from urllib.parse import unquote_plus, urlparse, parse_qs

from .phone_normalizer import normalize_phone


AUTOMATION_DOMAINS = [
    "wati.io",
    "interakt.shop",
    "aisensy.com",
    "gallabox.com",
    "respond.io",
    "botmaker.com"
]


def find_whatsapp_number(evidence):
    for item in evidence:
        text = unquote_plus(str(item))

        patterns = [
            r"wa\.me/(\+?\d+)",
            r"api\.whatsapp\.com/send\?[^ ]*phone=(\+?\d+)",
            r"whatsapp://send\?[^ ]*phone=(\+?\d+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # Also support phone parameters parsed from URLs.
        try:
            parsed = urlparse(text)
            params = parse_qs(parsed.query)
            if params.get("phone"):
                return params["phone"][0]
        except ValueError:
            pass

    return None


def find_keyword_evidence(evidence, normalized_phone):
    keywords = ["WhatsApp", "واتساب"]

    for item in evidence:
        text = str(item)

        for match in re.finditer(
            r"\+?\d[\d\s().-]{5,}\d",
            text
        ):
            candidate = normalize_phone(match.group())

            if candidate["number_e164"] != normalized_phone:
                continue

            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            nearby_text = text[start:end]

            for keyword in keywords:
                if re.search(
                    re.escape(keyword),
                    nearby_text,
                    re.IGNORECASE
                ):
                    return f"Keyword '{keyword}' near verified phone number"

    return None


def classify_whatsapp(phone=None, evidence=None):
    evidence = evidence or []

    linked_number = find_whatsapp_number(evidence)
    candidate = linked_number or phone

    normalized = normalize_phone(candidate)

    if normalized["status"] == "INSUFFICIENT":
        return {
            "number_e164": normalized["number_e164"],
            "status": "INSUFFICIENT",
            "type": "UNKNOWN",
            "matched_pattern": None,
            "evidence": evidence
        }

    evidence_text = " ".join(
        unquote_plus(str(item)) for item in evidence
    )

    matched_pattern = None

    # Check direct WhatsApp links.
    link_patterns = [
        r"wa\.me/\+?\d+",
        r"api\.whatsapp\.com/send",
        r"whatsapp://send"
    ]

    for pattern in link_patterns:
        match = re.search(pattern, evidence_text, re.IGNORECASE)
        if match:
            matched_pattern = match.group()
            break

    # Check WhatsApp keywords near the verified phone number.
    if not matched_pattern:
        matched_pattern = find_keyword_evidence(
            evidence,
            normalized["number_e164"]
        )

    status = "CONFIRMED" if matched_pattern else "PROBABLE"

    # Detect approved WhatsApp automation providers.
    automated = any(
        domain in evidence_text.lower()
        for domain in AUTOMATION_DOMAINS
    )

    if re.search(
        r"[?&]text=START_BOT(?:&|$)",
        evidence_text,
        re.IGNORECASE
    ):
        automated = True

    if status == "CONFIRMED":
        whatsapp_type = "AUTOMATED" if automated else "MANUAL"
    else:
        whatsapp_type = "UNKNOWN"

    return {
        "number_e164": normalized["number_e164"],
        "status": status,
        "type": whatsapp_type,
        "matched_pattern": matched_pattern,
        "evidence": evidence
    }
