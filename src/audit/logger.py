import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AuditRecord:
    timestamp: str
    direction: str
    mt_type: str
    reference: str
    message_hash: str
    raw_message: str
    status: str
    processing_time_ms: Optional[int] = None


class SWIFTAuditLogger:
    """
    금융 규제 요구사항 기반 감사 로그 시스템.
    전문 송수신 이력을 전체 보관하며 SHA-256 해시로 위변조를 방지한다.
    """

    def __init__(self):
        self._records: list[AuditRecord] = []

    def log_message(
        self,
        direction: str,
        mt_type: str,
        raw_message: str,
        status: str,
        reference: str = "",
        processing_time_ms: Optional[int] = None,
    ) -> AuditRecord:
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            direction=direction,
            mt_type=mt_type,
            reference=reference,
            message_hash=self._sha256(raw_message),
            raw_message=raw_message,
            status=status,
            processing_time_ms=processing_time_ms,
        )
        self._records.append(record)
        return record

    def get_logs(self, filters: Optional[dict] = None) -> list[AuditRecord]:
        if not filters:
            return list(self._records)

        result = []
        for r in self._records:
            match = True
            for key, value in filters.items():
                if key == "mt_type" and r.mt_type != value:
                    match = False
                elif key == "direction" and r.direction != value:
                    match = False
                elif key == "status" and r.status != value:
                    match = False
                elif key == "reference" and r.reference != value:
                    match = False
                elif key == "start_date":
                    if r.timestamp < value:
                        match = False
                elif key == "end_date":
                    if r.timestamp > value:
                        match = False
            if match:
                result.append(r)
        return result

    def verify_hash(self, message_id: str) -> bool:
        for record in self._records:
            if record.reference == message_id:
                expected = self._sha256(record.raw_message)
                return record.message_hash == expected
        return False

    def clear(self) -> None:
        self._records.clear()

    def _sha256(self, raw_message: str) -> str:
        return hashlib.sha256(raw_message.encode("utf-8")).hexdigest()
