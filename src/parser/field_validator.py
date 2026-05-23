import re
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """
    필드 검증 결과를 저장하는 데이터 클래스.

    Attributes:
        is_valid: 검증 통과 여부 (True=통과, False=오류 있음)
        errors:   검증 실패한 오류 메시지 목록
        warnings: 심각하지 않은 경고 메시지 목록 (예: 미등록 태그)
    """
    is_valid: bool
    errors: list[str]
    warnings: list[str]


class FieldValidator:
    """
    SWIFT MT 태그별 필드 값을 검증한다.
    각 태그에 대해 최대 길이, 정규식 패턴, 허용 값, 포맷 등을 정의하고 검사한다.
    또한 MT103 메시지 전체에 대한 필수 필드 존재 여부도 검증한다.

    사용 예:
        validator = FieldValidator()
        result = validator.validate(":20:", "SENDER-REF-001")
        mt103_result = validator.validate_mt103({":20:": "REF", ":23B:": "CRED", ...})
    """

    # 태그별 검증 규칙 정의
    # 각 규칙은 다음 키를 가질 수 있음:
    #   max_len: 최대 길이
    #   pattern: 허용되는 정규식 패턴
    #   values: 허용되는 값 목록
    #   format: 특수 포맷 검증 (예: YYMMDD+통화+금액)
    RULES = {
        # MT103/202 기본 필드
        ":20:": {"max_len": 16, "pattern": r"[A-Z0-9/\-]{1,16}"},
        ":21:": {"max_len": 16, "pattern": r"[A-Z0-9/\-]{1,16}"},
        ":23B:": {"values": ["CRED", "SPRI", "RETN"]},
        ":32A:": {"format": "YYMMDD+CURRENCY+AMOUNT"},
        ":50K:": {"max_len": 35, "pattern": r"/[A-Z0-9]+.*"},
        ":50F:": {"max_len": 35, "pattern": r"/[A-Z0-9]+.*"},
        ":59:": {"max_len": 35, "pattern": r"/[A-Z0-9]+.*"},
        ":70:": {"max_len": 140, "pattern": r".*"},
        ":71A:": {"values": ["BEN", "OUR", "SHA"]},
        # 은행 식별 필드 (BIC 형식)
        ":52A:": {"pattern": r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"},
        ":57A:": {"pattern": r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"},
        ":58A:": {"pattern": r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"},
        # MT900/910 계좌 정보
        ":25:": {"pattern": r"[A-Z0-9\-]{1,35}"},
        # MT940/950 잔액 보고 필드
        ":28C:": {"pattern": r"\d+/[A-Z0-9]+"},
        ":60F:": {"pattern": r"[CD]\d{6}[A-Z]{3}\d+"},
        ":62F:": {"pattern": r"[CD]\d{6}[A-Z]{3}\d+"},
        ":61:": {"pattern": r"\d{6}\d{4}[CD]\d+"},
    }

    def validate(self, tag: str, value: str) -> ValidationResult:
        """
        단일 태그의 값을 규칙에 따라 검증한다.

        검증 항목:
        1. 규칙이 정의되지 않은 태그 → 경고만 남기고 통과
        2. max_len → 값의 길이가 최대 길이를 초과하는지 확인
        3. pattern → 값이 정규식 패턴과 일치하는지 확인
        4. values → 값이 허용 목록에 포함되는지 확인
        5. format → 특수 포맷(YMD+통화+금액 등) 검증

        Args:
            tag:   태그 이름 (예: ":20:", ":32A:")
            value: 태그 값 (예: "SENDER-REF-001", "240101KRW50000000")

        Returns:
            ValidationResult 객체 (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        rule = self.RULES.get(tag)
        if rule is None:
            # 정의되지 않은 태그는 경고만 남기고 통과 처리
            warnings.append(f"No validation rule defined for tag {tag}")
            return ValidationResult(is_valid=True, errors=[], warnings=warnings)

        # 최대 길이 검증
        if "max_len" in rule and len(value) > rule["max_len"]:
            errors.append(
                f"{tag} exceeds max length {rule['max_len']} (got {len(value)})"
            )

        # 정규식 패턴 검증
        if "pattern" in rule:
            if not re.match(rule["pattern"], value.strip()):
                errors.append(f"{tag} value '{value}' does not match pattern {rule['pattern']}")

        # 허용 값 목록 검증
        if "values" in rule and value.strip() not in rule["values"]:
            errors.append(
                f"{tag} value '{value}' is not valid. Allowed: {rule['values']}"
            )

        # 특수 포맷 검증
        if "format" in rule:
            format_errors = self._validate_format(tag, value, rule["format"])
            errors.extend(format_errors)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_mt103(self, message: dict) -> ValidationResult:
        """
        MT103 메시지 전체에 대해 필수 필드 존재 여부와 각 필드 값을 검증한다.

        MT103 필수 필드:
        - :20: — Transaction Reference (거래 참조번호)
        - :23B: — Bank Operation Code (은행 업무 코드)
        - :32A: — Value Date / Currency / Amount (결제일/통화/금액)
        - :50K: 또는 :50F: — Ordering Customer (송금 고객)
        - :59: — Beneficiary Customer (수령 고객)

        Args:
            message: {태그: 값} 형태의 딕셔너리 (예: {":20:": "REF-001", ":23B:": "CRED", ...})

        Returns:
            ValidationResult 객체
        """
        errors = []
        warnings = []

        # MT103 필수 필드 정의
        required_fields = [":20:", ":23B:", ":32A:"]
        # :50K: 또는 :50F: 중 하나만 있으면 통과
        has_50 = ":50K:" in message or ":50F:" in message
        has_59 = ":59:" in message

        # 필수 필드 누락 검사
        for field in required_fields:
            if field not in message:
                errors.append(f"Required field {field} missing")

        if not has_50:
            errors.append("Required field :50K: or :50F: missing")
        if not has_59:
            errors.append("Required field :59: missing")

        # 각 필드 개별 값 검증
        for tag, value in message.items():
            result = self.validate(tag, value)
            errors.extend(result.errors)
            warnings.extend(result.warnings)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _validate_format(self, tag: str, value: str, fmt: str) -> list[str]:
        """
        특수 포맷 규칙을 검증한다.
        현재는 :32A: 필드의 YYMMDD+CURRENCY+AMOUNT 포맷만 지원한다.

        포맷 예: "240101KRW50000000" (2024년 1월 1일, 5천만원)
        - YYMMDD: 6자리 숫자
        - CURRENCY: 3자리 영대문자 (ISO 4217)
        - AMOUNT: 숫자 (쉼표 포함 가능)

        Args:
            tag:   태그 이름 (에러 메시지용)
            value: 태그 값
            fmt:   포맷 이름 ("YYMMDD+CURRENCY+AMOUNT")

        Returns:
            오류 메시지 리스트 (포맷이 맞으면 빈 리스트)
        """
        errors = []
        if fmt == "YYMMDD+CURRENCY+AMOUNT":
            if not re.match(r"^\d{6}[A-Z]{3}\d+(,\d{0,2})?$", value.strip()):
                errors.append(f"{tag} format should be YYMMDD+CURRENCY+AMOUNT (got '{value}')")
        return errors
