"""
Unit tests for tuning_service logic with mocked database.

Tests the weighted average calculation and schema builders without any real
database or API calls. All database access is mocked.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId

from models.tuning_loop import ScenarioWeight
from services.tuning_service import (
    calculate_weighted_average,
    create_writer_schema,
    create_critique_schema,
)


def make_eval_doc(scenario_id, task_completion, conversation_efficiency, status="COMPLETED"):
    """Helper to build a fake evaluation document as returned by MongoDB."""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "scenario_id": scenario_id,
        "status": status,
        "scores": {
            "task_completion": task_completion,
            "conversation_efficiency": conversation_efficiency,
        },
    }


class TestCalculateWeightedAverage:
    """Tests for calculate_weighted_average with mocked DB"""

    @pytest.mark.asyncio
    async def test_single_evaluation(self):
        """A single evaluation's weighted score is its average score"""
        collection = MagicMock()
        collection.find_one = AsyncMock(
            return_value=make_eval_doc("scen1", 80, 70)
        )
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            score = await calculate_weighted_average(
                evaluation_ids=["507f1f77bcf86cd799439011"],
                scenario_weights=[ScenarioWeight(scenario_id="scen1", weight=3)],
            )
        # (80 + 70) / 2 = 75.0
        assert score == 75.0

    @pytest.mark.asyncio
    async def test_two_evaluations_weighted(self):
        """Two evaluations with different weights should compute correctly"""
        collection = MagicMock()
        collection.find_one = AsyncMock(
            side_effect=[
                make_eval_doc("scen1", 80, 70),  # avg=75, weight=4 -> 300
                make_eval_doc("scen2", 60, 80),  # avg=70, weight=2 -> 140
            ]
        )
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            score = await calculate_weighted_average(
                evaluation_ids=["eval1", "eval2"],
                scenario_weights=[
                    ScenarioWeight(scenario_id="scen1", weight=4),
                    ScenarioWeight(scenario_id="scen2", weight=2),
                ],
            )
        # (300 + 140) / (4 + 2) = 440 / 6 = 73.33
        assert score == round(440 / 6, 2)

    @pytest.mark.asyncio
    async def test_equal_weights(self):
        """Equal weights should produce a simple average of the per-eval averages"""
        collection = MagicMock()
        collection.find_one = AsyncMock(
            side_effect=[
                make_eval_doc("scen1", 90, 90),  # avg=90
                make_eval_doc("scen2", 70, 70),  # avg=70
            ]
        )
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            score = await calculate_weighted_average(
                evaluation_ids=["e1", "e2"],
                scenario_weights=[
                    ScenarioWeight(scenario_id="scen1", weight=3),
                    ScenarioWeight(scenario_id="scen2", weight=3),
                ],
            )
        # (90*3 + 70*3) / 6 = 80.0
        assert score == 80.0

    @pytest.mark.asyncio
    async def test_higher_weight_dominates(self):
        """A scenario with a much higher weight should dominate the average"""
        collection = MagicMock()
        collection.find_one = AsyncMock(
            side_effect=[
                make_eval_doc("scen1", 100, 100),  # avg=100, weight=5 -> 500
                make_eval_doc("scen2", 0, 0),      # avg=0, weight=1 -> 0
            ]
        )
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            score = await calculate_weighted_average(
                evaluation_ids=["e1", "e2"],
                scenario_weights=[
                    ScenarioWeight(scenario_id="scen1", weight=5),
                    ScenarioWeight(scenario_id="scen2", weight=1),
                ],
            )
        # 500 / 6 = 83.33
        assert score == round(500 / 6, 2)

    @pytest.mark.asyncio
    async def test_evaluation_not_found_raises(self):
        """If an evaluation is not found, a ValueError should be raised"""
        collection = MagicMock()
        collection.find_one = AsyncMock(return_value=None)
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            with pytest.raises(ValueError, match="Evaluation not found"):
                await calculate_weighted_average(
                    evaluation_ids=["missing"],
                    scenario_weights=[ScenarioWeight(scenario_id="scen1", weight=3)],
                )

    @pytest.mark.asyncio
    async def test_incomplete_evaluation_raises(self):
        """An evaluation that is not COMPLETED should raise a ValueError"""
        collection = MagicMock()
        collection.find_one = AsyncMock(
            return_value=make_eval_doc("scen1", 80, 70, status="RUNNING")
        )
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            with pytest.raises(ValueError, match="not completed"):
                await calculate_weighted_average(
                    evaluation_ids=["e1"],
                    scenario_weights=[ScenarioWeight(scenario_id="scen1", weight=3)],
                )

    @pytest.mark.asyncio
    async def test_evaluation_without_scores_raises(self):
        """An evaluation without scores should raise a ValueError"""
        doc = make_eval_doc("scen1", 80, 70)
        doc["scores"] = None
        collection = MagicMock()
        collection.find_one = AsyncMock(return_value=doc)
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            with pytest.raises(ValueError, match="no scores"):
                await calculate_weighted_average(
                    evaluation_ids=["e1"],
                    scenario_weights=[ScenarioWeight(scenario_id="scen1", weight=3)],
                )

    @pytest.mark.asyncio
    async def test_missing_weight_for_scenario_raises(self):
        """If no weight is found for a scenario, a ValueError should be raised"""
        collection = MagicMock()
        collection.find_one = AsyncMock(
            return_value=make_eval_doc("scen_unknown", 80, 70)
        )
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            with pytest.raises(ValueError, match="No weight found"):
                await calculate_weighted_average(
                    evaluation_ids=["e1"],
                    scenario_weights=[ScenarioWeight(scenario_id="scen1", weight=3)],
                )

    @pytest.mark.asyncio
    async def test_rounding_to_two_decimals(self):
        """The result should be rounded to 2 decimal places"""
        collection = MagicMock()
        # avg = (33 + 44) / 2 = 38.5, weight=3 -> 115.5
        collection.find_one = AsyncMock(
            return_value=make_eval_doc("scen1", 33, 44)
        )
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            score = await calculate_weighted_average(
                evaluation_ids=["e1"],
                scenario_weights=[ScenarioWeight(scenario_id="scen1", weight=3)],
            )
        assert score == 38.5

    @pytest.mark.asyncio
    async def test_zero_scores(self):
        """Scores of 0 should produce a weighted average of 0"""
        collection = MagicMock()
        collection.find_one = AsyncMock(
            return_value=make_eval_doc("scen1", 0, 0)
        )
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            score = await calculate_weighted_average(
                evaluation_ids=["e1"],
                scenario_weights=[ScenarioWeight(scenario_id="scen1", weight=3)],
            )
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_perfect_scores(self):
        """Scores of 100 should produce a weighted average of 100"""
        collection = MagicMock()
        collection.find_one = AsyncMock(
            return_value=make_eval_doc("scen1", 100, 100)
        )
        with patch(
            "services.tuning_service.get_evaluations_collection",
            return_value=collection,
        ):
            score = await calculate_weighted_average(
                evaluation_ids=["e1"],
                scenario_weights=[ScenarioWeight(scenario_id="scen1", weight=3)],
            )
        assert score == 100.0


class TestSchemaBuilders:
    """Tests for create_writer_schema and create_critique_schema"""

    def test_writer_schema_returns_object(self):
        schema = create_writer_schema()
        assert schema is not None

    def test_critique_schema_returns_object(self):
        schema = create_critique_schema()
        assert schema is not None

    def test_writer_schema_deterministic(self):
        """Calling twice should both return non-None schemas"""
        assert create_writer_schema() is not None
        assert create_writer_schema() is not None

    def test_critique_schema_deterministic(self):
        assert create_critique_schema() is not None
        assert create_critique_schema() is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
