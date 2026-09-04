"""
Unit tests for evaluation_orchestrator logic with mocked database.

Tests the evaluation summary helper and the full evaluation orchestration
with all database and service calls mocked. No real API or DB calls are made.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId

from services.evaluation_orchestrator import (
    perform_full_evaluation,
    get_evaluation_summary,
)
from models.evaluation import TranscriptMessage


class TestGetEvaluationSummary:
    """Tests for get_evaluation_summary with mocked DB"""

    @pytest.mark.asyncio
    async def test_summary_not_found(self):
        """When the evaluation is not found, an error dict should be returned"""
        with patch(
            "services.evaluation_orchestrator.get_evaluation_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await get_evaluation_summary("missing_id")
        assert result["error"] == "Evaluation not found"
        assert result["result_id"] == "missing_id"

    @pytest.mark.asyncio
    async def test_summary_completed_with_scores(self):
        """A completed evaluation with scores should include them in the summary"""
        eval_doc = {
            "_id": "abc123",
            "status": "COMPLETED",
            "prompt_id": "prompt1",
            "scenario_id": "scen1",
            "created_at": "2025-10-04T10:00:00Z",
            "completed_at": "2025-10-04T10:05:00Z",
            "scores": {"task_completion": 85, "conversation_efficiency": 90},
        }
        with patch(
            "services.evaluation_orchestrator.get_evaluation_by_id",
            new_callable=AsyncMock,
            return_value=eval_doc,
        ):
            result = await get_evaluation_summary("abc123")
        assert result["result_id"] == "abc123"
        assert result["status"] == "COMPLETED"
        assert result["scores"]["task_completion"] == 85
        assert "error_message" not in result

    @pytest.mark.asyncio
    async def test_summary_failed_with_error(self):
        """A failed evaluation should include the error message in the summary"""
        eval_doc = {
            "_id": "abc123",
            "status": "FAILED",
            "prompt_id": "prompt1",
            "scenario_id": "scen1",
            "created_at": "2025-10-04T10:00:00Z",
            "completed_at": None,
            "error_message": "Gemini API timeout",
        }
        with patch(
            "services.evaluation_orchestrator.get_evaluation_by_id",
            new_callable=AsyncMock,
            return_value=eval_doc,
        ):
            result = await get_evaluation_summary("abc123")
        assert result["status"] == "FAILED"
        assert result["error_message"] == "Gemini API timeout"
        assert "scores" not in result

    @pytest.mark.asyncio
    async def test_summary_pending_no_scores(self):
        """A pending evaluation should not include scores"""
        eval_doc = {
            "_id": "abc123",
            "status": "PENDING",
            "prompt_id": "prompt1",
            "scenario_id": "scen1",
            "created_at": "2025-10-04T10:00:00Z",
            "completed_at": None,
        }
        with patch(
            "services.evaluation_orchestrator.get_evaluation_by_id",
            new_callable=AsyncMock,
            return_value=eval_doc,
        ):
            result = await get_evaluation_summary("abc123")
        assert result["status"] == "PENDING"
        assert "scores" not in result
        assert "error_message" not in result

    @pytest.mark.asyncio
    async def test_summary_includes_core_fields(self):
        """The summary should always include the core identifying fields"""
        eval_doc = {
            "_id": "abc123",
            "status": "COMPLETED",
            "prompt_id": "prompt1",
            "scenario_id": "scen1",
            "created_at": "2025-10-04T10:00:00Z",
            "completed_at": "2025-10-04T10:05:00Z",
        }
        with patch(
            "services.evaluation_orchestrator.get_evaluation_by_id",
            new_callable=AsyncMock,
            return_value=eval_doc,
        ):
            result = await get_evaluation_summary("abc123")
        for field in ("result_id", "status", "prompt_id", "scenario_id", "created_at", "completed_at"):
            assert field in result


class TestPerformFullEvaluation:
    """Tests for perform_full_evaluation with all dependencies mocked"""

    @pytest.mark.asyncio
    async def test_prompt_not_found_marks_failed(self):
        """If the prompt is not found, the evaluation should be marked FAILED"""
        with patch(
            "services.evaluation_orchestrator.update_evaluation_status",
            new_callable=AsyncMock,
        ) as mock_update, patch(
            "services.evaluation_orchestrator.get_prompt_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "services.evaluation_orchestrator.get_scenario_by_id",
            new_callable=AsyncMock,
            return_value={"title": "S", "objective": "O", "personality_id": "p1"},
        ):
            await perform_full_evaluation("r1", "missing_prompt", "scen1")

        # First call sets RUNNING, second call sets FAILED
        assert mock_update.call_count == 2
        # The second call should set FAILED status (passed as kwarg)
        second_call = mock_update.call_args_list[1]
        assert second_call.kwargs.get("status") == "FAILED"

    @pytest.mark.asyncio
    async def test_scenario_not_found_marks_failed(self):
        """If the scenario is not found, the evaluation should be marked FAILED"""
        with patch(
            "services.evaluation_orchestrator.update_evaluation_status",
            new_callable=AsyncMock,
        ) as mock_update, patch(
            "services.evaluation_orchestrator.get_prompt_by_id",
            new_callable=AsyncMock,
            return_value={"name": "P", "prompt_text": "text"},
        ), patch(
            "services.evaluation_orchestrator.get_scenario_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await perform_full_evaluation("r1", "prompt1", "missing_scen")

        assert mock_update.call_count == 2

    @pytest.mark.asyncio
    async def test_scenario_without_personality_marks_failed(self):
        """If the scenario has no personality_id, the evaluation should fail"""
        with patch(
            "services.evaluation_orchestrator.update_evaluation_status",
            new_callable=AsyncMock,
        ) as mock_update, patch(
            "services.evaluation_orchestrator.get_prompt_by_id",
            new_callable=AsyncMock,
            return_value={"name": "P", "prompt_text": "text"},
        ), patch(
            "services.evaluation_orchestrator.get_scenario_by_id",
            new_callable=AsyncMock,
            return_value={"title": "S", "objective": "O"},  # no personality_id
        ):
            await perform_full_evaluation("r1", "prompt1", "scen1")

        assert mock_update.call_count == 2

    @pytest.mark.asyncio
    async def test_successful_evaluation_flow(self):
        """A full successful evaluation should update status to RUNNING then save results"""
        fake_transcript = [
            TranscriptMessage(speaker="agent", message="Hello"),
            TranscriptMessage(speaker="debtor", message="Hi"),
        ]
        fake_eval_result = {
            "scores": {"task_completion": 80, "conversation_efficiency": 75},
            "evaluator_analysis": "Good empathy.",
        }
        with patch(
            "services.evaluation_orchestrator.update_evaluation_status",
            new_callable=AsyncMock,
        ) as mock_update_status, patch(
            "services.evaluation_orchestrator.update_evaluation_result",
            new_callable=AsyncMock,
        ) as mock_update_result, patch(
            "services.evaluation_orchestrator.get_prompt_by_id",
            new_callable=AsyncMock,
            return_value={"name": "P", "prompt_text": "agent prompt"},
        ), patch(
            "services.evaluation_orchestrator.get_scenario_by_id",
            new_callable=AsyncMock,
            return_value={
                "title": "S",
                "objective": "Negotiate payment",
                "personality_id": "pers1",
            },
        ), patch(
            "core.database.get_personality_by_id",
            new_callable=AsyncMock,
            return_value={
                "name": "John",
                "amount": 5000.0,
                "system_prompt": "debtor prompt",
            },
        ), patch(
            "services.evaluation_orchestrator.run_conversation_simulation",
            new_callable=AsyncMock,
            return_value=fake_transcript,
        ), patch(
            "services.evaluation_orchestrator.evaluate_transcript_dict",
            new_callable=AsyncMock,
            return_value=fake_eval_result,
        ):
            await perform_full_evaluation("r1", "prompt1", "scen1")

        # Status should be set to RUNNING once (no FAILED call on success)
        mock_update_status.assert_called_once_with("r1", "RUNNING")
        # Results should be saved with the transcript and scores
        mock_update_result.assert_called_once()
        call_kwargs = mock_update_result.call_args.kwargs
        assert call_kwargs["evaluation_id"] == "r1"
        assert len(call_kwargs["transcript"]) == 2
        assert call_kwargs["scores"]["task_completion"] == 80

    @pytest.mark.asyncio
    async def test_personality_not_found_marks_failed(self):
        """If the personality is not found, the evaluation should fail"""
        with patch(
            "services.evaluation_orchestrator.update_evaluation_status",
            new_callable=AsyncMock,
        ) as mock_update, patch(
            "services.evaluation_orchestrator.get_prompt_by_id",
            new_callable=AsyncMock,
            return_value={"name": "P", "prompt_text": "text"},
        ), patch(
            "services.evaluation_orchestrator.get_scenario_by_id",
            new_callable=AsyncMock,
            return_value={
                "title": "S",
                "objective": "O",
                "personality_id": "pers1",
            },
        ), patch(
            "core.database.get_personality_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await perform_full_evaluation("r1", "prompt1", "scen1")

        assert mock_update.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
