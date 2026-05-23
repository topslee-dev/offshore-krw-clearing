from src.parser.bic_validator import BICValidator, BICInfo


class TestBICValidator:
    validator = BICValidator()

    def test_validate_valid_bic_woori(self):
        assert self.validator.validate("WOOBKRSEXXX") is True

    def test_validate_valid_bic_bok(self):
        assert self.validator.validate("HNBKKRSEXXX") is True

    def test_validate_valid_bic_short(self):
        assert self.validator.validate("HNBKKRSE") is True

    def test_validate_lowercase_returns_true(self):
        assert self.validator.validate("hnbkkrsexxx") is True

    def test_validate_invalid_bic(self):
        assert self.validator.validate("INVALID") is False

    def test_validate_empty_string(self):
        assert self.validator.validate("") is False

    def test_validate_too_short(self):
        assert self.validator.validate("ABCD") is False

    def test_validate_invalid_country(self):
        assert self.validator.validate("ABCDZZSEXXX") is False

    def test_parse_valid_bic_returns_info(self):
        info = self.validator.parse("WOOBKRSEXXX")
        assert isinstance(info, BICInfo)

    def test_parse_valid_bic_fields(self):
        info = self.validator.parse("WOOBKRSEXXX")
        assert info.bank_code == "WOOB"
        assert info.country_code == "KR"
        assert info.location_code == "SE"
        assert info.branch_code == "XXX"

    def test_parse_valid_bic_short(self):
        info = self.validator.parse("HNBKKRSE")
        assert info is not None
        assert info.bank_code == "HNBK"
        assert info.branch_code is None

    def test_parse_invalid_bic_returns_none(self):
        info = self.validator.parse("INVALID")
        assert info is None

    def test_parse_empty_returns_none(self):
        info = self.validator.parse("")
        assert info is None

    def test_validate_eximbank(self):
        assert self.validator.validate("EXIKKRSEXXX") is True

    def test_validate_generic_us_bank(self):
        assert self.validator.validate("BOFAUS3NXXX") is True

    def test_parse_lowercase_works(self):
        info = self.validator.parse("hnbkkrsexxx")
        assert info is not None
        assert info.bank_code == "HNBK"
