from src.flow.payment_flow import OffshoreKRWPaymentFlow
from src.flow.status_machine import PaymentStatus


SAMPLE_MT103 = """{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{3:{108:TC001-REF}}
{4:
:20:TC001-REF
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


class TestTC001NormalOffshoreKRWPayment:

    def setup_method(self):
        self.flow = OffshoreKRWPaymentFlow()

    def test_full_flow_ends_settled(self):
        result = self.flow.process(SAMPLE_MT103)
        assert result.status == PaymentStatus.SETTLED, (
            f"Expected SETTLED, got {result.status}. Errors: {result.errors}"
        )

    def test_full_flow_generates_all_messages(self):
        result = self.flow.process(SAMPLE_MT103)
        assert len(result.all_messages) == 5, (
            f"Expected 5 messages, got {len(result.all_messages)}"
        )

    def test_full_flow_includes_mt103_to_bok(self):
        result = self.flow.process(SAMPLE_MT103)
        mt103_msgs = [m for m in result.all_messages if "I103" in m or "MT103" in m]
        assert len(mt103_msgs) >= 1

    def test_full_flow_includes_mt900(self):
        result = self.flow.process(SAMPLE_MT103)
        mt900_msgs = [m for m in result.all_messages if "O900" in m]
        assert len(mt900_msgs) == 1

    def test_full_flow_includes_mt910(self):
        result = self.flow.process(SAMPLE_MT103)
        mt910_msgs = [m for m in result.all_messages if "O910" in m]
        assert len(mt910_msgs) == 1

    def test_full_flow_includes_mt202(self):
        result = self.flow.process(SAMPLE_MT103)
        mt202_msgs = [m for m in result.all_messages if "O202" in m]
        assert len(mt202_msgs) == 1

    def test_full_flow_includes_mt950(self):
        result = self.flow.process(SAMPLE_MT103)
        mt950_msgs = [m for m in result.all_messages if "I950" in m]
        assert len(mt950_msgs) == 1

    def test_full_flow_no_errors(self):
        result = self.flow.process(SAMPLE_MT103)
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"

    def test_full_flow_audit_logs_generated(self):
        self.flow.process(SAMPLE_MT103)
        logs = self.flow.audit_logger.get_logs()
        assert len(logs) == 6
        log_types = [(l.direction, l.mt_type) for l in logs]
        expected = [
            ("INBOUND", "MT103"),
            ("OUTBOUND", "MT103"),
            ("INBOUND", "MT900"),
            ("OUTBOUND", "MT910"),
            ("OUTBOUND", "MT202"),
            ("INBOUND", "MT950"),
        ]
        for exp in expected:
            assert exp in log_types, f"Missing log entry: {exp}"

    def test_full_flow_state_machine_trace(self):
        self.flow.process(SAMPLE_MT103)
        assert self.flow.status.current_status == PaymentStatus.SETTLED
