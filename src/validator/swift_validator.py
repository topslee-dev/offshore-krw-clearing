from src.parser.field_validator import FieldValidator, ValidationResult


class SWIFTValidator:
    def __init__(self):
        self._field_validator = FieldValidator()

    def _extract_block4(self, message: dict) -> dict:
        block4 = message.get("block4", {})
        if not isinstance(block4, dict):
            return {}
        return block4

    def validate_mt103(self, message: dict) -> ValidationResult:
        block4 = message.get("block4", {})
        if not isinstance(block4, dict):
            return ValidationResult(is_valid=False, errors=["block4 must be a dict of {tag: value}"], warnings=[])
        return self._field_validator.validate_mt103(block4)

    def validate_mt202(self, message: dict) -> ValidationResult:
        block4 = self._extract_block4(message)
        return self._field_validator.validate_mt202(block4)

    def validate_mt900(self, message: dict) -> ValidationResult:
        block4 = self._extract_block4(message)
        return self._field_validator.validate_mt900(block4)

    def validate_mt910(self, message: dict) -> ValidationResult:
        block4 = self._extract_block4(message)
        return self._field_validator.validate_mt910(block4)

    def validate_mt940(self, message: dict) -> ValidationResult:
        block4 = self._extract_block4(message)
        return self._field_validator.validate_mt940(block4)

    def validate_mt950(self, message: dict) -> ValidationResult:
        block4 = self._extract_block4(message)
        return self._field_validator.validate_mt950(block4)

    def validate_field(self, tag: str, value: str) -> bool:
        result = self._field_validator.validate(tag, value)
        return result.is_valid
