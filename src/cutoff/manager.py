from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


@dataclass
class CutOffResult:
    is_within: bool
    remaining_minutes: int
    next_value_date: date


class CutOffTimeManager:
    """
    역외원화결제 마감시간 관리자.
    BOK 원화 국내(16:30), BOK 역외원화(15:00), SWIFT 일일 마감(17:00)을 관리한다.
    """

    CUTOFF_TIMES = {
        "BOK_KRW_DOMESTIC": time(16, 30),
        "BOK_KRW_OFFSHORE": time(15, 0),
        "SWIFT_DAILY": time(17, 0),
    }

    def __init__(self, tz_name: str = "Asia/Seoul"):
        self._tz_name = tz_name

    def check_cutoff(self, payment_type: str) -> CutOffResult:
        now = self._now()
        cutoff = self.CUTOFF_TIMES[payment_type]

        is_within = now.time() < cutoff
        remaining = self._calc_remaining(now, cutoff)
        next_value = self._calc_next_value_date(now)

        return CutOffResult(
            is_within=is_within,
            remaining_minutes=remaining,
            next_value_date=next_value,
        )

    def is_available(self, payment_type: str) -> bool:
        return self.check_cutoff(payment_type).is_within

    def get_cutoff_time(self, payment_type: str) -> Optional[time]:
        return self.CUTOFF_TIMES.get(payment_type)

    def _now(self) -> datetime:
        try:
            if ZoneInfo is not None:
                return datetime.now(ZoneInfo(self._tz_name))
        except Exception:
            pass
        return datetime.now(timezone.utc) + timedelta(hours=9)

    def _calc_remaining(self, now: datetime, cutoff: time) -> int:
        cutoff_dt = datetime(now.year, now.month, now.day, cutoff.hour, cutoff.minute, tzinfo=now.tzinfo)
        diff = cutoff_dt - now
        return max(0, int(diff.total_seconds() // 60))

    def _calc_next_value_date(self, now: datetime) -> date:
        next_day = now.date() + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        return next_day
