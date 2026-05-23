from decimal import Decimal


class MT9xxBuilder:
    """
    MT900 (Debit Note), MT910 (Credit Note),
    MT940 (Customer Statement), MT950 (Bank Statement) 전문 생성기.
    한국은행 연동 시 응답/확인 메시지를 생성한다.
    """

    def build_mt900(self, debit_data: dict) -> str:
        reference = debit_data["reference"]
        related_ref = debit_data["related_ref"]
        account = debit_data["account"]
        value_date = debit_data["value_date"]
        currency = debit_data["currency"]
        amount = self._format_amount(debit_data["amount"])
        sender_bic = debit_data.get("sender_bic", "HNBKKRSEXXX")
        receiver_bic = debit_data.get("receiver_bic", "WOOBURKRSAXXX")

        lines = [
            "{1:F01" + sender_bic + "0000000000}",
            "{2:O900" + sender_bic + "XXX}",
            "{4:",
            ":20:" + reference,
            ":21:" + related_ref,
            ":25:" + account,
            ":32A:" + value_date + currency + amount + ",",
            "-}",
        ]

        return "\n".join(lines)

    def build_mt910(self, credit_data: dict) -> str:
        reference = credit_data["reference"]
        related_ref = credit_data["related_ref"]
        account = credit_data["account"]
        value_date = credit_data["value_date"]
        currency = credit_data["currency"]
        amount = self._format_amount(credit_data["amount"])
        sender_bic = credit_data.get("sender_bic", "WOOBURKRSAXXX")
        receiver_bic = credit_data.get("receiver_bic", "HNBKKRSEXXX")

        lines = [
            "{1:F01" + sender_bic + "0000000000}",
            "{2:O910" + sender_bic + "XXX}",
            "{4:",
            ":20:" + reference,
            ":21:" + related_ref,
            ":25:" + account,
            ":32A:" + value_date + currency + amount + ",",
            "-}",
        ]

        return "\n".join(lines)

    def build_mt940(self, statement_data: dict) -> str:
        reference = statement_data["reference"]
        account = statement_data["account"]
        sequence = statement_data.get("sequence", "1/1")
        opening = statement_data["opening_balance"]
        closing = statement_data["closing_balance"]
        lines_list = statement_data.get("statement_lines", [])
        sender_bic = statement_data.get("sender_bic", "HNBKKRSEXXX")
        receiver_bic = statement_data.get("receiver_bic", "WOOBURKRSAXXX")

        result = [
            "{1:F01" + sender_bic + "0000000000}",
            "{2:I940" + receiver_bic + "XXX}",
            "{4:",
            ":20:" + reference,
            ":25:" + account,
            ":28C:" + sequence,
            ":60F:" + opening,
        ]

        for line in lines_list:
            result.append(":61:" + line)

        result.append(":62F:" + closing)
        result.append("-}")

        return "\n".join(result)

    def build_mt950(self, statement_data: dict) -> str:
        reference = statement_data["reference"]
        account = statement_data["account"]
        sequence = statement_data.get("sequence", "1/1")
        opening = statement_data["opening_balance"]
        closing = statement_data["closing_balance"]
        lines_list = statement_data.get("statement_lines", [])
        sender_bic = statement_data.get("sender_bic", "HNBKKRSEXXX")
        receiver_bic = statement_data.get("receiver_bic", "WOOBURKRSAXXX")

        result = [
            "{1:F01" + sender_bic + "0000000000}",
            "{2:I950" + receiver_bic + "XXX}",
            "{4:",
            ":20:" + reference,
            ":25:" + account,
            ":28C:" + sequence,
            ":60F:" + opening,
        ]

        for line in lines_list:
            result.append(":61:" + line)

        result.append(":62F:" + closing)
        result.append("-}")

        return "\n".join(result)

    def _format_amount(self, amount: Decimal) -> str:
        return str(int(amount))
