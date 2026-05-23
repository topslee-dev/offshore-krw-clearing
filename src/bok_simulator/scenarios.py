import hashlib
from datetime import datetime, timezone
from typing import Optional


class ScenarioEngine:
    """
    한국은행(BOK) 연동 예외 시나리오 시뮬레이션 엔진.
    7가지 예외 상황을 재현하고 처리 결과를 반환한다.
    """

    SCENARIOS = {
        "DUPLICATE_REF": "동일 Reference 중복 전송",
        "INVALID_BIC": "잘못된 BIC 코드",
        "AMOUNT_MISMATCH": "MT103 vs MT202 금액 불일치",
        "CUTOFF_EXCEEDED": "마감시간 초과 전문",
        "INVALID_KRW_FORMAT": "원화 금액 형식 오류",
        "BOK_TIMEOUT": "한국은행 응답 타임아웃",
        "NOSTRO_INSUFFICIENT": "노스트로 계좌 잔액 부족",
    }

    def __init__(self):
        self._processed_refs: set[str] = set()
        self._repair_queue: list[dict] = []

    def test_scenario(self, scenario_key: str, message: Optional[str] = None) -> dict:
        if scenario_key not in self.SCENARIOS:
            return {"error": f"Unknown scenario: {scenario_key}"}

        handler = getattr(self, f"_handle_{scenario_key.lower()}", None)
        if handler is None:
            return {"error": f"No handler for scenario: {scenario_key}"}

        return handler(message)

    def _handle_duplicate_ref(self, message: Optional[str] = None) -> dict:
        ref = self._extract_ref(message or "")
        if ref in self._processed_refs:
            return {
                "error_code": "ACK299",
                "reason": "DUPLICATE_REF",
                "description": self.SCENARIOS["DUPLICATE_REF"],
                "action": "IGNORE",
            }
        self._processed_refs.add(ref)
        return {
            "error_code": "ACK199",
            "reason": "ACCEPTED",
            "description": "First occurrence, processed",
            "action": "PROCESS",
        }

    def _handle_invalid_bic(self, message: Optional[str] = None) -> dict:
        return {
            "error_code": "NAK199",
            "reason": "INVALID_BIC",
            "description": self.SCENARIOS["INVALID_BIC"],
            "action": "REPAIR_QUEUE",
            "repair_required": True,
        }

    def _handle_amount_mismatch(self, message: Optional[str] = None) -> dict:
        return {
            "error_code": "NAK299",
            "reason": "AMOUNT_MISMATCH",
            "description": self.SCENARIOS["AMOUNT_MISMATCH"],
            "action": "ESCALATION",
            "repair_required": True,
        }

    def _handle_cutoff_exceeded(self, message: Optional[str] = None) -> dict:
        return {
            "error_code": "ACK299",
            "reason": "CUTOFF_EXCEEDED",
            "description": self.SCENARIOS["CUTOFF_EXCEEDED"],
            "action": "NEXT_VALUE_DATE",
            "next_value_date": self._next_business_day(),
        }

    def _handle_invalid_krw_format(self, message: Optional[str] = None) -> dict:
        return {
            "error_code": "NAK199",
            "reason": "INVALID_KRW_FORMAT",
            "description": self.SCENARIOS["INVALID_KRW_FORMAT"],
            "action": "REPAIR_QUEUE",
            "repair_required": True,
        }

    def _handle_bok_timeout(self, message: Optional[str] = None) -> dict:
        return {
            "error_code": "TIMEOUT",
            "reason": "BOK_TIMEOUT",
            "description": self.SCENARIOS["BOK_TIMEOUT"],
            "action": "RETRY_QUEUE",
            "retry_count": 1,
            "max_retries": 3,
        }

    def _handle_nostro_insufficient(self, message: Optional[str] = None) -> dict:
        return {
            "error_code": "NAK299",
            "reason": "NOSTRO_INSUFFICIENT",
            "description": self.SCENARIOS["NOSTRO_INSUFFICIENT"],
            "action": "LIMIT_ALERT",
            "repair_required": True,
        }

    def add_to_repair_queue(self, entry: dict) -> None:
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._repair_queue.append(entry)

    def get_repair_queue(self) -> list[dict]:
        return list(self._repair_queue)

    def clear_repair_queue(self) -> None:
        self._repair_queue.clear()

    def is_processed(self, ref: str) -> bool:
        return ref in self._processed_refs

    def reset(self) -> None:
        self._processed_refs.clear()
        self._repair_queue.clear()

    def _extract_ref(self, message: str) -> str:
        import re
        match = re.search(r":20:(\S+)", message)
        return match.group(1) if match else hashlib.md5(message.encode()).hexdigest()[:16]

    def _next_business_day(self) -> str:
        from datetime import timedelta
        today = datetime.now(timezone.utc)
        next_day = today + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        return next_day.strftime("%Y-%m-%d")
