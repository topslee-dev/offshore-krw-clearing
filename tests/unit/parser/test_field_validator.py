from src.parser.field_validator import FieldValidator, ValidationResult


class TestFieldValidator:
    validator = FieldValidator()

    def test_validate_twenty_valid(self):
        result = self.validator.validate(":20:", "SENDER-REF-001")
        assert result.is_valid is True

    def test_validate_twenty_too_long(self):
        result = self.validator.validate(":20:", "A" * 17)
        assert result.is_valid is False
        assert any("max length" in e for e in result.errors)

    def test_validate_23b_valid(self):
        result = self.validator.validate(":23B:", "CRED")
        assert result.is_valid is True

    def test_validate_23b_invalid(self):
        result = self.validator.validate(":23B:", "INVALID")
        assert result.is_valid is False

    def test_validate_71a_valid_values(self):
        for val in ["BEN", "OUR", "SHA"]:
            result = self.validator.validate(":71A:", val)
            assert result.is_valid is True

    def test_validate_71a_invalid(self):
        result = self.validator.validate(":71A:", "INVALID")
        assert result.is_valid is False

    def test_validate_32a_format_valid(self):
        result = self.validator.validate(":32A:", "240101KRW50000000")
        assert result.is_valid is True

    def test_validate_32a_format_invalid(self):
        result = self.validator.validate(":32A:", "INVALID")
        assert result.is_valid is False

    def test_validate_50k_valid(self):
        result = self.validator.validate(":50K:", "/123456789")
        assert result.is_valid is True

    def test_validate_unknown_tag_returns_valid_with_warning(self):
        result = self.validator.validate(":99X:", "test")
        assert result.is_valid is True
        assert len(result.warnings) > 0

    def test_validate_mt103_minimal_valid(self):
        msg = {
            ":20:": "REF-001",
            ":23B:": "CRED",
            ":32A:": "240101KRW50000000",
            ":50K:": "/123456789",
            ":59:": "/987654321",
        }
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is True

    def test_validate_mt103_missing_required(self):
        msg = {
            ":20:": "REF-001",
        }
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is False
        errors_str = " ".join(result.errors)
        assert ":23B:" in errors_str
        assert ":32A:" in errors_str

    def test_validate_mt103_missing_50_or_59(self):
        msg = {
            ":20:": "REF-001",
            ":23B:": "CRED",
            ":32A:": "240101KRW50000000",
        }
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is False
        errors_str = " ".join(result.errors)
        assert ":50K" in errors_str
        assert ":59" in errors_str

    def test_validate_mt103_with_50f(self):
        msg = {
            ":20:": "REF-001",
            ":23B:": "CRED",
            ":32A:": "240101KRW50000000",
            ":50F:": "/123456789",
            ":59:": "/987654321",
        }
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is True
