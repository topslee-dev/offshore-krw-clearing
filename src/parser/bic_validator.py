import re
from dataclasses import dataclass


@dataclass
class BICInfo:
    """
    BIC 코드를 분해한 정보.
    BIC(Business Identifier Code)는 8자리 또는 11자리로 구성된다.

    Attributes:
        bank_code:     은행 코드 (4자리, 예: "WOOB" — 우리은행)
        country_code:  국가 코드 (2자리, ISO 3166, 예: "KR" — 대한민국)
        location_code: 위치 코드 (2자리, 예: "SE" — 서울)
        branch_code:   지점 코드 (3자리, 선택, 예: "XXX" — 본점)
    """
    bank_code: str
    country_code: str
    location_code: str
    branch_code: str | None = None


class BICValidator:
    """
    SWIFT BIC 코드의 유효성을 검증하고 구조를 분석한다.
    BIC 형식: [A-Z]{4}[A-Z]{2}[A-Z0-9]{2}[A-Z0-9]{3} (8+3)

    사용 예:
        validator = BICValidator()
        validator.validate("HNBKKRSEXXX")  # True
        info = validator.parse("WOOBKRSEXXX")  # BICInfo 객체
    """

    # BIC 정규식: 4자리 은행코드 + 2자리 국가코드 + 2자리 위치코드 + [선택 3자리 지점코드]
    BIC_PATTERN = re.compile(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$")

    # ISO 3166-1 alpha-2 국가 코드 중 SWIFT에서 주로 사용하는 코드 목록
    COUNTRY_CODES = {
        "KR", "US", "GB", "DE", "FR", "JP", "CN", "SG", "HK",
        "CH", "NL", "AU", "CA", "IT", "ES", "SE", "DK", "NO",
        "FI", "BE", "AT", "IE", "LU", "PT", "GR", "NZ", "MY",
        "TH", "VN", "ID", "PH", "IN", "RU", "ZA", "BR", "MX",
    }

    def validate(self, bic: str) -> bool:
        """
        BIC 코드가 올바른 형식과 유효한 국가 코드를 가지는지 검증한다.

        검증 조건:
        1. 형식: 8자리(기본) 또는 11자리(지점 포함)의 영대문자+숫자
        2. 국가 코드가 ISO 3166 목록에 존재

        Args:
            bic: 검증할 BIC 문자열 (대소문자 구분 없음)

        Returns:
            유효하면 True, 아니면 False
        """
        bic = bic.upper().strip()
        if not self.BIC_PATTERN.match(bic):
            return False
        # 5~6번째 문자가 국가 코드 (예: "KR", "US")
        country = bic[4:6]
        if country not in self.COUNTRY_CODES:
            return False
        return True

    def parse(self, bic: str) -> BICInfo | None:
        """
        유효한 BIC 코드를 분해하여 구성 요소별 정보를 반환한다.
        유효하지 않은 BIC는 None을 반환한다.

        Args:
            bic: 분해할 BIC 문자열

        Returns:
            BICInfo 객체 (유효한 경우), None (유효하지 않은 경우)
        """
        bic = bic.upper().strip()
        if not self.validate(bic):
            return None

        # BIC 구조: WOOB + KR + SE + XXX
        bank_code = bic[0:4]        # 은행 코드
        country_code = bic[4:6]     # 국가 코드
        location_code = bic[6:8]    # 위치 코드
        branch_code = bic[8:11] if len(bic) > 8 else None  # 지점 코드 (11자리인 경우만)

        return BICInfo(
            bank_code=bank_code,
            country_code=country_code,
            location_code=location_code,
            branch_code=branch_code,
        )
