"""
Unit tests for Evaluation Pydantic models
Tests validation logic without any database or API calls
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models.evaluation import (
    EvaluationStatus,
    TranscriptMessage,
    EvaluationScores,
    EvaluationCreate,
    EvaluationResponse,
    EvaluationStatusResponse,
)


class TestEvaluationStatus:
    """Tests for EvaluationStatus enum"""

    def test_pending_value(self):
        assert EvaluationStatus.PENDING.value == "PENDING"

    def test_running_value(self):
        assert EvaluationStatus.RUNNING.value == "RUNNING"

    def test_completed_value(self):
        assert EvaluationStatus.COMPLETED.value == "COMPLETED"

    def test_failed_value(self):
        assert EvaluationStatus.FAILED.value == "FAILED"

    def test_enum_is_str(self):
        """EvaluationStatus should be a str enum"""
        assert isinstance(EvaluationStatus.PENDING, str)

    def test_from_value(self):
        """Should be constructable from the string value"""
        assert EvaluationStatus("COMPLETED") == EvaluationStatus.COMPLETED


class TestTranscriptMessage:
    """Tests for TranscriptMessage model (evaluation.py version)"""

    def test_valid_agent_message(self):
        msg = TranscriptMessage(speaker="agent", message="Hello")
        assert msg.speaker == "agent"
        assert msg.message == "Hello"

    def test_valid_debtor_message(self):
        msg = TranscriptMessage(speaker="debtor", message="I can't pay")
        assert msg.speaker == "debtor"

    def test_missing_speaker_rejected(self):
        with pytest.raises(ValidationError):
            TranscriptMessage(message="Hello")

    def test_missing_message_rejected(self):
        with pytest.raises(ValidationError):
            TranscriptMessage(speaker="agent")


class TestEvaluationScores:
    """Tests for EvaluationScores model"""

    def test_valid_scores(self):
        scores = EvaluationScores(task_completion=75, conversation_efficiency=82)
        assert scores.task_completion == 75
        assert scores.conversation_efficiency == 82

    def test_min_scores(self):
        """Scores at the minimum (0) should be accepted"""
        scores = EvaluationScores(task_completion=0, conversation_efficiency=0)
        assert scores.task_completion == 0

    def test_max_scores(self):
        """Scores at the maximum (100) should be accepted"""
        scores = EvaluationScores(task_completion=100, conversation_efficiency=100)
        assert scores.conversation_efficiency == 100

    def test_task_completion_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationScores(task_completion=-1, conversation_efficiency=50)

    def test_task_completion_above_hundred_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationScores(task_completion=101, conversation_efficiency=50)

    def test_conversation_efficiency_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationScores(task_completion=50, conversation_efficiency=-1)

    def test_conversation_efficiency_above_hundred_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationScores(task_completion=50, conversation_efficiency=101)

    def test_missing_field_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationScores(task_completion=50)


class TestEvaluationCreate:
    """Tests for EvaluationCreate request model"""

    def test_valid_create(self):
        req = EvaluationCreate(
            prompt_id="507f1f77bcf86cd799439011",
            scenario_id="507f1f77bcf86cd799439012",
        )
        assert req.prompt_id == "507f1f77bcf86cd799439011"
        assert req.scenario_id == "507f1f77bcf86cd799439012"

    def test_missing_prompt_id_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationCreate(scenario_id="scen123")

    def test_missing_scenario_id_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationCreate(prompt_id="prompt123")


class TestEvaluationResponse:
    """Tests for EvaluationResponse model"""

    def _valid_payload(self, **overrides):
        payload = {
            "_id": "507f1f77bcf86cd799439013",
            "prompt_id": "507f1f77bcf86cd799439011",
            "scenario_id": "507f1f77bcf86cd799439012",
            "status": EvaluationStatus.COMPLETED,
            "created_at": datetime(2025, 10, 4, 10, 30, 0, tzinfo=timezone.utc),
        }
        payload.update(overrides)
        return payload

    def test_valid_minimal_response(self):
        resp = EvaluationResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439013"
        assert resp.status == EvaluationStatus.COMPLETED
        assert resp.transcript is None
        assert resp.scores is None

    def test_populate_by_name(self):
        resp = EvaluationResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439013"

    def test_id_field_directly(self):
        payload = self._valid_payload()
        payload["id"] = payload.pop("_id")
        resp = EvaluationResponse(**payload)
        assert resp.id == "507f1f77bcf86cd799439013"

    def test_response_with_transcript_and_scores(self):
        resp = EvaluationResponse(**self._valid_payload(
            transcript=[
                TranscriptMessage(speaker="agent", message="Hello"),
                TranscriptMessage(speaker="debtor", message="Hi"),
            ],
            scores=EvaluationScores(task_completion=80, conversation_efficiency=70),
            evaluator_analysis="Good empathy shown.",
            completed_at=datetime(2025, 10, 4, 10, 32, 0, tzinfo=timezone.utc),
        ))
        assert len(resp.transcript) == 2
        assert resp.scores.task_completion == 80
        assert resp.evaluator_analysis == "Good empathy shown."
        assert resp.completed_at is not None

    def test_failed_status_with_error(self):
        resp = EvaluationResponse(**self._valid_payload(
            status=EvaluationStatus.FAILED,
            error_message="Gemini API timeout",
        ))
        assert resp.status == EvaluationStatus.FAILED
        assert resp.error_message == "Gemini API timeout"

    def test_status_from_string(self):
        """Status should accept the string value"""
        resp = EvaluationResponse(**self._valid_payload(status="RUNNING"))
        assert resp.status == EvaluationStatus.RUNNING

    def test_missing_status_rejected(self):
        payload = self._valid_payload()
        del payload["status"]
        with pytest.raises(ValidationError):
            EvaluationResponse(**payload)

    def test_missing_created_at_rejected(self):
        payload = self._valid_payload()
        del payload["created_at"]
        with pytest.raises(ValidationError):
            EvaluationResponse(**payload)


class TestEvaluationStatusResponse:
    """Tests for EvaluationStatusResponse model"""

    def test_valid_response(self):
        resp = EvaluationStatusResponse(
            result_id="507f1f77bcf86cd799439013",
            status=EvaluationStatus.PENDING,
        )
        assert resp.result_id == "507f1f77bcf86cd799439013"
        assert resp.status == EvaluationStatus.PENDING

    def test_status_from_string(self):
        resp = EvaluationStatusResponse(result_id="abc", status="COMPLETED")
        assert resp.status == EvaluationStatus.COMPLETED

    def test_missing_result_id_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationStatusResponse(status=EvaluationStatus.PENDING)

    def test_missing_status_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationStatusResponse(result_id="abc")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
