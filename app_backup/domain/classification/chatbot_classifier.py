
CHATBOT_VENDORS = {
    "Intercom": [
        "widget.intercom.io",
        "window.intercom",
        "#intercom-container"
    ],
    "Tidio": [
        "code.tidio.co",
        "window.tidioChatApi",
        "#tidio-chat"
    ],
    "Zendesk": [
        "static.zdassets.com/ekr/snippet.js",
        "window.zE",
        "#launcher"
    ],
    "Drift": [
        "js.driftt.com",
        "window.drift",
        "#drift-widget"
    ],
    "Crisp": [
        "client.crisp.chat",
        "window.$crisp"
    ],
    "LiveChat": [
        "cdn.livechatinc.com",
        "window.__lc"
    ],
    "Tawk.to": [
        "embed.tawk.to",
        "window.Tawk_API"
    ],
    "Freshchat": [
        "wchat.freshchat.com",
        "window.fcWidget"
    ],
    "HubSpot Chat": [
        "js.hs-scripts.com",
        "window.HubSpotConversations"
    ],
    "ManyChat": [
        "widget.manychat.com",
        "manychat.com"
    ],
    "JivoChat": [
        "code.jivosite.com",
        "window.jivo_api"
    ]
}


def classify_chatbot(html_content="", inspection_status="COMPLETE"):
    """
    Detect recognized website chatbot vendors.

    YES     = Recognized chatbot signature found.
    NO      = Inspection completed with no recognized signature.
    UNKNOWN = Inspection failed or was incomplete.
    """

    status = str(inspection_status).upper()

    # Never classify a failed or incomplete inspection as NO.
    if status != "COMPLETE":
        return {
            "status": "UNKNOWN",
            "vendor": None,
            "matched_pattern": None
        }

    content = str(html_content).lower()

    # Search for all recognized chatbot vendors.
    for vendor, patterns in CHATBOT_VENDORS.items():
        for pattern in patterns:
            if pattern.lower() in content:
                return {
                    "status": "YES",
                    "vendor": vendor,
                    "matched_pattern": pattern
                }

    # Inspection succeeded, but no chatbot was detected.
    return {
        "status": "NO",
        "vendor": None,
        "matched_pattern": None
    }
