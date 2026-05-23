import random
import time
from decimal import Decimal

from src.parser.block_parser import SWIFTBlockParser
from src.parser.tag_parser import TagParser
from src.parser.bic_validator import BICValidator
from src.builder.mt9xx_builder import MT9xxBuilder
from src.cutoff.manager import CutOffTimeManager
from src.bok_simulator.scenarios import ScenarioEngine


class BOKMessageHandler:

    def __init__(self):
        self.block_parser = SWIFTBlockParser()
        self.tag_parser = TagParser()
        self.bic_validator = BICValidator()
        self.mt9xx_builder = MT9xxBuilder()
        self.cutoff_manager = CutOffTimeManager()
        self.scenarios = ScenarioEngine()
        self._timeout_probability = 0.3
        self._nostro_balance = Decimal("1000000000")

    def handle_mt103(self, raw_message: str) -> dict:
        parsed = self.block_parser.parse(raw_message)
        if not parsed.is_complete:
            return {
                "status": "REJECTED", "error_code": "NAK199",
                "reason": "Invalid message structure", "response": None,
                "processing_time_ms": 0,
            }

        block4 = parsed.block4 or ""
        tags = {t.name: t.value for t in self.tag_parser.extract_tags(block4)}
        ref = tags.get(":20:", "")

        dup_check = self.scenarios.test_scenario("DUPLICATE_REF", raw_message)
        if dup_check.get("error_code") == "ACK299":
            return {
                "status": "DUPLICATE", "error_code": "ACK299",
                "reason": "Duplicate reference", "response": None,
                "processing_time_ms": 0,
            }

        bic = self._extract_bic(parsed)
        if bic and not self.bic_validator.validate(bic):
            self.scenarios.add_to_repair_queue({"message": raw_message, "reason": "INVALID_BIC", "bic": bic})
            return {
                "status": "REJECTED", "error_code": "NAK199",
                "reason": f"Invalid BIC: {bic}", "response": None,
                "processing_time_ms": 0,
            }

        amount_str = tags.get(":32A:", "")[9:] if len(tags.get(":32A:", "")) > 9 else ""
        if amount_str and not self._validate_krw_format(amount_str):
            self.scenarios.add_to_repair_queue({"message": raw_message, "reason": "INVALID_KRW_FORMAT", "amount": amount_str})
            return {
                "status": "REJECTED", "error_code": "NAK199",
                "reason": f"Invalid KRW format: {amount_str}", "response": None,
                "processing_time_ms": 0,
            }

        cutoff = self.cutoff_manager.check_cutoff("BOK_KRW_OFFSHORE")
        if not cutoff.is_within:
            self.scenarios.test_scenario("CUTOFF_EXCEEDED", raw_message)
            return {
                "status": "REJECTED", "error_code": "ACK299",
                "reason": f"Cutoff exceeded. Next value date: {cutoff.next_value_date}",
                "response": None, "processing_time_ms": 0,
            }

        amount = self._parse_amount(amount_str)
        if amount >= self._nostro_balance:
            self.scenarios.test_scenario("NOSTRO_INSUFFICIENT", raw_message)
            return {
                "status": "REJECTED", "error_code": "NAK299",
                "reason": "Nostro balance insufficient",
                "response": None, "processing_time_ms": 0,
            }

        if random.random() < self._timeout_probability:
            self.scenarios.test_scenario("BOK_TIMEOUT", raw_message)
            return {
                "status": "TIMEOUT", "error_code": "TIMEOUT",
                "reason": "BOK gateway timeout", "response": None,
                "processing_time_ms": 30000,
            }

        processing_time = random.uniform(0.5, 2.0)
        time.sleep(processing_time * 0.01)

        mt900 = self.mt9xx_builder.build_mt900({
            "reference": "BOK-900-" + ref[-8:] if len(ref) >= 8 else "BOK-900-001",
            "related_ref": ref,
            "account": "1234567890",
            "value_date": tags.get(":32A:", "999999")[:6],
            "currency": "KRW",
            "amount": amount,
        })

        self._nostro_balance -= amount

        return {
            "status": "ACCEPTED", "error_code": "ACK199",
            "reason": "Processed successfully", "response": mt900,
            "processing_time_ms": int(processing_time * 1000),
        }

    def handle_mt202(self, raw_message: str) -> dict:
        parsed = self.block_parser.parse(raw_message)
        if not parsed.is_complete:
            return {
                "status": "REJECTED", "error_code": "NAK199",
                "reason": "Invalid message structure", "response": None,
                "processing_time_ms": 0,
            }

        block4 = parsed.block4 or ""
        tags = {t.name: t.value for t in self.tag_parser.extract_tags(block4)}
        ref = tags.get(":20:", "")
        amount_str = tags.get(":32A:", "")[9:] if len(tags.get(":32A:", "")) > 9 else ""
        amount = self._parse_amount(amount_str)

        related_ref = tags.get(":21:", "")
        if related_ref:
            for record in self.scenarios.get_repair_queue():
                if related_ref in record.get("message", ""):
                    self.scenarios.test_scenario("AMOUNT_MISMATCH", raw_message)
                    self.scenarios.add_to_repair_queue({
                        "message": raw_message,
                        "reason": "AMOUNT_MISMATCH",
                        "related_ref": related_ref,
                    })
                    return {
                        "status": "REJECTED", "error_code": "NAK299",
                        "reason": f"Amount mismatch with MT103 {related_ref}",
                        "response": None, "processing_time_ms": 0,
                    }

        cutoff = self.cutoff_manager.check_cutoff("BOK_KRW_DOMESTIC")
        if not cutoff.is_within:
            self.scenarios.test_scenario("CUTOFF_EXCEEDED", raw_message)
            return {
                "status": "REJECTED", "error_code": "ACK299",
                "reason": f"Cutoff exceeded. Next value date: {cutoff.next_value_date}",
                "response": None, "processing_time_ms": 0,
            }

        if random.random() < self._timeout_probability:
            self.scenarios.test_scenario("BOK_TIMEOUT", raw_message)
            return {
                "status": "TIMEOUT", "error_code": "TIMEOUT",
                "reason": "BOK gateway timeout", "response": None,
                "processing_time_ms": 30000,
            }

        mt950 = self.mt9xx_builder.build_mt950({
            "reference": "MT950-" + ref[-8:] if len(ref) >= 8 else "MT950-001",
            "account": "KRW-NOSTRO-001",
            "sequence": "1/1",
            "opening_balance": "C" + tags.get(":32A:", "999999")[:6] + "KRW1000000000,",
            "closing_balance": "C" + tags.get(":32A:", "999999")[:6] + "KRW1050000000,",
            "statement_lines": [],
        })

        return {
            "status": "ACCEPTED", "error_code": "ACK199",
            "reason": "Settlement completed", "response": mt950,
            "processing_time_ms": 100,
        }

    def _extract_bic(self, parsed) -> str:
        if parsed.block2:
            raw = parsed.block2.replace("{", "").replace("}", "")
            raw = raw.lstrip("IO")
            raw = raw[3:]
            raw = raw.rstrip("XXX")
            return raw[:8] if len(raw) >= 8 else raw
        return ""

    def _validate_krw_format(self, amount_str: str) -> bool:
        import re
        cleaned = amount_str.replace(",", "")
        return bool(re.match(r"^\d+$", cleaned))

    def _parse_amount(self, amount_str: str) -> Decimal:
        cleaned = amount_str.replace(",", "")
        try:
            return Decimal(cleaned)
        except Exception:
            return Decimal("0")
