import re
from dataclasses import dataclass, field


@dataclass
class Block1Info:
    protocol: str = ""
    session: str = ""
    sender_bic: str = ""
    sequence: str = ""


@dataclass
class Block2Info:
    direction: str = ""
    mt_type: str = ""
    receiver_bic: str = ""
    terminal: str = ""


@dataclass
class ParsedMessage:
    """
    SWIFT MT 메시지를 Block별로 파싱한 결과를 저장하는 데이터 클래스.
    Block 1(Basic Header)부터 Block 5(Trailer)까지의 내용을 각각 보관한다.
    raw_ 접두사가 붙은 필드는 원본 Block 문자열을, 없는 필드는 정제된 내용을 저장한다.
    """
    block1: str | None = None
    block1_raw: str | None = None
    block1_info: Block1Info | None = None
    block2: str | None = None
    block2_raw: str | None = None
    block2_info: Block2Info | None = None
    block3: str | None = None
    block3_raw: str | None = None
    block4: str | None = None
    block4_raw: str | None = None
    block5: str | None = None
    block5_raw: str | None = None

    @property
    def is_complete(self) -> bool:
        return self.block1 is not None and self.block2 is not None and self.block4 is not None


class SWIFTBlockParser:
    """
    SWIFT MT 메시지를 Block 1~5로 분리하여 파싱한다.
    기본 형식: {1:...}{2:...}{3:...}{4:...-}{5:...}

    사용 예:
        parser = SWIFTBlockParser()
        result = parser.parse(raw_message)
        print(result.block1)  # Basic Header 내용
        print(result.block4)  # Text 본문 내용
    """

    def parse(self, raw_message: str) -> ParsedMessage:
        """
        원본 SWIFT 메시지를 받아 Block별로 파싱한다.

        Args:
            raw_message: SWIFT MT 원본 문자열 (Block 1~5 포함)

        Returns:
            ParsedMessage 객체 — 각 Block의 원본(raw)과 정제된 내용 포함
        """
        result = ParsedMessage()
        blocks = self._extract_blocks(raw_message)

        for block_id, content in blocks:
            if block_id == "1":
                result.block1_raw = f"{{1:{content}}}"
                result.block1 = self._parse_block1(content)
                result.block1_info = self._parse_block1_info(content)
            elif block_id == "2":
                result.block2_raw = f"{{2:{content}}}"
                result.block2 = self._parse_block2(content)
                result.block2_info = self._parse_block2_info(content)
            elif block_id == "3":
                # User Header: {3:{108:REF...}}
                result.block3_raw = f"{{3:{content}}}"
                result.block3 = self._parse_block3(content)
            elif block_id == "4":
                # Text 본문: {4:\\n:20:...\\n-}
                result.block4_raw = f"{{4:\n{content}\n}}"
                result.block4 = self._parse_block4(content)
            elif block_id == "5":
                # Trailer: {5:CHK...}
                result.block5_raw = f"{{5:{content}}}"
                result.block5 = self._parse_block5(content)

        return result

    def _extract_blocks(self, raw_message: str) -> list[tuple[str, str]]:
        """
        정규표현식으로 {id:content} 패턴을 찾아 Block ID와 내용을 추출한다.

        패턴: {숫자:내용} — Block ID(1~5)와 중괄호 안의 내용을 그룹화
        Block 4의 경우 내용이 여러 줄에 걸쳐 있으므로 re.DOTALL 플래그 사용

        Returns:
            [(block_id, content), ...] 형태의 리스트
        """
        pattern = r"\{(\d):(.*?)(?:\}|$)"
        matches = re.findall(pattern, raw_message, re.DOTALL)
        result = []
        for block_id, content in matches:
            content = content.rstrip()
            result.append((block_id, content))
        return result

    def _parse_block1(self, content: str) -> str:
        content = content.strip("{}")
        return content

    def _parse_block1_info(self, content: str) -> Block1Info:
        raw = content.strip("{}")
        if len(raw) >= 5:
            protocol = raw[0:1]
            session = raw[1:3]
            rest = raw[3:]
            sequence_match = re.search(r"(\d{6,})", rest)
            if sequence_match:
                bic_part = rest[: sequence_match.start()]
                sequence = sequence_match.group(1)
            else:
                bic_part = rest
                sequence = ""
            return Block1Info(
                protocol=protocol,
                session=session,
                sender_bic=bic_part,
                sequence=sequence,
            )
        return Block1Info()

    def _parse_block2(self, content: str) -> str:
        content = content.strip("{}")
        return content

    def _parse_block2_info(self, content: str) -> Block2Info:
        raw = content.strip("{}")
        if len(raw) >= 7:
            direction = raw[0:1]
            mt_type = raw[1:4]
            remaining = raw[4:]
            terminal = remaining[-3:] if remaining[-3:] in ("XXX", "YYY") else ""
            receiver_bic = remaining[:-3] if terminal else remaining
            return Block2Info(
                direction=direction,
                mt_type=mt_type,
                receiver_bic=receiver_bic,
                terminal=terminal,
            )
        return Block2Info()

    def _parse_block3(self, content: str) -> str:
        """
        Block 3: User Header — 중첩된 중괄호 {3:{108:...}}를 처리한다.
        바깥 중괄호를 제거한 후, 내부 {108:...}에서도 중괄호를 벗겨낸다.
        """
        content = content.strip("{}")
        inner = re.sub(r"^\{|\}$", "", content)
        return inner

    def _parse_block4(self, content: str) -> str:
        """
        Block 4: Text 본문 — 앞뒤 공백과 종료 마커(-)를 제거한다.
        Block 4는 항상 -}로 끝나므로, content 끝의 -를 제거한다.
        """
        content = content.strip()
        if content.endswith("-"):
            content = content[:-1]
        return content.strip()

    def _parse_block5(self, content: str) -> str:
        """Block 5: Trailer — 중괄호를 제거하고 내부 문자열(CHK 등) 반환"""
        content = content.strip("{}")
        return content
