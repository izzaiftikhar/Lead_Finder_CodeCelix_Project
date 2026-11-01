
import phonenumbers
from phonenumbers import PhoneNumberFormat, PhoneNumberType


def normalize_phone(phone, default_region="AE"):
    if not phone:
        return {
            "number_e164": None,
            "status": "INSUFFICIENT",
            "reason": "Phone number is missing"
        }

    try:
        parsed = phonenumbers.parse(phone, default_region)

        if not phonenumbers.is_valid_number(parsed):
            return {
                "number_e164": None,
                "status": "INSUFFICIENT",
                "reason": "Invalid phone number"
            }

        number_type = phonenumbers.number_type(parsed)

        if number_type not in (
            PhoneNumberType.MOBILE,
            PhoneNumberType.FIXED_LINE_OR_MOBILE
        ):
            return {
                "number_e164": phonenumbers.format_number(
                    parsed, PhoneNumberFormat.E164
                ),
                "status": "INSUFFICIENT",
                "reason": "Landline or unsupported number type"
            }

        return {
            "number_e164": phonenumbers.format_number(
                parsed, PhoneNumberFormat.E164
            ),
            "status": "VALID",
            "reason": "Valid mobile number"
        }

    except phonenumbers.NumberParseException:
        return {
            "number_e164": None,
            "status": "INSUFFICIENT",
            "reason": "Phone number could not be parsed"
        }
