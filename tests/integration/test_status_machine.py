from decimal import Decimal
from src.flow.status_machine import StatusMachine, PaymentStatus


class TestStatusMachine:
    def test_initial_state(self):
        sm = StatusMachine()
        assert sm.current_status == PaymentStatus.INIT

    def test_transition_init_to_received(self):
        sm = StatusMachine()
        sm.transition(PaymentStatus.RECEIVED)
        assert sm.current_status == PaymentStatus.RECEIVED

    def test_transition_full_flow(self):
        sm = StatusMachine()
        sm.transition(PaymentStatus.RECEIVED)
        sm.transition(PaymentStatus.VALIDATED)
        sm.transition(PaymentStatus.PROCESSING)
        sm.transition(PaymentStatus.PENDING_BOK)
        sm.transition(PaymentStatus.SETTLED)
        assert sm.current_status == PaymentStatus.SETTLED

    def test_transition_received_to_error(self):
        sm = StatusMachine()
        sm.transition(PaymentStatus.RECEIVED)
        sm.transition(PaymentStatus.ERROR)
        assert sm.current_status == PaymentStatus.ERROR

    def test_transition_error_to_repair(self):
        sm = StatusMachine()
        sm.transition(PaymentStatus.RECEIVED)
        sm.transition(PaymentStatus.ERROR)
        sm.transition(PaymentStatus.REPAIR)
        assert sm.current_status == PaymentStatus.REPAIR

    def test_transition_repair_to_validated(self):
        sm = StatusMachine()
        sm.transition(PaymentStatus.RECEIVED)
        sm.transition(PaymentStatus.ERROR)
        sm.transition(PaymentStatus.REPAIR)
        sm.transition(PaymentStatus.VALIDATED)
        assert sm.current_status == PaymentStatus.VALIDATED

    def test_invalid_transition_raises(self):
        sm = StatusMachine()
        try:
            sm.transition(PaymentStatus.SETTLED)
            assert False, "Should have raised"
        except ValueError:
            pass

    def test_can_transition_true(self):
        sm = StatusMachine()
        assert sm.can_transition(PaymentStatus.RECEIVED) is True

    def test_can_transition_false(self):
        sm = StatusMachine()
        assert sm.can_transition(PaymentStatus.SETTLED) is False

    def test_reset(self):
        sm = StatusMachine()
        sm.transition(PaymentStatus.RECEIVED)
        sm.reset()
        assert sm.current_status == PaymentStatus.INIT

    def test_settled_has_no_allowed_transitions(self):
        sm = StatusMachine()
        sm.transition(PaymentStatus.RECEIVED)
        sm.transition(PaymentStatus.VALIDATED)
        sm.transition(PaymentStatus.PROCESSING)
        sm.transition(PaymentStatus.PENDING_BOK)
        sm.transition(PaymentStatus.SETTLED)
        assert sm.can_transition(PaymentStatus.ERROR) is False
