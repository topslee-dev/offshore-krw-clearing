from datetime import time
from src.cutoff.manager import CutOffTimeManager


class TestTC003CutoffExceeded:

    def setup_method(self):
        self.manager = CutOffTimeManager()

    def test_bok_krw_domestic_cutoff_time(self):
        cutoff = self.manager.get_cutoff_time("BOK_KRW_DOMESTIC")
        assert cutoff == time(16, 30)

    def test_bok_krw_offshore_cutoff_time(self):
        cutoff = self.manager.get_cutoff_time("BOK_KRW_OFFSHORE")
        assert cutoff == time(15, 0)

    def test_swift_daily_cutoff_time(self):
        cutoff = self.manager.get_cutoff_time("SWIFT_DAILY")
        assert cutoff == time(17, 0)

    def test_check_cutoff_returns_result(self):
        result = self.manager.check_cutoff("BOK_KRW_OFFSHORE")
        assert hasattr(result, "is_within")
        assert hasattr(result, "remaining_minutes")
        assert hasattr(result, "next_value_date")

    def test_is_available_returns_bool(self):
        available = self.manager.is_available("BOK_KRW_OFFSHORE")
        assert isinstance(available, bool)

    def test_next_value_date_is_future(self):
        result = self.manager.check_cutoff("BOK_KRW_OFFSHORE")
        from datetime import date
        assert result.next_value_date >= date.today()

    def test_cutoff_exceeded_flow(self):
        result = self.manager.check_cutoff("BOK_KRW_DOMESTIC")
        if not result.is_within:
            assert result.remaining_minutes == 0
            assert result.next_value_date > __import__("datetime").date.today()

    def test_unknown_payment_type_raises(self):
        import pytest
        with pytest.raises(KeyError):
            self.manager.check_cutoff("UNKNOWN_TYPE")

    def test_all_cutoff_times_defined(self):
        assert "BOK_KRW_DOMESTIC" in self.manager.CUTOFF_TIMES
        assert "BOK_KRW_OFFSHORE" in self.manager.CUTOFF_TIMES
        assert "SWIFT_DAILY" in self.manager.CUTOFF_TIMES
