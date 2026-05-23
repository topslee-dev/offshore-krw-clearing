from src.parser.field_validator import FieldValidator, ValidationResult


class SWIFTValidator:
    """
    SWIFT MT 메시지 전체에 대한 검증을 수행한다.
    내부적으로 FieldValidator를 사용하여 개별 태그를 검증한다.

    사용 예:
        validator = SWIFTValidator()
        result = validator.validate_mt103({":20:": "REF-001", ":23B:": "CRED", ...})
        ok = validator.validate_field(":20:", "SENDER-REF-001")
    """

    def __init__(self):
        self._field_validator = FieldValidator()

    def validate_mt103(self, message: dict) -> ValidationResult:
        """
        MT103 메시지 구조의 유효성을 검증한다.
        block4 아래의 태그들을 추출하여 필드 검증을 수행한다.

        Args:
            message: dict — block1, block2, block4 키를 가진 딕셔너리.
                     block4의 값은 {태그: 값} 형태의 dict여야 한다.

        Returns:
            ValidationResult — 검증 결과
        """
        block4 = message.get("block4", {})
        if not isinstance(block4, dict):
            return ValidationResult(
                is_valid=False,
                errors=["block4 must be a dict of {tag: value}"],
                warnings=[],
            )

        return self._field_validator.validate_mt103(block4)

    def validate_field(self, tag: str, value: str) -> bool:
        """
        단일 태그의 값을 검증한다.

        Args:
            tag:   태그 이름 (예: ":20:", ":32A:")
            value: 태그 값

        Returns:
            bool — 유효하면 True
        """
        result = self._field_validator.validate(tag, value)
        return result.is_valid
