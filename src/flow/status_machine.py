from enum import Enum


class PaymentStatus(Enum):
    INIT = "INIT"
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    PENDING_BOK = "PENDING_BOK"
    SETTLED = "SETTLED"
    ERROR = "ERROR"
    REPAIR = "REPAIR"


class StatusMachine:
    """
    역외원화결제 상태 머신.
    각 상태에서 허용되는 전이만 수행하며, 잘못된 전이는 ValueError를 발생시킨다.

    상태 전이 규칙:
        INIT → RECEIVED
        RECEIVED → VALIDATED | ERROR
        VALIDATED → PROCESSING | ERROR
        PROCESSING → PENDING_BOK | ERROR
        PENDING_BOK → SETTLED | ERROR
        SETTLED (종료 상태)
        ERROR → REPAIR
        REPAIR → VALIDATED | ERROR
    """

    _TRANSITIONS = {
        PaymentStatus.INIT: {PaymentStatus.RECEIVED},
        PaymentStatus.RECEIVED: {PaymentStatus.VALIDATED, PaymentStatus.ERROR},
        PaymentStatus.VALIDATED: {PaymentStatus.PROCESSING, PaymentStatus.ERROR},
        PaymentStatus.PROCESSING: {PaymentStatus.PENDING_BOK, PaymentStatus.ERROR},
        PaymentStatus.PENDING_BOK: {PaymentStatus.SETTLED, PaymentStatus.ERROR},
        PaymentStatus.SETTLED: set(),
        PaymentStatus.ERROR: {PaymentStatus.REPAIR},
        PaymentStatus.REPAIR: {PaymentStatus.VALIDATED, PaymentStatus.ERROR},
    }

    def __init__(self):
        self._current = PaymentStatus.INIT

    @property
    def current_status(self) -> PaymentStatus:
        return self._current

    def transition(self, target: PaymentStatus) -> PaymentStatus:
        allowed = self._TRANSITIONS.get(self._current, set())
        if target not in allowed:
            raise ValueError(
                f"Cannot transition from {self._current.value} to {target.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        self._current = target
        return self._current

    def can_transition(self, target: PaymentStatus) -> bool:
        return target in self._TRANSITIONS.get(self._current, set())

    def reset(self) -> None:
        self._current = PaymentStatus.INIT
