from decimal import Decimal
from src.flow.exchange_processor import ExchangeRateProcessor, KRWAmount


class TestExchangeRateProcessor:
    def setup_method(self):
        self.processor = ExchangeRateProcessor()

    def test_convert_usd_to_krw(self):
        result = self.processor.convert_to_krw(Decimal("1000"), "USD")
        assert isinstance(result, KRWAmount)
        assert result.currency == "USD"
        assert result.original == Decimal("1000")
        assert result.krw_amount > Decimal("0")

    def test_convert_cnh_to_krw(self):
        result = self.processor.convert_to_krw(Decimal("1000"), "CNH")
        assert result.krw_amount > Decimal("0")

    def test_apply_spread(self):
        result = self.processor.apply_spread(Decimal("1330.50"), 30)
        assert result > Decimal("1330.50")

    def test_spread_calculation(self):
        spread = self.processor.apply_spread(Decimal("1000"), 100)
        assert spread == Decimal("1010.00")

    def test_zero_spread(self):
        result = self.processor.apply_spread(Decimal("1330.50"), 0)
        assert result == Decimal("1330.50")

    def test_bok_reporting_krw(self):
        result = self.processor.calculate_bok_reporting_amount(
            Decimal("50000000"), "KRW"
        )
        assert result == Decimal("50000000")

    def test_bok_reporting_usd(self):
        result = self.processor.calculate_bok_reporting_amount(
            Decimal("10000"), "USD"
        )
        assert result > Decimal("0")

    def test_set_rate(self):
        self.processor.set_rate("USD", Decimal("1400.00"))
        result = self.processor.convert_to_krw(Decimal("100"), "USD")
        assert result.rate == Decimal("1400.00")

    def test_get_rate(self):
        rate = self.processor.get_rate("USD")
        assert rate is not None
        assert rate > Decimal("0")
