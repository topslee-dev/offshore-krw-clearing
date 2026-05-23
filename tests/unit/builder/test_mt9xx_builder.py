from decimal import Decimal
from src.builder.mt9xx_builder import MT9xxBuilder


class TestMT9xxBuilder:
    builder = MT9xxBuilder()

    DEBIT = {
        "reference": "BOK-900-001",
        "related_ref": "MT202-REF-001",
        "account": "1234567890",
        "value_date": "240101",
        "currency": "KRW",
        "amount": Decimal("50000000"),
    }

    CREDIT = {
        "reference": "BOK-910-001",
        "related_ref": "MT202-REF-001",
        "account": "1234567890",
        "value_date": "240101",
        "currency": "KRW",
        "amount": Decimal("50000000"),
    }

    STATEMENT = {
        "reference": "STMT-950-001",
        "account": "KRW-NOSTRO-001",
        "sequence": "1/1",
        "opening_balance": "C240101KRW500000000,",
        "closing_balance": "C240101KRW650000000,",
        "statement_lines": [
            "240101C200000000,,NTRFMT202COVER001",
            "240101D50000000,,NTRFMT900DEBIT001",
        ],
    }

    # === MT900 ===

    def test_build_mt900_starts_with_block1(self):
        result = self.builder.build_mt900(self.DEBIT)
        assert result.startswith("{1:F01")

    def test_build_mt900_ends_with_closing(self):
        result = self.builder.build_mt900(self.DEBIT)
        assert result.endswith("-}")

    def test_build_mt900_contains_reference(self):
        result = self.builder.build_mt900(self.DEBIT)
        assert ":20:BOK-900-001" in result

    def test_build_mt900_contains_related_ref(self):
        result = self.builder.build_mt900(self.DEBIT)
        assert ":21:MT202-REF-001" in result

    def test_build_mt900_contains_account(self):
        result = self.builder.build_mt900(self.DEBIT)
        assert ":25:1234567890" in result

    def test_build_mt900_contains_amount(self):
        result = self.builder.build_mt900(self.DEBIT)
        assert ":32A:240101KRW50000000," in result

    def test_build_mt900_block2_is_O900(self):
        result = self.builder.build_mt900(self.DEBIT)
        assert "{2:O900" in result

    # === MT910 ===

    def test_build_mt910_ends_with_closing(self):
        result = self.builder.build_mt910(self.CREDIT)
        assert result.endswith("-}")

    def test_build_mt910_contains_reference(self):
        result = self.builder.build_mt910(self.CREDIT)
        assert ":20:BOK-910-001" in result

    def test_build_mt910_contains_related_ref(self):
        result = self.builder.build_mt910(self.CREDIT)
        assert ":21:MT202-REF-001" in result

    def test_build_mt910_contains_amount(self):
        result = self.builder.build_mt910(self.CREDIT)
        assert ":32A:240101KRW50000000," in result

    def test_build_mt910_block2_is_O910(self):
        result = self.builder.build_mt910(self.CREDIT)
        assert "{2:O910" in result

    # === MT940 ===

    def test_build_mt940_returns_string(self):
        result = self.builder.build_mt940(self.STATEMENT)
        assert isinstance(result, str)

    def test_build_mt940_starts_with_block1(self):
        result = self.builder.build_mt940(self.STATEMENT)
        assert result.startswith("{1:F01")

    def test_build_mt940_ends_with_closing(self):
        result = self.builder.build_mt940(self.STATEMENT)
        assert result.endswith("-}")

    def test_build_mt940_contains_reference(self):
        result = self.builder.build_mt940(self.STATEMENT)
        assert ":20:STMT-950-001" in result

    def test_build_mt940_contains_sequence(self):
        result = self.builder.build_mt940(self.STATEMENT)
        assert ":28C:1/1" in result

    def test_build_mt940_contains_opening(self):
        result = self.builder.build_mt940(self.STATEMENT)
        assert ":60F:C240101KRW500000000," in result

    def test_build_mt940_contains_closing(self):
        result = self.builder.build_mt940(self.STATEMENT)
        assert ":62F:C240101KRW650000000," in result

    def test_build_mt940_contains_statement_lines(self):
        result = self.builder.build_mt940(self.STATEMENT)
        assert ":61:240101C200000000,,NTRFMT202COVER001" in result
        assert ":61:240101D50000000,,NTRFMT900DEBIT001" in result

    def test_build_mt940_block2_is_I940(self):
        result = self.builder.build_mt940(self.STATEMENT)
        assert "{2:I940" in result

    # === MT950 ===

    def test_build_mt950_returns_string(self):
        result = self.builder.build_mt950(self.STATEMENT)
        assert isinstance(result, str)

    def test_build_mt950_block2_is_I950(self):
        result = self.builder.build_mt950(self.STATEMENT)
        assert "{2:I950" in result

    def test_build_mt950_contains_same_content_as_mt940(self):
        mt940 = self.builder.build_mt940(self.STATEMENT)
        mt950 = self.builder.build_mt950(self.STATEMENT)
        assert ":20:STMT-950-001" in mt950
        assert ":60F:" in mt950
        assert ":62F:" in mt950

    # === Empty lines ===

    def test_build_mt940_no_lines(self):
        data = {**self.STATEMENT, "statement_lines": []}
        result = self.builder.build_mt940(data)
        assert ":61:" not in result
