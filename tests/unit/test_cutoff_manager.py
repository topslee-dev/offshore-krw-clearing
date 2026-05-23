from datetime import time
from src.cutoff.manager import CutOffTimeManager, CutOffResult


RAW_MT103 = """{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{4:
:20:SENDER-REF-001
:23B:CRED
:32A:240101KRW50000000,
:50K:/123456789
:59:/987654321
-}"""


class TestCutOffTimeManager:
    def setup_method(self):
        self.manager = CutOffTimeManager()

    def test_check_cutoff_returns_cutoff_result(self):
        result = self.manager.check_cutoff("BOK_KRW_OFFSHORE")
        assert isinstance(result, CutOffResult)

    def test_check_cutoff_has_remaining_minutes(self):
        result = self.manager.check_cutoff("BOK_KRW_OFFSHORE")
        assert isinstance(result.remaining_minutes, int)

    def test_check_cutoff_has_next_value_date(self):
        result = self.manager.check_cutoff("BOK_KRW_OFFSHORE")
        assert isinstance(result.next_value_date, object)

    def test_is_available_returns_bool(self):
        result = self.manager.is_available("BOK_KRW_OFFSHORE")
        assert isinstance(result, bool)

    def test_get_cutoff_time_known(self):
        t = self.manager.get_cutoff_time("BOK_KRW_DOMESTIC")
        assert t == time(16, 30)

    def test_get_cutoff_time_offshore(self):
        t = self.manager.get_cutoff_time("BOK_KRW_OFFSHORE")
        assert t == time(15, 0)

    def test_get_cutoff_time_swift(self):
        t = self.manager.get_cutoff_time("SWIFT_DAILY")
        assert t == time(17, 0)

    def test_get_cutoff_time_unknown(self):
        t = self.manager.get_cutoff_time("UNKNOWN")
        assert t is None

    def test_cutoff_times_defined(self):
        assert "BOK_KRW_DOMESTIC" in self.manager.CUTOFF_TIMES
        assert "BOK_KRW_OFFSHORE" in self.manager.CUTOFF_TIMES
        assert "SWIFT_DAILY" in self.manager.CUTOFF_TIMES
