
from datetime import datetime, timezone

from .whatsapp_classifier import classify_whatsapp
from .chatbot_classifier import classify_chatbot
from .hot_lead_evaluator import is_hot_lead


def classify_lead(
    phone=None,
    whatsapp_evidence=None,
    website_html="",
    inspection_status="COMPLETE",
    source_url=None
):
    whatsapp_evidence = whatsapp_evidence or []

    # Classify WhatsApp
    whatsapp = classify_whatsapp(
        phone=phone,
        evidence=whatsapp_evidence
    )

    # Classify website chatbot
    chatbot = classify_chatbot(
        html_content=website_html,
        inspection_status=inspection_status
    )

    # Evaluate hot lead
    hot_lead = is_hot_lead(
        whatsapp["type"],
        chatbot["status"]
    )

    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "whatsapp": {
            "number_e164": whatsapp["number_e164"],
            "status": whatsapp["status"],
            "type": whatsapp["type"],
            "evidence": {
                "source_url": source_url,
                "matched_pattern": whatsapp.get("matched_pattern"),
                "confidence": None,
                "observation_timestamp": timestamp
            }
        },

        "chatbot": {
            "status": chatbot["status"],
            "vendor": chatbot["vendor"],
            "evidence": {
                "source_url": source_url,
                "matched_pattern": chatbot["matched_pattern"],
                "confidence": None,
                "observation_timestamp": timestamp
            }
        },

        "is_hot_lead": hot_lead
    }
