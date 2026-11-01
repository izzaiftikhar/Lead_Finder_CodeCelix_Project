
from app.domain.classification.phone_normalizer import normalize_phone
from app.domain.classification.whatsapp_classifier import classify_whatsapp
from app.domain.classification.chatbot_classifier import classify_chatbot
from app.domain.classification.hot_lead_evaluator import is_hot_lead


def test_valid_uae_mobile():
    result = normalize_phone("0501234567")
    assert result["status"] == "VALID"
    assert result["number_e164"] == "+971501234567"


def test_invalid_phone():
    result = normalize_phone("123")
    assert result["status"] == "INSUFFICIENT"


def test_confirmed_whatsapp():
    result = classify_whatsapp(
        phone="0501234567",
        evidence=["https://wa.me/971501234567"]
    )
    assert result["status"] == "CONFIRMED"


def test_probable_whatsapp():
    result = classify_whatsapp(phone="0501234567")
    assert result["status"] == "PROBABLE"


def test_intercom_chatbot():
    result = classify_chatbot(
        html_content="widget.intercom.io",
        inspection_status="COMPLETE"
    )
    assert result["status"] == "YES"
    assert result["vendor"] == "Intercom"


def test_chatbot_not_detected():
    result = classify_chatbot(
        html_content="<html><body>Business website</body></html>",
        inspection_status="COMPLETE"
    )
    assert result["status"] == "NO"


def test_blocked_website():
    result = classify_chatbot(
        html_content="",
        inspection_status="HTTP_403"
    )
    assert result["status"] == "UNKNOWN"


def test_timeout_website():
    result = classify_chatbot(
        html_content="",
        inspection_status="TIMEOUT"
    )
    assert result["status"] == "UNKNOWN"


def test_hot_lead():
    assert is_hot_lead("MANUAL", "NO") is True


def test_not_hot_automated():
    assert is_hot_lead("AUTOMATED", "NO") is False


def test_not_hot_unknown_chatbot():
    assert is_hot_lead("MANUAL", "UNKNOWN") is False

# Additional tests for the technical directive

def test_uae_landline_rejected():
    result = normalize_phone("04 123 4567")
    assert result["status"] == "INSUFFICIENT"


def test_arabic_whatsapp_keyword():
    result = classify_whatsapp(
        phone="0501234567",
        evidence=["واتساب 0501234567"]
    )
    assert result["status"] == "CONFIRMED"


def test_all_automation_providers():
    providers = [
        "wati.io",
        "interakt.shop",
        "aisensy.com",
        "gallabox.com",
        "respond.io",
        "botmaker.com"
    ]

    for provider in providers:
        result = classify_whatsapp(
            phone="0501234567",
            evidence=[
                "https://wa.me/971501234567",
                provider
            ]
        )
        assert result["type"] == "AUTOMATED", provider


def test_all_chatbot_vendors():
    vendors = [
        "widget.intercom.io",
        "code.tidio.co",
        "static.zdassets.com/ekr/snippet.js",
        "js.driftt.com",
        "client.crisp.chat",
        "cdn.livechatinc.com",
        "embed.tawk.to",
        "wchat.freshchat.com",
        "js.hs-scripts.com",
        "widget.manychat.com",
        "code.jivosite.com"
    ]

    for vendor in vendors:
        result = classify_chatbot(
            html_content=vendor,
            inspection_status="COMPLETE"
        )
        assert result["status"] == "YES", vendor


def test_floating_whatsapp_is_not_chatbot():
    result = classify_chatbot(
        html_content='<a href="https://wa.me/971501234567">WhatsApp</a>',
        inspection_status="COMPLETE"
    )
    assert result["status"] == "NO"


def test_http_500_returns_unknown():
    result = classify_chatbot(
        html_content="",
        inspection_status="HTTP_500"
    )
    assert result["status"] == "UNKNOWN"


def test_start_bot_parameter_is_automated():
    result = classify_whatsapp(
        phone="0501234567",
        evidence=[
            "https://wa.me/971501234567?text=START_BOT"
        ]
    )
    assert result["type"] == "AUTOMATED"

from app.domain.classification.lead_classifier import classify_lead


def test_complete_lead_classification():
    result = classify_lead(
        phone="0501234567",
        whatsapp_evidence=[
            "https://wa.me/971501234567"
        ],
        website_html="<html>Business website</html>",
        inspection_status="COMPLETE",
        source_url="https://example.com"
    )

    assert result["whatsapp"]["status"] == "CONFIRMED"
    assert result["whatsapp"]["type"] == "MANUAL"
    assert result["chatbot"]["status"] == "NO"
    assert result["is_hot_lead"] is True


def test_complete_pipeline_with_unknown_chatbot():
    result = classify_lead(
        phone="0501234567",
        whatsapp_evidence=[
            "https://wa.me/971501234567"
        ],
        website_html="",
        inspection_status="TIMEOUT"
    )

    assert result["chatbot"]["status"] == "UNKNOWN"
    assert result["is_hot_lead"] is False

def test_confirmed_only_does_not_change_classification():
    result = classify_whatsapp(
        phone="0501234567",
        evidence=[]
    )
    assert result["status"] == "PROBABLE"


def test_invalid_landline_cannot_be_confirmed():
    result = classify_whatsapp(
        phone="041234567",
        evidence=["https://wa.me/97141234567"]
    )
    assert result["status"] == "INSUFFICIENT"


def test_chatbot_unknown_on_failed_inspection():
    result = classify_chatbot(
        html_content="",
        inspection_status="FAILED"
    )
    assert result["status"] == "UNKNOWN"
