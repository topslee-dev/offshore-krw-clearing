from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


@dataclass
class KRWAmount:
    original: Decimal
    currency: str
    rate: Decimal
    krw_amount: Decimal
    spread_applied: Optional[Decimal] = None


class ExchangeRateProcessor:
    """
    역외원화 환율 처리 모듈.
    USD/KRW, CNH/KRW 등 외화를 원화로 변환하고 스프레드를 적용한다.
    기준환율 및 재정환율을 지원한다.
    """

    _BASE_RATES: dict[str, Decimal] = {
        "USD": Decimal("1330.50"),
        "CNH": Decimal("184.30"),
        "EUR": Decimal("1450.20"),
        "JPY": Decimal("8.95"),
    }

    _SPREAD_BPS: dict[str, int] = {
        "BASE": 0,
        "FINANCIAL": 30,
    }

    def convert_to_krw(
        self,
        amount: Decimal,
        from_currency: str,
        rate_type: str = "BASE",
    ) -> KRWAmount:
        base_rate = self._get_rate(from_currency, rate_type)
        spread_applied = None

        if rate_type == "FINANCIAL":
            spread_bp = self._SPREAD_BPS.get("FINANCIAL", 0)
            adjusted_rate = self.apply_spread(base_rate, spread_bp)
            spread_applied = adjusted_rate - base_rate
        else:
            adjusted_rate = base_rate

        krw_amount = (amount * adjusted_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return KRWAmount(
            original=amount,
            currency=from_currency,
            rate=adjusted_rate,
            krw_amount=krw_amount,
            spread_applied=spread_applied,
        )

    def apply_spread(self, base_rate: Decimal, spread_bp: int) -> Decimal:
        spread_rate = Decimal(spread_bp) / Decimal("10000")
        return (base_rate * (Decimal("1") + spread_rate)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def calculate_bok_reporting_amount(self, amount: Decimal, currency: str) -> Decimal:
        if currency == "KRW":
            return amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        krw = self.convert_to_krw(amount, currency, rate_type="FINANCIAL")
        return krw.krw_amount

    def set_rate(self, currency: str, rate: Decimal) -> None:
        self._BASE_RATES[currency.upper()] = rate

    def get_rate(self, currency: str) -> Optional[Decimal]:
        return self._BASE_RATES.get(currency.upper())

    def _get_rate(self, currency: str, rate_type: str) -> Decimal:
        return self._BASE_RATES.get(currency.upper(), Decimal("1"))
