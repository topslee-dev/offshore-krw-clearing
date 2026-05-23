from src.bok_simulator.scenarios import ScenarioEngine


class TestScenarioEngine:
    def setup_method(self):
        self.engine = ScenarioEngine()

    def test_scenarios_defined(self):
        assert "DUPLICATE_REF" in self.engine.SCENARIOS
        assert "INVALID_BIC" in self.engine.SCENARIOS
        assert "AMOUNT_MISMATCH" in self.engine.SCENARIOS
        assert "CUTOFF_EXCEEDED" in self.engine.SCENARIOS
        assert "INVALID_KRW_FORMAT" in self.engine.SCENARIOS
        assert "BOK_TIMEOUT" in self.engine.SCENARIOS
        assert "NOSTRO_INSUFFICIENT" in self.engine.SCENARIOS

    def test_scenario_count(self):
        assert len(self.engine.SCENARIOS) == 7

    def test_duplicate_ref_first_accepted(self):
        msg = "{1:F01}{2:I103}{4::20:REF-001\n-}"
        result = self.engine.test_scenario("DUPLICATE_REF", msg)
        assert result["error_code"] == "ACK199"

    def test_duplicate_ref_second_rejected(self):
        msg = "{1:F01}{2:I103}{4::20:REF-001\n-}"
        self.engine.test_scenario("DUPLICATE_REF", msg)
        result = self.engine.test_scenario("DUPLICATE_REF", msg)
        assert result["error_code"] == "ACK299"

    def test_duplicate_ref_has_action_ignore(self):
        msg = "{1:F01}{2:I103}{4::20:REF-002\n-}"
        self.engine.test_scenario("DUPLICATE_REF", msg)
        result = self.engine.test_scenario("DUPLICATE_REF", msg)
        assert result["action"] == "IGNORE"

    def test_invalid_bic_returns_nak199(self):
        result = self.engine.test_scenario("INVALID_BIC")
        assert result["error_code"] == "NAK199"
        assert result["repair_required"] is True

    def test_amount_mismatch_returns_escalation(self):
        result = self.engine.test_scenario("AMOUNT_MISMATCH")
        assert result["action"] == "ESCALATION"

    def test_cutoff_exceeded_has_next_value_date(self):
        result = self.engine.test_scenario("CUTOFF_EXCEEDED")
        assert result["action"] == "NEXT_VALUE_DATE"
        assert "next_value_date" in result

    def test_invalid_krw_format_repair_required(self):
        result = self.engine.test_scenario("INVALID_KRW_FORMAT")
        assert result["repair_required"] is True

    def test_bok_timeout_has_retry_count(self):
        result = self.engine.test_scenario("BOK_TIMEOUT")
        assert result["retry_count"] == 1

    def test_nostro_insufficient_alert(self):
        result = self.engine.test_scenario("NOSTRO_INSUFFICIENT")
        assert result["action"] == "LIMIT_ALERT"

    def test_unknown_scenario_returns_error(self):
        result = self.engine.test_scenario("UNKNOWN")
        assert "error" in result

    def test_repair_queue_add_and_get(self):
        self.engine.add_to_repair_queue({"message": "test", "reason": "ERROR"})
        queue = self.engine.get_repair_queue()
        assert len(queue) == 1
        assert queue[0]["reason"] == "ERROR"

    def test_repair_queue_clear(self):
        self.engine.add_to_repair_queue({"message": "test", "reason": "ERROR"})
        self.engine.clear_repair_queue()
        assert len(self.engine.get_repair_queue()) == 0

    def test_is_processed(self):
        msg = "{1:F01}{2:I103}{4::20:REF-003\n-}"
        self.engine.test_scenario("DUPLICATE_REF", msg)
        assert self.engine.is_processed("REF-003") is True

    def test_is_not_processed(self):
        assert self.engine.is_processed("NONEXISTENT") is False

    def test_reset(self):
        msg = "{1:F01}{2:I103}{4::20:REF-004\n-}"
        self.engine.test_scenario("DUPLICATE_REF", msg)
        self.engine.reset()
        result = self.engine.test_scenario("DUPLICATE_REF", msg)
        assert result["error_code"] == "ACK199"

    def test_repair_queue_timestamp_added(self):
        self.engine.add_to_repair_queue({"message": "test"})
        assert "timestamp" in self.engine.get_repair_queue()[0]
