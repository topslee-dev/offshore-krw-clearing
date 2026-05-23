from decimal import Decimal


class MT202Builder:
    """
    MT202 (Cover Payment) 은행간 자금이체 전문 생성기.
    은행 간 원화/외화 자금 이체 메시지를 생성한다.
    """

    def build(self, cover_data: dict) -> str:
        sender_ref = cover_data["sender_ref"]
        related_ref = cover_data["related_ref"]
        value_date = cover_data["value_date"]
        currency = cover_data["currency"]
        amount = self._format_amount(cover_data["amount"])
        sender_bic = cover_data.get("sender_bic", "WOOBURKRSAXXX")
        ordering_institution = cover_data["ordering_institution"]
        beneficiary_institution = cover_data["beneficiary_institution"]

        lines = [
            "{1:F01" + sender_bic + "0000000000}",
            "{2:O202" + self._ensure_terminal(sender_bic) + "}",
            "{4:",
            ":20:" + sender_ref,
            ":21:" + related_ref,
            ":32A:" + value_date + currency + amount + ",",
            ":52A:" + ordering_institution,
            ":58A:" + beneficiary_institution,
            "-}",
        ]

        return "\n".join(lines)

    def _format_amount(self, amount: Decimal) -> str:
        return str(int(amount))

    def _ensure_terminal(self, bic: str) -> str:
        if len(bic) <= 8:
            return bic + "XXX"
        return bic
