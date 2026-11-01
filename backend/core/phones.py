"""Phone normalization to E.164 with country hints (rule-based; no libphonenumber dependency)."""
import re

CC = {"AE": "971", "SA": "966", "QA": "974", "KW": "965", "BH": "973", "GB": "44", "US": "1"}
# national-number patterns: (mobile, landline)
RULES = {
    "971": (r"5\d{8}", r"[2-4679]\d{7}"),
    "966": (r"5\d{8}", r"1[1-7]\d{7}"),
    "974": (r"[3567]\d{7}", r"4\d{7}"),
    "965": (r"[569]\d{7}", r"2\d{7}"),
    "973": (r"[36]\d{7}", r"[17]\d{7}"),
    "44": (r"7[1-57-9]\d{8}", r"[123]\d{8,9}"),
    "1": (r"[2-9]\d{2}[2-9]\d{6}", None),   # US/CA: line type indistinguishable
}


def normalize_phone(raw, country="AE"):
    """Returns (e164 | None, kind) where kind in mobile | landline | mobile_or_fixed | invalid."""
    if not raw:
        return None, "invalid"
    s = re.sub(r"[^\d+]", "", str(raw))
    digits = s[1:] if s.startswith("+") else (s[2:] if s.startswith("00") else None)
    if digits is None:  # national format
        cc = CC.get(country)
        if not cc:
            return None, "invalid"
        digits = cc + (s[1:] if s.startswith("0") and cc != "1" else s.lstrip("0") if cc != "1" else s)
        if cc == "1" and s.startswith("1") and len(s) == 11:
            digits = s
    for cc in sorted(RULES, key=len, reverse=True):
        if digits.startswith(cc):
            nat = digits[len(cc):]
            mob, land = RULES[cc]
            if re.fullmatch(mob, nat):
                return "+" + cc + nat, ("mobile_or_fixed" if cc == "1" else "mobile")
            if land and re.fullmatch(land, nat):
                return "+" + cc + nat, "landline"
            return None, "invalid"
    return None, "invalid"


def is_whatsapp_capable(kind):
    return kind in ("mobile", "mobile_or_fixed")
