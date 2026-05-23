from src.validator.swift_validator import SWIFTValidator


class TestSWIFTValidatorAllTypes:
    validator = SWIFTValidator()

    def test_validate_mt202_valid(self):
        msg = {
            "block4": {
                ":20:": "COVER-001",
                ":21:": "MT103-REF-001",
                ":32A:": "240101KRW50000000",
                ":52A:": "HNBKKRSEXXX",
                ":58A:": "WOOBKRSEXXX",
            }
        }
        result = self.validator.validate_mt202(msg)
        assert result.is_valid is True

    def test_validate_mt202_missing_required(self):
        msg = {"block4": {":20:": "COVER-001"}}
        result = self.validator.validate_mt202(msg)
        assert result.is_valid is False

    def test_validate_mt900_valid(self):
        msg = {
            "block4": {
                ":20:": "BOK-900-001",
                ":21:": "MT202-REF-001",
                ":25:": "1234567890",
                ":32A:": "240101KRW50000000",
            }
        }
        result = self.validator.validate_mt900(msg)
        assert result.is_valid is True

    def test_validate_mt900_missing_required(self):
        msg = {"block4": {":20:": "BOK-900-001"}}
        result = self.validator.validate_mt900(msg)
        assert result.is_valid is False

    def test_validate_mt910_valid(self):
        msg = {
            "block4": {
                ":20:": "BOK-910-001",
                ":21:": "MT202-REF-001",
                ":25:": "1234567890",
                ":32A:": "240101KRW50000000",
            }
        }
        result = self.validator.validate_mt910(msg)
        assert result.is_valid is True

    def test_validate_mt940_valid(self):
        msg = {
            "block4": {
                ":20:": "STMT-001",
                ":25:": "1234567890",
                ":28C:": "1/1",
                ":60F:": "C240101KRW1000000000,",
                ":62F:": "C240101KRW1500000000,",
            }
        }
        result = self.validator.validate_mt940(msg)
        assert result.is_valid is True

    def test_validate_mt940_missing_required(self):
        msg = {"block4": {":20:": "STMT-001"}}
        result = self.validator.validate_mt940(msg)
        assert result.is_valid is False

    def test_validate_mt950_valid(self):
        msg = {
            "block4": {
                ":20:": "STMT-001",
                ":25:": "KRW-NOSTRO-001",
                ":28C:": "1/1",
                ":60F:": "C240101KRW500000000,",
                ":62F:": "C240101KRW650000000,",
            }
        }
        result = self.validator.validate_mt950(msg)
        assert result.is_valid is True

    def test_iso4217_invalid_currency(self):
        msg = {
            "block4": {
                ":20:": "REF-001",
                ":23B:": "CRED",
                ":32A:": "240101ZZZ50000000",
                ":50K:": "/123456789",
                ":59:": "/987654321",
            }
        }
        result = self.validator.validate_mt103(msg)
        assert result.is_valid is False
        assert any("ISO 4217" in e for e in result.errors)
