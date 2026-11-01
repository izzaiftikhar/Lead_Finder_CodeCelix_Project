"""Fictional demo records (not real businesses). Only used in demo mode."""
from .classify import is_hot_lead, score

RAW = [('Palm Gate Realty', 'Dubai', 'Real Estate', 'https://palmgaterealty.example', '+971 50 123 4567', 'Confirmed (demo)', 'MANUAL', 'NO', 92, 'WhatsApp contact link shown; no chatbot signal in sample notes.'), ('Crescent Keys Properties', 'Abu Dhabi', 'Real Estate', 'https://crescentkeys.example', '+971 2 555 0182', 'Probable (demo)', 'UNKNOWN', 'UNKNOWN', 68, 'Mobile contact listed; WhatsApp link not independently verified.'), ('Harborline Medical Centre', 'Sharjah', 'Clinics', 'https://harborlineclinic.example', '+971 6 555 0144', 'Confirmed (demo)', 'MANUAL', 'NO', 89, 'WhatsApp contact listed; sample inspection found no chatbot signal.'), ('Oasis Family Clinic', 'Dubai', 'Clinics', 'https://oasisfamilyclinic.example', '+971 55 555 0119', 'Confirmed (demo)', 'AUTOMATED', 'YES', 55, 'Sample notes indicate a chat widget and automated WhatsApp greeting.'), ('Dune & Door Realty', 'Ajman', 'Real Estate', '', '+971 50 555 0190', 'Probable (demo)', 'UNKNOWN', 'UNKNOWN', 61, 'Website and automation need real-world verification.'), ('Blue Pearl Dermatology', 'Abu Dhabi', 'Clinics', 'https://bluepearlderm.example', '+971 50 555 0121', 'Confirmed (demo)', 'MANUAL', 'NO', 86, 'Contact link and website status are illustrative only.'), ('Skyline Nest Properties', 'Dubai', 'Real Estate', 'https://skylinenest.example', '+971 4 555 0170', 'Confirmed (demo)', 'AUTOMATED', 'YES', 58, 'Sample notes indicate a chatbot signature.'), ('Marina View Health Clinic', 'Ras Al Khaimah', 'Clinics', 'https://marinaviewhealth.example', '+971 7 555 0166', 'Confirmed (demo)', 'MANUAL', 'NO', 84, 'Sample contact and chatbot findings are not verified.'), ('Cedar Stone Real Estate', 'Sharjah', 'Real Estate', 'https://cedarstone.example', '+971 50 555 0133', 'Probable (demo)', 'UNKNOWN', 'NO', 73, 'WhatsApp status is probable; chatbot absence is illustrative.'), ('Nour Family Healthcare', 'Fujairah', 'Clinics', '', '+971 50 555 0155', 'Confirmed (demo)', 'MANUAL', 'UNKNOWN', 77, 'No website is listed in this sample record.'), ('Golden Sand Properties', 'Dubai', 'Real Estate', 'https://goldensands.example', '+971 50 555 0101', 'Confirmed (demo)', 'MANUAL', 'NO', 95, 'Illustrative high-priority lead.'), ('Cove Medical & Wellness', 'Abu Dhabi', 'Clinics', 'https://covemedical.example', '+971 2 555 0199', 'Probable (demo)', 'UNKNOWN', 'UNKNOWN', 64, 'Sample needs manual validation before outreach.')]

WA = {"Confirmed": "CONFIRMED", "Probable": "PROBABLE"}
CB = {"NO": "NOT_DETECTED", "YES": "DETECTED", "UNKNOWN": "UNKNOWN"}

def demo_records():
    out = []
    for i, (name, city, niche, site, phone, wa, auto, chat, _s, ev) in enumerate(RAW):
        w = WA[wa.split(" ")[0]]; c = CB[chat]
        out.append({"dedupe_key": f"demo:{i}", "business_name": name, "country": "UAE", "city": city, "niche": niche,
          "website": site or None, "phone": phone, "whatsapp_number": None, "whatsapp_state": w, "chatbot_state": c,
          "chatbot_vendor": None, "is_hot": 1 if is_hot_lead(w, c) else 0, "lead_score": score(w, c, bool(site), True),
          "evidence": "[DEMO DATA - fictional] " + ev, "source": "demo", "is_demo": 1})
    return out
