from decimal import Decimal
from src.builder.mt202_builder import MT202Builder


RAW_EXPECTED = """{1:F01WOOBURKRSAXXX0000000000}
{2:O202WOOBURKRSAXXX}
{4:
:20:COVER-001
:21:MT103-REF-001
:32A:240101KRW50000000,
:52A:WOOBUS33
:58A:HNBKKRSE
-}"""


class TestMT202Builder:
    builder = MT202Builder()

    COVER = {
        "sender_ref": "COVER-001",
        "related_ref": "MT103-REF-001",
        "value_date": "240101",
        "currency": "KRW",
        "amount": Decimal("50000000"),
        "sender_bic": "WOOBURKRSAXXX",
        "ordering_institution": "WOOBUS33",
        "beneficiary_institution": "HNBKKRSE",
    }

    def test_build_returns_string(self):
        result = self.builder.build(self.COVER)
        assert isinstance(result, str)

    def test_build_starts_with_block1(self):
        result = self.builder.build(self.COVER)
        assert result.startswith("{1:F01")

    def test_build_ends_with_closing(self):
        result = self.builder.build(self.COVER)
        assert result.endswith("-}")

    def test_build_contains_sender_ref(self):
        result = self.builder.build(self.COVER)
        assert ":20:COVER-001" in result

    def test_build_contains_related_ref(self):
        result = self.builder.build(self.COVER)
        assert ":21:MT103-REF-001" in result

    def test_build_contains_amount(self):
        result = self.builder.build(self.COVER)
        assert ":32A:240101KRW50000000," in result

    def test_build_contains_ordering(self):
        result = self.builder.build(self.COVER)
        assert ":52A:WOOBUS33" in result

    def test_build_contains_beneficiary(self):
        result = self.builder.build(self.COVER)
        assert ":58A:HNBKKRSE" in result

    def test_build_full_message(self):
        result = self.builder.build(self.COVER)
        assert result == RAW_EXPECTED

    def test_build_with_usd_amount(self):
        data = {**self.COVER, "currency": "USD", "amount": Decimal("1000000")}
        result = self.builder.build(data)
        assert ":32A:240101USD1000000," in result

    def test_build_block2_is_output(self):
        result = self.builder.build(self.COVER)
        assert "{2:O202" in result

    def test_build_no_block3(self):
        result = self.builder.build(self.COVER)
        assert "{3:" not in result
