"""Starter catalog. Matrix and keywords follow the build spec. Cities are a curated starter list;
run scripts/load_geonames.py with cities15000.txt for the full catalog (GeoNames, CC-BY 4.0)."""

COUNTRIES = {"AE": "UAE", "SA": "Saudi Arabia", "QA": "Qatar", "KW": "Kuwait", "BH": "Bahrain", "GB": "UK", "US": "USA"}
GULF = {"AE", "SA", "QA", "KW", "BH"}
NICHES = {"REAL_ESTATE": "Real Estate", "CLINICS": "Clinics", "B2B_AGENCIES": "B2B Agencies", "SAAS": "SaaS"}

MATRIX = {
    "AE": ["REAL_ESTATE", "CLINICS"], "SA": ["REAL_ESTATE", "CLINICS"], "QA": ["REAL_ESTATE", "CLINICS"],
    "KW": ["REAL_ESTATE", "CLINICS"], "BH": ["REAL_ESTATE", "CLINICS"],
    "GB": ["CLINICS", "B2B_AGENCIES", "SAAS"], "US": ["REAL_ESTATE", "CLINICS", "B2B_AGENCIES", "SAAS"],
}

KEYWORDS = {
    ("REAL_ESTATE", "ANY", "en"): ["real estate agency", "property broker", "estate agent", "property management"],
    ("REAL_ESTATE", "GULF", "ar"): ["وكالة عقارية", "عقارات", "وسيط عقاري"],
    ("CLINICS", "ANY", "en"): ["clinic", "dental clinic", "medical center", "dermatology clinic", "polyclinic"],
    ("CLINICS", "GULF", "ar"): ["عيادة", "مركز طبي", "عيادة أسنان"],
    ("B2B_AGENCIES", "ANY", "en"): ["digital marketing agency", "web development agency", "branding agency", "software consultancy"],
    ("SAAS", "ANY", "en"): ["SaaS company", "B2B software company", "software platform"],
}

CITIES = {
    "AE": {"Dubai": ["Dubai"], "Abu Dhabi": ["Abu Dhabi", "Al Ain"], "Sharjah": ["Sharjah"], "Ajman": ["Ajman"],
           "Ras Al Khaimah": ["Ras Al Khaimah"], "Fujairah": ["Fujairah"], "Umm Al Quwain": ["Umm Al Quwain"]},
    "SA": {"Riyadh": ["Riyadh"], "Makkah": ["Jeddah", "Mecca", "Taif"], "Madinah": ["Medina"],
           "Eastern Province": ["Dammam", "Khobar", "Dhahran", "Jubail", "Hofuf"], "Asir": ["Abha"],
           "Tabuk": ["Tabuk"], "Qassim": ["Buraidah"], "Hail": ["Hail"]},
    "QA": {"Doha": ["Doha"], "Al Rayyan": ["Al Rayyan"], "Al Wakrah": ["Al Wakrah"], "Al Khor": ["Al Khor"], "Umm Salal": ["Umm Salal"]},
    "KW": {"Capital": ["Kuwait City"], "Hawalli": ["Hawalli", "Salmiya"], "Farwaniya": ["Farwaniya"], "Jahra": ["Jahra"], "Ahmadi": ["Ahmadi"]},
    "BH": {"Capital": ["Manama"], "Southern": ["Riffa", "Isa Town", "Sitra"], "Muharraq": ["Muharraq"], "Northern": ["Hamad Town"]},
    "GB": {"England": ["London", "Manchester", "Birmingham", "Leeds", "Liverpool", "Bristol", "Sheffield", "Newcastle upon Tyne",
                       "Nottingham", "Leicester", "Southampton", "Brighton"],
           "Scotland": ["Glasgow", "Edinburgh", "Aberdeen"], "Wales": ["Cardiff", "Swansea"], "Northern Ireland": ["Belfast"]},
    "US": {"New York": ["New York"], "California": ["Los Angeles", "San Diego", "San Jose", "San Francisco", "Sacramento"],
           "Texas": ["Houston", "Dallas", "Austin", "San Antonio"], "Florida": ["Miami", "Orlando", "Tampa", "Jacksonville"],
           "Illinois": ["Chicago"], "Arizona": ["Phoenix"], "Pennsylvania": ["Philadelphia"], "Washington": ["Seattle"],
           "Massachusetts": ["Boston"], "Georgia": ["Atlanta"], "Colorado": ["Denver"], "Nevada": ["Las Vegas"],
           "District of Columbia": ["Washington"], "Michigan": ["Detroit"], "Minnesota": ["Minneapolis"],
           "North Carolina": ["Charlotte"], "Tennessee": ["Nashville"], "Oregon": ["Portland"], "Ohio": ["Columbus"],
           "Missouri": ["Kansas City"]},
}

# (vendor, kind, scope, patterns). Patterns are lowercase substrings matched against page source. Admin-editable in DB.
SIGNATURES = [
    ("Intercom", "LIVE_CHAT", "chatbot", ["widget.intercom.io", "js.intercomcdn.com", "intercom-container"]),
    ("Drift", "LIVE_CHAT", "chatbot", ["js.driftt.com", "drift-frame"]),
    ("Crisp", "LIVE_CHAT", "chatbot", ["client.crisp.chat", "$crisp"]),
    ("Tawk.to", "LIVE_CHAT", "chatbot", ["embed.tawk.to", "tawk_api"]),
    ("Tidio", "LIVE_CHAT", "chatbot", ["code.tidio.co", "tidiochatapi", "tidio-chat"]),
    ("LiveChat", "LIVE_CHAT", "chatbot", ["cdn.livechatinc.com", "__lc.license"]),
    ("Zendesk", "LIVE_CHAT", "chatbot", ["static.zdassets.com", "ekr/snippet.js", "zopim"]),
    ("Freshchat", "LIVE_CHAT", "chatbot", ["wchat.freshchat.com", "fcwidget"]),
    ("HubSpot Conversations", "LIVE_CHAT", "chatbot", ["js.usemessages.com", "hubspotconversations"]),
    ("Olark", "LIVE_CHAT", "chatbot", ["static.olark.com", "olark.identify"]),
    ("Zoho SalesIQ", "LIVE_CHAT", "chatbot", ["salesiq.zoho", "zsiqchat"]),
    ("JivoChat", "LIVE_CHAT", "chatbot", ["code.jivosite.com", "jivo_api"]),
    ("Smartsupp", "LIVE_CHAT", "chatbot", ["smartsuppchat.com", "_smartsupp"]),
    ("Userlike", "LIVE_CHAT", "chatbot", ["userlike-cdn-widgets", "userlike.com/widget"]),
    ("LiveAgent", "LIVE_CHAT", "chatbot", [".ladesk.com"]),
    ("Chatbase", "AI_BOT", "chatbot", ["chatbase.co/embed", "chatbase.co/chatbot-iframe"]),
    ("Botpress", "AI_BOT", "chatbot", ["cdn.botpress.cloud", "botpress.cloud"]),
    ("Landbot", "AI_BOT", "chatbot", ["cdn.landbot.io", "landbot.io/"]),
    ("Voiceflow", "AI_BOT", "chatbot", ["cdn.voiceflow.com"]),
    ("Dialogflow Messenger", "AI_BOT", "chatbot", ["df-messenger"]),
    ("Kommunicate", "AI_BOT", "chatbot", ["widget.kommunicate.io"]),
    ("Ada", "AI_BOT", "chatbot", ["static.ada.support", "ada-embed"]),
    ("Podium", "LIVE_CHAT", "chatbot", ["connect.podium.com"]),
    ("WATI", "AI_BOT", "whatsapp", ["wati.io"]), ("Respond.io", "AI_BOT", "whatsapp", ["respond.io"]),
    ("Interakt", "AI_BOT", "whatsapp", ["interakt.shop", "interakt.ai"]), ("AiSensy", "AI_BOT", "whatsapp", ["aisensy.com"]),
    ("Gupshup", "AI_BOT", "whatsapp", ["gupshup.io"]), ("Twilio", "AI_BOT", "whatsapp", ["sdk.twilio.com", "twiliocdn.com"]),
    ("360dialog", "AI_BOT", "whatsapp", ["360dialog.io"]), ("Landbot", "AI_BOT", "whatsapp", ["landbot.io"]),
    ("ManyChat", "AI_BOT", "whatsapp", ["manychat.com"]), ("Botpress", "AI_BOT", "whatsapp", ["botpress.cloud"]),
    ("Chatfuel", "AI_BOT", "whatsapp", ["chatfuel.com"]), ("SleekFlow", "AI_BOT", "whatsapp", ["sleekflow.io"]),
    ("Zoko", "AI_BOT", "whatsapp", ["zoko.io"]), ("Trengo", "AI_BOT", "whatsapp", ["trengo.com"]),
    ("Kommunicate", "AI_BOT", "whatsapp", ["kommunicate.io"]),
]
