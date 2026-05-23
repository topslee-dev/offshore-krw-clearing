from src.parser.block_parser import SWIFTBlockParser, ParsedMessage


RAW_MT103 = """
{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{3:{108:REF20240101001}}
{4:
:20:SENDER-REF-001
:23B:CRED
:32A:240101KRW50000000,
:50K:/123456789
WOORI BANK SEOUL
:57A:HNBKKRSE
:59:/987654321
KOREA BANK COUNTERPARTY
:70:OFFSHORE KRW PAYMENT TEST
:71A:SHA
-}
"""

RAW_MT202 = """
{1:F01WOOBURKRSAXXX0000000000}
{2:O202WOOBURKRSAXXX}
{4:
:20:COVER-REF-001
:21:MT103-REF-001
:32A:240101USD1000000,
:52A:WOOBUS33
:58A:HNBKKRSE
-}
"""


class TestSWIFTBlockParser:
    parser = SWIFTBlockParser()

    def test_parse_mt103_returns_parsed_message(self):
        result = self.parser.parse(RAW_MT103)
        assert isinstance(result, ParsedMessage)

    def test_parse_mt103_block1(self):
        result = self.parser.parse(RAW_MT103)
        assert result.block1 is not None
        assert "F01WOOBURKRSAXXX0000000000" in result.block1

    def test_parse_mt103_block2(self):
        result = self.parser.parse(RAW_MT103)
        assert result.block2 is not None
        assert "I103HNBKKRSEXXX" in result.block2

    def test_parse_mt103_block3(self):
        result = self.parser.parse(RAW_MT103)
        assert result.block3 is not None
        assert "108:REF20240101001" in result.block3

    def test_parse_mt103_block4(self):
        result = self.parser.parse(RAW_MT103)
        assert result.block4 is not None
        assert ":20:SENDER-REF-001" in result.block4

    def test_parse_mt103_block5_none(self):
        result = self.parser.parse(RAW_MT103)
        assert result.block5 is None

    def test_parse_mt202_block2_contains_output(self):
        result = self.parser.parse(RAW_MT202)
        assert result.block2 is not None
        assert "O202" in result.block2

    def test_parse_mt202_no_block3(self):
        result = self.parser.parse(RAW_MT202)
        assert result.block3 is None

    def test_is_complete_returns_true_for_valid_message(self):
        result = self.parser.parse(RAW_MT103)
        assert result.is_complete is True

    def test_is_complete_returns_false_for_empty(self):
        result = ParsedMessage()
        assert result.is_complete is False

    def test_parse_empty_string(self):
        result = self.parser.parse("")
        assert isinstance(result, ParsedMessage)
        assert result.block1 is None

    def test_block1_raw_format(self):
        result = self.parser.parse(RAW_MT103)
        assert result.block1_raw.startswith("{1:")
        assert result.block1_raw.endswith("}")

    def test_block4_raw_format(self):
        result = self.parser.parse(RAW_MT103)
        assert result.block4_raw.startswith("{4:")
        assert result.block4_raw.endswith("}")
