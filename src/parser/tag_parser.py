import re
from dataclasses import dataclass


@dataclass
class Tag:
    """
    SWIFT 메시지에서 추출한 개별 태그 정보.
    태그는 Block 4(Text) 내에서 :XX: 형식으로 표시된다.

    Attributes:
        name:  태그 이름 (예: ":20:", ":32A:")
        value: 태그 값 (예: "SENDER-REF-001", "240101KRW50000000,")
        line:  Block 4 내에서 태그가 위치한 줄 번호 (1부터 시작)
    """
    name: str
    value: str
    line: int


@dataclass
class Field:
    """
    태그를 파싱하여 구조화한 필드 정보.
    일부 태그는 :52A/D: 처럼 qualifier를 포함할 수 있다.

    Attributes:
        name:      태그 이름 (예: ":52A/D:")
        raw_value: 원본 값 그대로
        qualifier: 태그 이름의 '/' 뒤에 오는 추가 식별자 (예: "D")
        value:     실제 값 (raw_value와 같거나 처리된 값)
    """
    name: str
    raw_value: str
    qualifier: str | None = None
    value: str | None = None

    def __post_init__(self):
        """value가 명시적으로 주어지지 않으면 raw_value를 그대로 사용"""
        if self.value is None:
            self.value = self.raw_value


class TagParser:
    """
    SWIFT Block 4(Text)에서 태그(:XX:)를 추출하고 파싱한다.
    SWIFT 태그는 :20:VALUE 형식으로, 줄 시작 부분의 콜론(:)으로 구분된다.

    사용 예:
        parser = TagParser()
        tags = parser.extract_tags(block4_text)
        field = parser.parse_field(tags[0])
    """

    # 태그 패턴: 줄 시작의 :XX:와 그 뒤의 값
    # \w+ 는 태그 이름(알파벳+숫자)을, (.*)는 값을 캡처
    TAG_PATTERN = re.compile(r"^:(\w+):\s*(.*)", re.MULTILINE)

    # Block 4 종료 마커: 마지막 줄의 -}
    # extract_tags 전에 이를 제거해야 함
    BLOCK4_END_PATTERN = re.compile(r"-}$")

    def extract_tags(self, text_block: str) -> list[Tag]:
        """
        Block 4 텍스트에서 모든 태그를 추출한다.
        태그는 :XX:VALUE 형식으로, 각 태그는 새 줄에서 시작한다.

        Args:
            text_block: Block 4의 raw 텍스트 (종료 마커 포함 가능)

        Returns:
            Tag 객체 리스트 (발견 순서대로, 발견되지 않으면 빈 리스트)
        """
        tags = []
        # Block 4 종료 마커(-})를 제거하고 순수 태그 영역만 남김
        text_block = self.BLOCK4_END_PATTERN.sub("", text_block)

        for match in self.TAG_PATTERN.finditer(text_block):
            # 그룹 1: 태그 이름 (20, 32A 등) → :20: 형식으로 변환
            tag_name = f":{match.group(1)}:"
            # 그룹 2: 태그 값 (공백 제거)
            tag_value = match.group(2).strip()
            # 현재 태그 앞까지의 줄바꿈 개수 + 1 = 태그의 줄 번호
            line_number = text_block[: match.start()].count("\n") + 1
            tags.append(Tag(name=tag_name, value=tag_value, line=line_number))

        return tags

    def parse_field(self, tag: Tag) -> Field:
        """
        Tag 객체를 Field 객체로 변환한다.
        :52A/D: 형식의 태그에서 '/' 뒤의 qualifier를 추출한다.

        Args:
            tag: TagParser.extract_tags()로 얻은 Tag 객체

        Returns:
            Field 객체 — name, raw_value, qualifier, value 포함
        """
        qualifier = None
        value = tag.value

        # 태그 이름에 '/'가 있으면 qualifier 추출 (예: ":52A/D:" → "D")
        if "/" in tag.name:
            parts = tag.name.strip(":").split("/")
            if len(parts) > 1:
                qualifier = parts[1]

        return Field(
            name=tag.name,
            raw_value=tag.value,
            qualifier=qualifier,
            value=value,
        )
