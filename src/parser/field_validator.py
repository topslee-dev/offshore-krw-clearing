import re
from dataclasses import dataclass


ISO4217_CURRENCIES = {
    "KRW", "USD", "EUR", "JPY", "CNY", "CNH", "GBP", "CHF", "CAD", "AUD",
    "NZD", "SGD", "HKD", "SEK", "NOK", "DKK", "INR", "BRL", "MXN", "ZAR",
    "RUB", "TRY", "THB", "IDR", "MYR", "PHP", "VND", "TWD", "SAR", "AED",
    "PLN", "CZK", "HUF", "ILS", "CLP", "COP", "ARS", "PEN", "NGN", "KES",
}


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]


class FieldValidator:
    RULES = {
        ":20:": {"max_len": 16, "pattern": r"[A-Z0-9/\-]{1,16}"},
        ":21:": {"max_len": 16, "pattern": r"[A-Z0-9/\-]{1,16}"},
        ":23B:": {"values": ["CRED", "SPRI", "RETN"]},
        ":32A:": {"format": "YYMMDD+CURRENCY+AMOUNT"},
        ":33B:": {"format": "YYMMDD+CURRENCY+AMOUNT"},
        ":50K:": {"max_len": 35, "pattern": r"/[A-Z0-9]+.*"},
        ":50F:": {"max_len": 35, "pattern": r"/[A-Z0-9]+.*"},
        ":59:": {"max_len": 35, "pattern": r"/[A-Z0-9]+.*"},
        ":70:": {"max_len": 140, "pattern": r".*"},
        ":71A:": {"values": ["BEN", "OUR", "SHA"]},
        ":52A:": {"pattern": r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"},
        ":57A:": {"pattern": r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"},
        ":58A:": {"pattern": r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"},
        ":25:": {"pattern": r"[A-Z0-9\-]{1,35}"},
        ":28C:": {"pattern": r"\d+/[A-Z0-9]+"},
        ":60F:": {"pattern": r"[CD]\d{6}[A-Z]{3}\d+"},
        ":62F:": {"pattern": r"[CD]\d{6}[A-Z]{3}\d+"},
        ":61:": {"pattern": r"\d{6}\d{4}[CD]\d+"},
    }

    REQUIRED = {
        "MT103": [":20:", ":23B:", ":32A:", ":50K:/:50F:", ":59:"],
        "MT202": [":20:", ":21:", ":32A:", ":52A:", ":58A:"],
        "MT900": [":20:", ":21:", ":25:", ":32A:"],
        "MT910": [":20:", ":21:", ":25:", ":32A:"],
        "MT940": [":20:", ":25:", ":28C:", ":60F:", ":62F:"],
        "MT950": [":20:", ":25:", ":28C:", ":60F:", ":62F:"],
    }

    def validate(self, tag: str, value: str) -> ValidationResult:
        errors = []
        warnings = []

        rule = self.RULES.get(tag)
        if rule is None:
            warnings.append(f"No validation rule defined for tag {tag}")
            return ValidationResult(is_valid=True, errors=[], warnings=warnings)

        if "max_len" in rule and len(value) > rule["max_len"]:
            errors.append(
                f"{tag} exceeds max length {rule['max_len']} (got {len(value)})"
            )

        if "pattern" in rule:
            if not re.match(rule["pattern"], value.strip()):
                errors.append(f"{tag} value '{value}' does not match pattern {rule['pattern']}")

        if "values" in rule and value.strip() not in rule["values"]:
            errors.append(
                f"{tag} value '{value}' is not valid. Allowed: {rule['values']}"
            )

        if "format" in rule:
            format_errors = self._validate_format(tag, value, rule["format"])
            errors.extend(format_errors)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_mt103(self, message: dict) -> ValidationResult:
        return self._validate_message(message, "MT103")

    def validate_mt202(self, message: dict) -> ValidationResult:
        return self._validate_message(message, "MT202")

    def validate_mt900(self, message: dict) -> ValidationResult:
        return self._validate_message(message, "MT900")

    def validate_mt910(self, message: dict) -> ValidationResult:
        return self._validate_message(message, "MT910")

    def validate_mt940(self, message: dict) -> ValidationResult:
        return self._validate_message(message, "MT940")

    def validate_mt950(self, message: dict) -> ValidationResult:
        return self._validate_message(message, "MT950")

    def _validate_message(self, message: dict, mt_type: str) -> ValidationResult:
        errors = []
        warnings = []

        required_fields = self.REQUIRED.get(mt_type, [])

        for tag in required_fields:
            if "/" in tag:
                alt1, alt2 = tag.split("/")
                alt1_full = f":{alt1.strip(':')}:"
                alt2_full = f":{alt2.strip(':')}:"
                if alt1_full not in message and alt2_full not in message:
                    errors.append(f"Required field {alt1_full} or {alt2_full} missing")
            else:
                if tag not in message:
                    errors.append(f"Required field {tag} missing")

        for tag, value in message.items():
            result = self.validate(tag, value)
            errors.extend(result.errors)
            warnings.extend(result.warnings)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _validate_format(self, tag: str, value: str, fmt: str) -> list[str]:
        errors = []
        if fmt == "YYMMDD+CURRENCY+AMOUNT":
            match = re.match(r"^(\d{6})([A-Z]{3})(\d+(?:,\d{0,2})?)$", value.strip())
            if not match:
                errors.append(f"{tag} format should be YYMMDD+CURRENCY+AMOUNT (got '{value}')")
            else:
                currency = match.group(2)
                if currency not in ISO4217_CURRENCIES:
                    errors.append(
                        f"{tag} currency '{currency}' is not a valid ISO 4217 code"
                    )
        return errors
