from decimal import Decimal
from datetime import time
from src.bok_simulator.handlers import BOKMessageHandler


VALID_MT103 = """{1:F01WOOBURKRSAXXX0000000000}
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

INVALID_MT103 = "NOT A SWIFT MESSAGE"

INVALID_BIC_MT103 = """{1:F01INVALID123XXXX0000000000}
{2:I103INVALIDXXXX}
{4:
:20:REF-BIC-001
:23B:CRED
:32A:240101KRW50000000,
:50K:/123456789
:59:/987654321
-}"""

VALID_MT202 = """{1:F01WOOBURKRSAXXX0000000000}
{2:O202WOOBURKRSAXXX}
{4:
:20:COVER-001
:21:MT103-REF-001
:32A:240101KRW50000000,
:52A:WOOBUS33
:58A:HNBKKRSE
-}"""


class TestBOKMessageHandler:
    def setup_method(self):
        self.handler = BOKMessageHandler()
        self.handler._timeout_probability = 0.0
        self.handler._nostro_balance = Decimal("999999999999")
        self.handler.cutoff_manager.CUTOFF_TIMES["BOK_KRW_OFFSHORE"] = time(23, 59)
        self.handler.cutoff_manager.CUTOFF_TIMES["BOK_KRW_DOMESTIC"] = time(23, 59)

    def test_handle_mt103_valid_returns_accepted(self):
        result = self.handler.handle_mt103(VALID_MT103)
        assert result["status"] == "ACCEPTED"
        assert result["error_code"] == "ACK199"

    def test_handle_mt103_has_response(self):
        result = self.handler.handle_mt103(VALID_MT103)
        assert result["response"] is not None
        assert "MT900" in result["response"] or "O900" in result["response"]

    def test_handle_mt103_has_processing_time(self):
        result = self.handler.handle_mt103(VALID_MT103)
        assert result["processing_time_ms"] >= 0

    def test_handle_mt103_invalid_rejected(self):
        result = self.handler.handle_mt103(INVALID_MT103)
        assert result["status"] == "REJECTED"

    def test_handle_mt103_invalid_bic_rejected(self):
        result = self.handler.handle_mt103(INVALID_BIC_MT103)
        assert result["status"] == "REJECTED"
        assert "BIC" in result.get("reason", "")

    def test_handle_mt202_valid_returns_accepted(self):
        result = self.handler.handle_mt202(VALID_MT202)
        assert result["status"] == "ACCEPTED"

    def test_handle_mt202_has_mt950_response(self):
        result = self.handler.handle_mt202(VALID_MT202)
        assert "I950" in result.get("response", "") or "MT950" in result.get("response", "")

    def test_handle_mt202_invalid_rejected(self):
        result = self.handler.handle_mt202(INVALID_MT103)
        assert result["status"] == "REJECTED"

    def test_duplicate_mt103_rejected(self):
        self.handler.handle_mt103(VALID_MT103)
        result = self.handler.handle_mt103(VALID_MT103)
        assert result["status"] == "DUPLICATE"
