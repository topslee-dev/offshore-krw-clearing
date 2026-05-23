from src.flow.payment_flow import OffshoreKRWPaymentFlow
from src.flow.status_machine import PaymentStatus


RAW_MT103 = """{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{3:{108:REF20240101001}}
{4:
:20:SENDER-REF-001
:23B:CRED
:32A:240101KRW50000000,
:50K:/123456789
WOORI BANK SEOUL
:57A:HNBKKRSE
:59:/987654321
KOREA BANK COUNTERPARTY
:70:OFFSHORE KRW PAYMENT TEST
:71A:SHA
-}"""

INVALID_MT103 = "INVALID MESSAGE FORMAT"

MISSING_FIELDS_MT103 = """{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{4:
:20:REF-001
-}"""


class TestOffshoreKRWPaymentFlow:
    def setup_method(self):
        self.flow = OffshoreKRWPaymentFlow()

    def test_process_valid_mt103_returns_settled(self):
        result = self.flow.process(RAW_MT103)
        assert result.status == PaymentStatus.SETTLED

    def test_process_valid_mt103_has_messages(self):
        result = self.flow.process(RAW_MT103)
        assert len(result.all_messages) > 0

    def test_process_valid_mt103_contains_mt103(self):
        result = self.flow.process(RAW_MT103)
        assert any("I103" in m for m in result.all_messages)

    def test_process_valid_mt103_contains_mt900(self):
        result = self.flow.process(RAW_MT103)
        assert any("O900" in m for m in result.all_messages)

    def test_process_valid_mt103_contains_mt910(self):
        result = self.flow.process(RAW_MT103)
        assert any("O910" in m or "MT910" in m for m in result.all_messages)

    def test_process_valid_mt103_contains_mt202(self):
        result = self.flow.process(RAW_MT103)
        assert any("O202" in m or "MT202" in m for m in result.all_messages)

    def test_process_valid_mt103_contains_mt950(self):
        result = self.flow.process(RAW_MT103)
        assert any("I950" in m or "MT950" in m for m in result.all_messages)

    def test_process_invalid_message_returns_error(self):
        result = self.flow.process(INVALID_MT103)
        assert result.status == PaymentStatus.ERROR

    def test_process_invalid_message_has_errors(self):
        result = self.flow.process(INVALID_MT103)
        assert len(result.errors) > 0

    def test_process_missing_fields_returns_error(self):
        result = self.flow.process(MISSING_FIELDS_MT103)
        assert result.status == PaymentStatus.ERROR

    def test_process_logs_audit_records(self):
        self.flow.process(RAW_MT103)
        logs = self.flow.audit_logger.get_logs()
        assert len(logs) >= 5

    def test_process_logs_inbound_mt103(self):
        self.flow.process(RAW_MT103)
        logs = self.flow.audit_logger.get_logs({"mt_type": "MT103", "direction": "INBOUND"})
        assert len(logs) >= 1
