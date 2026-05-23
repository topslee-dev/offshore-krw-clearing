from dataclasses import dataclass, field
from decimal import Decimal

from src.parser.block_parser import SWIFTBlockParser
from src.parser.tag_parser import TagParser
from src.parser.bic_validator import BICValidator
from src.parser.field_validator import FieldValidator
from src.builder.mt103_builder import MT103Builder
from src.builder.mt202_builder import MT202Builder
from src.builder.mt9xx_builder import MT9xxBuilder
from src.flow.status_machine import StatusMachine, PaymentStatus
from src.flow.exchange_processor import ExchangeRateProcessor
from src.cutoff.manager import CutOffTimeManager
from src.audit.logger import SWIFTAuditLogger
from src.bok_simulator.scenarios import ScenarioEngine


@dataclass
class PaymentResult:
    status: PaymentStatus
    all_messages: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class OffshoreKRWPaymentFlow:

    def __init__(self):
        self.block_parser = SWIFTBlockParser()
        self.tag_parser = TagParser()
        self.bic_validator = BICValidator()
        self.field_validator = FieldValidator()
        self.mt103_builder = MT103Builder()
        self.mt202_builder = MT202Builder()
        self.mt9xx_builder = MT9xxBuilder()
        self.exchange_processor = ExchangeRateProcessor()
        self.cutoff_manager = CutOffTimeManager()
        self.scenarios = ScenarioEngine()
        self.status = StatusMachine()
        self.audit_logger = SWIFTAuditLogger()

    def process(self, incoming_mt103: str) -> PaymentResult:
        messages: list[str] = []
        errors: list[str] = []
        warnings: list[str] = []

        parsed = self.block_parser.parse(incoming_mt103)
        self.status.transition(PaymentStatus.RECEIVED)
        self.audit_logger.log_message("INBOUND", "MT103", incoming_mt103, "RECEIVED")

        if not parsed.is_complete:
            self.status.transition(PaymentStatus.ERROR)
            errors.append("Invalid message structure")
            return PaymentResult(status=PaymentStatus.ERROR, all_messages=messages, errors=errors, warnings=warnings)

        block4 = parsed.block4 or ""
        tags = {t.name: t.value for t in self.tag_parser.extract_tags(block4)}

        if block2_info := parsed.block2_info:
            bic = block2_info.receiver_bic if block2_info.receiver_bic else block2_info.receiver_bic
            if bic and not self.bic_validator.validate(bic):
                self.status.transition(PaymentStatus.ERROR)
                errors.append(f"Invalid BIC: {bic}")
                self.scenarios.add_to_repair_queue({
                    "message": incoming_mt103,
                    "reason": "INVALID_BIC",
                    "bic": bic,
                })
                return PaymentResult(status=PaymentStatus.ERROR, all_messages=messages, errors=errors, warnings=warnings)

        cutoff = self.cutoff_manager.check_cutoff("BOK_KRW_OFFSHORE")
        if not cutoff.is_within:
            warnings.append(
                f"Cutoff exceeded for BOK_KRW_OFFSHORE. "
                f"Remaining: {cutoff.remaining_minutes}min. "
                f"Next value date: {cutoff.next_value_date}"
            )

        validation = self.field_validator.validate_mt103(tags)
        if not validation.is_valid:
            self.status.transition(PaymentStatus.ERROR)
            errors.extend(validation.errors)
            for err in validation.errors:
                self.scenarios.add_to_repair_queue({"message": incoming_mt103, "reason": err})
            return PaymentResult(status=PaymentStatus.ERROR, all_messages=messages, errors=errors, warnings=warnings)

        self.status.transition(PaymentStatus.VALIDATED)
        self.status.transition(PaymentStatus.PROCESSING)

        raw_32a = tags.get(":32A:", "999999XXX0")
        currency = raw_32a[6:9] if len(raw_32a) >= 9 else "KRW"
        amount = self._extract_amount(raw_32a)

        if currency != "KRW":
            krw = self.exchange_processor.convert_to_krw(amount, currency, rate_type="FINANCIAL")
            warnings.append(
                f"FX conversion: {amount} {currency} → {krw.krw_amount} KRW "
                f"(rate: {krw.rate}, spread: {krw.spread_applied})"
            )

        sender_bic = (parsed.block1_info.sender_bic
                      if parsed.block1_info and parsed.block1_info.sender_bic
                      else "WOOBURKRSAXXX")

        bok_mt103 = self.mt103_builder.build({
            "sender_ref": tags.get(":20:", ""),
            "value_date": raw_32a[:6],
            "currency": currency,
            "amount": amount,
            "sender_bic": sender_bic,
            "receiver_bic": "HNBKKRSEXXX",
            "ordering_customer": {
                "account": tags.get(":50K:", tags.get(":50F:", "")),
                "name": "",
            },
            "beneficiary_customer": {
                "account": tags.get(":59:", ""),
                "name": "",
            },
            "charge_type": tags.get(":71A:", "SHA"),
        })
        messages.append(bok_mt103)
        self.audit_logger.log_message("OUTBOUND", "MT103", bok_mt103, "FORWARDED_TO_BOK")

        self.status.transition(PaymentStatus.PENDING_BOK)

        mt900_ref = "BOK-900-" + tags.get(":20:", "")[-8:]
        mt900 = self.mt9xx_builder.build_mt900({
            "reference": mt900_ref,
            "related_ref": tags.get(":20:", ""),
            "account": "1234567890",
            "value_date": raw_32a[:6],
            "currency": "KRW",
            "amount": amount,
        })
        messages.append(mt900)
        self.audit_logger.log_message("INBOUND", "MT900", mt900, "RECEIVED")

        mt910_ref = "WOORI-910-" + tags.get(":20:", "")[-8:]
        mt910 = self.mt9xx_builder.build_mt910({
            "reference": mt910_ref,
            "related_ref": tags.get(":20:", ""),
            "account": "1234567890",
            "value_date": raw_32a[:6],
            "currency": "KRW",
            "amount": amount,
        })
        messages.append(mt910)
        self.audit_logger.log_message("OUTBOUND", "MT910", mt910, "SENT")

        mt202 = self.mt202_builder.build({
            "sender_ref": "COVER-" + tags.get(":20:", ""),
            "related_ref": tags.get(":20:", ""),
            "value_date": raw_32a[:6],
            "currency": "KRW",
            "amount": amount,
            "sender_bic": sender_bic,
            "ordering_institution": sender_bic,
            "beneficiary_institution": "HNBKKRSEXXX",
        })
        messages.append(mt202)
        self.audit_logger.log_message("OUTBOUND", "MT202", mt202, "SENT")

        mt950_ref = "MT950-" + tags.get(":20:", "")[-8:]
        mt950 = self.mt9xx_builder.build_mt950({
            "reference": mt950_ref,
            "account": "KRW-NOSTRO-001",
            "sequence": "1/1",
            "opening_balance": "C" + raw_32a[:6] + "KRW1000000000,",
            "closing_balance": "C" + raw_32a[:6] + "KRW1050000000,",
            "statement_lines": [],
        })
        messages.append(mt950)
        self.audit_logger.log_message("INBOUND", "MT950", mt950, "RECEIVED")

        self.status.transition(PaymentStatus.SETTLED)

        return PaymentResult(
            status=PaymentStatus.SETTLED,
            all_messages=messages,
            errors=[],
            warnings=warnings,
        )

    def _extract_amount(self, tag_32a: str) -> Decimal:
        tag_32a = tag_32a.replace(",", "")
        if len(tag_32a) >= 9:
            amount_str = tag_32a[9:]
            try:
                return Decimal(amount_str)
            except Exception:
                return Decimal("0")
        return Decimal("0")
