from decimal import Decimal
from src.builder.mt103_builder import MT103Builder


RAW_EXPECTED = """{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{3:{108:REF20240101001}}
{4:
:20:REF20240101001
:23B:CRED
:32A:240101KRW50000000,
:50K:/123456789
WOORI BANK SEOUL
:57A:HNBKKRSE
:59:/987654321
KOREA BANK COUNTERPARTY
:70:OFFSHORE KRW PAYMENT TEST
:71A:SHA
-}"""


class TestMT103Builder:
    builder = MT103Builder()

    PAYMENT = {
        "sender_ref": "REF20240101001",
        "value_date": "240101",
        "currency": "KRW",
        "amount": Decimal("50000000"),
        "sender_bic": "WOOBURKRSAXXX",
        "receiver_bic": "HNBKKRSEXXX",
        "ordering_customer": {
            "account": "/123456789",
            "name": "WOORI BANK SEOUL",
        },
        "beneficiary_customer": {
            "account": "/987654321",
            "name": "KOREA BANK COUNTERPARTY",
        },
        "beneficiary_bank": "HNBKKRSE",
        "remittance_info": "OFFSHORE KRW PAYMENT TEST",
        "charge_type": "SHA",
    }

    def test_build_returns_string(self):
        result = self.builder.build(self.PAYMENT)
        assert isinstance(result, str)

    def test_build_starts_with_block1(self):
        result = self.builder.build(self.PAYMENT)
        assert result.startswith("{1:F01")

    def test_build_ends_with_closing(self):
        result = self.builder.build(self.PAYMENT)
        assert result.endswith("-}")

    def test_build_contains_reference(self):
        result = self.builder.build(self.PAYMENT)
        assert ":20:REF20240101001" in result

    def test_build_contains_amount(self):
        result = self.builder.build(self.PAYMENT)
        assert ":32A:240101KRW50000000," in result

    def test_build_contains_ordering_account(self):
        result = self.builder.build(self.PAYMENT)
        assert ":50K:/123456789" in result

    def test_build_contains_beneficiary(self):
        result = self.builder.build(self.PAYMENT)
        assert ":59:/987654321" in result

    def test_build_contains_beneficiary_bank(self):
        result = self.builder.build(self.PAYMENT)
        assert ":57A:HNBKKRSE" in result

    def test_build_contains_remittance(self):
        result = self.builder.build(self.PAYMENT)
        assert "OFFSHORE KRW PAYMENT TEST" in result

    def test_build_contains_charge_sha(self):
        result = self.builder.build(self.PAYMENT)
        assert ":71A:SHA" in result

    def test_build_full_message(self):
        result = self.builder.build(self.PAYMENT)
        assert result == RAW_EXPECTED

    def test_build_without_remittance(self):
        data = {**self.PAYMENT, "remittance_info": None}
        result = self.builder.build(data)
        assert ":70:" not in result

    def test_build_without_beneficiary_bank(self):
        data = {**self.PAYMENT, "beneficiary_bank": None}
        result = self.builder.build(data)
        assert ":57A:" not in result

    def test_build_multi_line_block4(self):
        result = self.builder.build(self.PAYMENT)
        lines = result.split("\n")
        block4_start = [i for i, l in enumerate(lines) if l.startswith("{4:")][0]
        block4_end = [i for i, l in enumerate(lines) if l == "-}"][0]
        assert block4_end > block4_start
