"""
Unit tests for TuningLoop Pydantic models
Tests validation logic without any database or API calls
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models.tuning_loop import (
    TuningStatus,
    ScenarioWeight,
    TuningConfig,
    TuningIteration,
    TuningLoopCreate,
    TuningLoopResponse,
    TuningLoopStatusResponse,
)


class TestTuningStatus:
    """Tests for TuningStatus enum"""

    def test_pending_value(self):
        assert TuningStatus.PENDING.value == "PENDING"

    def test_running_value(self):
        assert TuningStatus.RUNNING.value == "RUNNING"

    def test_completed_value(self):
        assert TuningStatus.COMPLETED.value == "COMPLETED"

    def test_failed_value(self):
        assert TuningStatus.FAILED.value == "FAILED"

    def test_enum_is_str(self):
        assert isinstance(TuningStatus.PENDING, str)

    def test_from_value(self):
        assert TuningStatus("RUNNING") == TuningStatus.RUNNING


class TestScenarioWeight:
    """Tests for ScenarioWeight model"""

    def test_valid_weight(self):
        sw = ScenarioWeight(scenario_id="scen1", weight=3)
        assert sw.scenario_id == "scen1"
        assert sw.weight == 3

    def test_weight_below_one_rejected(self):
        with pytest.raises(ValidationError):
            ScenarioWeight(scenario_id="scen1", weight=0)

    def test_weight_above_five_rejected(self):
        with pytest.raises(ValidationError):
            ScenarioWeight(scenario_id="scen1", weight=6)

    def test_all_valid_weights(self):
        """Weights 1 through 5 should all be accepted"""
        for w in range(1, 6):
            sw = ScenarioWeight(scenario_id="scen", weight=w)
            assert sw.weight == w

    def test_missing_scenario_id_rejected(self):
        with pytest.raises(ValidationError):
            ScenarioWeight(weight=3)

    def test_missing_weight_rejected(self):
        with pytest.raises(ValidationError):
            ScenarioWeight(scenario_id="scen1")


class TestTuningConfig:
    """Tests for TuningConfig model"""

    def _valid_payload(self, **overrides):
        payload = {
            "target_score": 85.0,
            "max_iterations": 5,
            "scenario_weights": [
                ScenarioWeight(scenario_id="scen1", weight=4),
                ScenarioWeight(scenario_id="scen2", weight=3),
            ],
        }
        payload.update(overrides)
        return payload

    def test_valid_config(self):
        config = TuningConfig(**self._valid_payload())
        assert config.target_score == 85.0
        assert config.max_iterations == 5
        assert len(config.scenario_weights) == 2

    def test_target_score_zero_accepted(self):
        config = TuningConfig(**self._valid_payload(target_score=0))
        assert config.target_score == 0

    def test_target_score_hundred_accepted(self):
        config = TuningConfig(**self._valid_payload(target_score=100))
        assert config.target_score == 100

    def test_target_score_above_hundred_rejected(self):
        with pytest.raises(ValidationError):
            TuningConfig(**self._valid_payload(target_score=150.0))

    def test_target_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            TuningConfig(**self._valid_payload(target_score=-1.0))

    def test_max_iterations_zero_rejected(self):
        with pytest.raises(ValidationError):
            TuningConfig(**self._valid_payload(max_iterations=0))

    def test_max_iterations_above_ten_rejected(self):
        with pytest.raises(ValidationError):
            TuningConfig(**self._valid_payload(max_iterations=11))

    def test_max_iterations_one_accepted(self):
        config = TuningConfig(**self._valid_payload(max_iterations=1))
        assert config.max_iterations == 1

    def test_max_iterations_ten_accepted(self):
        config = TuningConfig(**self._valid_payload(max_iterations=10))
        assert config.max_iterations == 10

    def test_empty_scenario_weights_accepted(self):
        """TuningConfig allows empty scenario_weights (no min_length)"""
        config = TuningConfig(**self._valid_payload(scenario_weights=[]))
        assert config.scenario_weights == []


class TestTuningIteration:
    """Tests for TuningIteration model"""

    def test_valid_iteration(self):
        it = TuningIteration(
            iteration_number=1,
            prompt_id="prompt123",
            evaluation_ids=["eval1", "eval2"],
            weighted_score=78.5,
        )
        assert it.iteration_number == 1
        assert it.weighted_score == 78.5
        assert len(it.evaluation_ids) == 2

    def test_iteration_number_zero_rejected(self):
        with pytest.raises(ValidationError):
            TuningIteration(
                iteration_number=0,
                prompt_id="p",
                evaluation_ids=[],
                weighted_score=50.0,
            )

    def test_weighted_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            TuningIteration(
                iteration_number=1,
                prompt_id="p",
                evaluation_ids=[],
                weighted_score=-1.0,
            )

    def test_weighted_score_above_hundred_rejected(self):
        with pytest.raises(ValidationError):
            TuningIteration(
                iteration_number=1,
                prompt_id="p",
                evaluation_ids=[],
                weighted_score=101.0,
            )

    def test_weighted_score_bounds(self):
        """Scores 0 and 100 should be accepted"""
        for score in (0.0, 100.0):
            it = TuningIteration(
                iteration_number=1,
                prompt_id="p",
                evaluation_ids=[],
                weighted_score=score,
            )
            assert it.weighted_score == score

    def test_empty_evaluation_ids_accepted(self):
        it = TuningIteration(
            iteration_number=1,
            prompt_id="p",
            evaluation_ids=[],
            weighted_score=50.0,
        )
        assert it.evaluation_ids == []


class TestTuningLoopCreate:
    """Tests for TuningLoopCreate request model"""

    def _valid_payload(self, **overrides):
        payload = {
            "initial_prompt_id": "prompt123",
            "target_score": 85.0,
            "max_iterations": 5,
            "scenarios": [ScenarioWeight(scenario_id="scen1", weight=3)],
        }
        payload.update(overrides)
        return payload

    def test_valid_create(self):
        req = TuningLoopCreate(**self._valid_payload())
        assert req.initial_prompt_id == "prompt123"
        assert req.target_score == 85.0

    def test_empty_scenarios_rejected(self):
        """TuningLoopCreate requires at least one scenario (min_length=1)"""
        with pytest.raises(ValidationError):
            TuningLoopCreate(**self._valid_payload(scenarios=[]))

    def test_target_score_bounds(self):
        with pytest.raises(ValidationError):
            TuningLoopCreate(**self._valid_payload(target_score=-1.0))
        with pytest.raises(ValidationError):
            TuningLoopCreate(**self._valid_payload(target_score=101.0))

    def test_max_iterations_bounds(self):
        with pytest.raises(ValidationError):
            TuningLoopCreate(**self._valid_payload(max_iterations=0))
        with pytest.raises(ValidationError):
            TuningLoopCreate(**self._valid_payload(max_iterations=11))

    def test_missing_initial_prompt_id_rejected(self):
        payload = self._valid_payload()
        del payload["initial_prompt_id"]
        with pytest.raises(ValidationError):
            TuningLoopCreate(**payload)


class TestTuningLoopResponse:
    """Tests for TuningLoopResponse model"""

    def _valid_payload(self, **overrides):
        payload = {
            "_id": "507f1f77bcf86cd799439015",
            "status": TuningStatus.COMPLETED,
            "config": TuningConfig(
                target_score=85.0,
                max_iterations=5,
                scenario_weights=[ScenarioWeight(scenario_id="scen1", weight=3)],
            ),
            "created_at": datetime(2025, 10, 4, 11, 0, 0, tzinfo=timezone.utc),
        }
        payload.update(overrides)
        return payload

    def test_valid_response(self):
        resp = TuningLoopResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439015"
        assert resp.status == TuningStatus.COMPLETED

    def test_iterations_default_empty(self):
        """iterations should default to an empty list"""
        resp = TuningLoopResponse(**self._valid_payload())
        assert resp.iterations == []

    def test_optional_fields_default_none(self):
        resp = TuningLoopResponse(**self._valid_payload())
        assert resp.final_prompt_id is None
        assert resp.error_message is None
        assert resp.completed_at is None

    def test_response_with_iterations(self):
        iterations = [
            TuningIteration(
                iteration_number=1,
                prompt_id="p1",
                evaluation_ids=["e1"],
                weighted_score=67.5,
            ),
            TuningIteration(
                iteration_number=2,
                prompt_id="p2",
                evaluation_ids=["e2"],
                weighted_score=86.2,
            ),
        ]
        resp = TuningLoopResponse(**self._valid_payload(
            iterations=iterations,
            final_prompt_id="p2",
            completed_at=datetime(2025, 10, 4, 11, 15, 0, tzinfo=timezone.utc),
        ))
        assert len(resp.iterations) == 2
        assert resp.final_prompt_id == "p2"
        assert resp.completed_at is not None

    def test_failed_status_with_error(self):
        resp = TuningLoopResponse(**self._valid_payload(
            status=TuningStatus.FAILED,
            error_message="Writer-Critique cycle failed",
        ))
        assert resp.status == TuningStatus.FAILED
        assert resp.error_message == "Writer-Critique cycle failed"

    def test_status_from_string(self):
        resp = TuningLoopResponse(**self._valid_payload(status="RUNNING"))
        assert resp.status == TuningStatus.RUNNING

    def test_populate_by_name(self):
        resp = TuningLoopResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439015"


class TestTuningLoopStatusResponse:
    """Tests for TuningLoopStatusResponse model"""

    def test_valid_response_with_all_fields(self):
        resp = TuningLoopStatusResponse(
            tuning_loop_id="abc123",
            status=TuningStatus.RUNNING,
            current_iteration=2,
            latest_score=78.5,
        )
        assert resp.tuning_loop_id == "abc123"
        assert resp.current_iteration == 2
        assert resp.latest_score == 78.5

    def test_optional_fields_default_none(self):
        resp = TuningLoopStatusResponse(
            tuning_loop_id="abc",
            status=TuningStatus.PENDING,
        )
        assert resp.current_iteration is None
        assert resp.latest_score is None

    def test_missing_tuning_loop_id_rejected(self):
        with pytest.raises(ValidationError):
            TuningLoopStatusResponse(status=TuningStatus.PENDING)

    def test_missing_status_rejected(self):
        with pytest.raises(ValidationError):
            TuningLoopStatusResponse(tuning_loop_id="abc")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
