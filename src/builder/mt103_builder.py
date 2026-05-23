import textwrap
from decimal import Decimal


class MT103Builder:
    """
    MT103 (Customer Credit Transfer) 송금 전문 생성기.
    역외원화결제용 MT103 메시지를 생성한다.
    """

    def build(self, payment_data: dict) -> str:
        sender_ref = payment_data["sender_ref"]
        value_date = payment_data["value_date"]
        currency = payment_data["currency"]
        amount = self._format_amount(payment_data["amount"])
        sender_bic = payment_data["sender_bic"]
        receiver_bic = payment_data["receiver_bic"]
        ordering = payment_data["ordering_customer"]
        beneficiary = payment_data["beneficiary_customer"]
        charge_type = payment_data.get("charge_type", "SHA")

        lines = [
            "{1:F01" + sender_bic + "0000000000}",
            "{2:I103" + self._ensure_terminal(receiver_bic) + "}",
            "{3:{108:" + sender_ref + "}}",
            "{4:",
            ":20:" + sender_ref,
            ":23B:CRED",
            ":32A:" + value_date + currency + amount + ",",
            ":50K:" + ordering["account"],
        ]

        if ordering.get("name"):
            lines.append(ordering["name"].upper())

        if payment_data.get("beneficiary_bank"):
            lines.append(":57A:" + payment_data["beneficiary_bank"])

        lines.append(":59:" + beneficiary["account"])
        if beneficiary.get("name"):
            lines.append(beneficiary["name"].upper())

        if payment_data.get("remittance_info"):
            lines.append(":70:" + payment_data["remittance_info"])

        lines.append(":71A:" + charge_type)
        lines.append("-}")

        return "\n".join(lines)

    def _format_amount(self, amount: Decimal) -> str:
        amount_int = int(amount)
        return str(amount_int)

    def _ensure_terminal(self, bic: str) -> str:
        if len(bic) <= 8:
            return bic + "XXX"
        return bic
