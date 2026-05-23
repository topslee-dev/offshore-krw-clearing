from src.validator.swift_validator import SWIFTValidator


class TestSWIFTValidator:
    validator = SWIFTValidator()

    # === validate_field ===

    def test_validate_field_valid_20(self):
        assert self.validator.validate_field(":20:", "REF-001") is True

    def test_validate_field_invalid_20_too_long(self):
        assert self.validator.validate_field(":20:", "A" * 17) is False

    def test_validate_field_valid_23b(self):
        assert self.validator.validate_field(":23B:", "CRED") is True

    def test_validate_field_invalid_23b(self):
        assert self.validator.validate_field(":23B:", "INVALID") is False

    def test_validate_field_valid_71a(self):
        assert self.validator.validate_field(":71A:", "SHA") is True
        assert self.validator.validate_field(":71A:", "BEN") is True
        assert self.validator.validate_field(":71A:", "OUR") is True

    def test_validate_field_invalid_71a(self):
        assert self.validator.validate_field(":71A:", "INVALID") is False

    # === validate_mt103 ===

    def test_validate_mt103_valid(self):
        msg = {
            "block4": {
                ":20:": "REF-001",
                ":23B:": "CRED",
                ":32A:": "240101KRW50000000",
                ":50K:": "/123456789",
                ":59:": "/987654321",
            }
        }
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is True

    def test_validate_mt103_missing_required(self):
        msg = {"block4": {":20:": "REF-001"}}
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is False
        errors = " ".join(result.errors)
        assert ":23B:" in errors
        assert ":32A:" in errors

    def test_validate_mt103_missing_50(self):
        msg = {
            "block4": {
                ":20:": "REF-001",
                ":23B:": "CRED",
                ":32A:": "240101KRW50000000",
                ":59:": "/987654321",
            }
        }
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is False
        assert any(":50K:" in e for e in result.errors)

    def test_validate_mt103_with_50f(self):
        msg = {
            "block4": {
                ":20:": "REF-001",
                ":23B:": "CRED",
                ":32A:": "240101KRW50000000",
                ":50F:": "/123456789",
                ":59:": "/987654321",
            }
        }
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is True

    def test_validate_mt103_invalid_field_value(self):
        msg = {
            "block4": {
                ":20:": "REF-001",
                ":23B:": "INVALID",
                ":32A:": "240101KRW50000000",
                ":50K:": "/123456789",
                ":59:": "/987654321",
            }
        }
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is False
        assert any(":23B:" in e for e in result.errors)

    def test_validate_mt103_block4_not_dict(self):
        msg = {"block4": "not a dict"}
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is False
