from src.audit.logger import SWIFTAuditLogger, AuditRecord


RAW_MT103 = """{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{4:
:20:REF-001
:23B:CRED
:32A:240101KRW50000000,
:50K:/123456789
:59:/987654321
-}"""


class TestSWIFTAuditLogger:
    def setup_method(self):
        self.logger = SWIFTAuditLogger()

    def test_log_message_returns_record(self):
        record = self.logger.log_message("INBOUND", "MT103", RAW_MT103, "RECEIVED")
        assert isinstance(record, AuditRecord)

    def test_log_message_contains_hash(self):
        record = self.logger.log_message("INBOUND", "MT103", RAW_MT103, "RECEIVED")
        assert record.message_hash is not None
        assert len(record.message_hash) == 64

    def test_log_message_contains_timestamp(self):
        record = self.logger.log_message("INBOUND", "MT103", RAW_MT103, "RECEIVED")
        assert record.timestamp is not None

    def test_get_logs_returns_all(self):
        self.logger.log_message("INBOUND", "MT103", RAW_MT103, "RECEIVED")
        self.logger.log_message("OUTBOUND", "MT202", RAW_MT103, "SENT")
        logs = self.logger.get_logs()
        assert len(logs) == 2

    def test_get_logs_filter_by_mt_type(self):
        self.logger.log_message("INBOUND", "MT103", RAW_MT103, "RECEIVED")
        self.logger.log_message("OUTBOUND", "MT202", RAW_MT103, "SENT")
        logs = self.logger.get_logs({"mt_type": "MT103"})
        assert len(logs) == 1
        assert logs[0].mt_type == "MT103"

    def test_get_logs_filter_by_direction(self):
        self.logger.log_message("INBOUND", "MT103", RAW_MT103, "RECEIVED")
        self.logger.log_message("OUTBOUND", "MT202", RAW_MT103, "SENT")
        logs = self.logger.get_logs({"direction": "OUTBOUND"})
        assert len(logs) == 1
        assert logs[0].direction == "OUTBOUND"

    def test_verify_hash_valid(self):
        self.logger.log_message("INBOUND", "MT103", RAW_MT103, "RECEIVED", reference="REF-001")
        assert self.logger.verify_hash("REF-001") is True

    def test_verify_hash_invalid(self):
        assert self.logger.verify_hash("NONEXISTENT") is False

    def test_clear(self):
        self.logger.log_message("INBOUND", "MT103", RAW_MT103, "RECEIVED")
        self.logger.clear()
        assert len(self.logger.get_logs()) == 0
