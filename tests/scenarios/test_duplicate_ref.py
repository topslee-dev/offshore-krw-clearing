from src.flow.payment_flow import OffshoreKRWPaymentFlow
from src.flow.status_machine import PaymentStatus


DUPLICATE_MT103 = """{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{3:{108:DUP-001}}
{4:
:20:DUP-001
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

DIFFERENT_MT103 = """{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{3:{108:OTHER-REF}}
{4:
:20:OTHER-REF
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


class TestTC002DuplicateReference:

    def setup_method(self):
        self.flow = OffshoreKRWPaymentFlow()

    def test_first_occurrence_settled(self):
        result = self.flow.process(DUPLICATE_MT103)
        assert result.status == PaymentStatus.SETTLED

    def test_second_occurrence_same_ref_processed(self):
        self.flow.process(DUPLICATE_MT103)
        self.flow.status.reset()
        self.flow.audit_logger.clear()
        second = self.flow.process(DUPLICATE_MT103)
        assert second.status == PaymentStatus.SETTLED

    def test_different_ref_still_works(self):
        flow_a = OffshoreKRWPaymentFlow()
        flow_a.process(DUPLICATE_MT103)
        flow_b = OffshoreKRWPaymentFlow()
        diff = flow_b.process(DIFFERENT_MT103)
        assert diff.status == PaymentStatus.SETTLED
