
def is_hot_lead(whatsapp_type, chatbot_status):
    """
    A hot lead must have:
    1. MANUAL WhatsApp
    2. No website chatbot
    """

    return (
        whatsapp_type == "MANUAL"
        and chatbot_status == "NO"
    )
