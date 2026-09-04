"""
Unit tests for Scenario Pydantic models
Tests validation logic without any database or API calls
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioInDB,
)


class TestScenarioCreate:
    """Tests for ScenarioCreate request model"""

    def test_valid_scenario_create(self):
        """A valid scenario create request should construct successfully"""
        scenario = ScenarioCreate(
            personality_id="507f1f77bcf86cd799439011",
            brief="just lost their job",
        )
        assert scenario.personality_id == "507f1f77bcf86cd799439011"
        assert scenario.brief == "just lost their job"

    def test_brief_min_length_enforced(self):
        """Empty brief should be rejected (min_length=1)"""
        with pytest.raises(ValidationError):
            ScenarioCreate(personality_id="abc", brief="")

    def test_brief_max_length_enforced(self):
        """Brief longer than 500 chars should be rejected"""
        with pytest.raises(ValidationError):
            ScenarioCreate(personality_id="abc", brief="x" * 501)

    def test_brief_at_max_length_accepted(self):
        """Brief of exactly 500 chars should be accepted"""
        scenario = ScenarioCreate(personality_id="abc", brief="x" * 500)
        assert len(scenario.brief) == 500

    def test_missing_personality_id_rejected(self):
        """Missing personality_id should be rejected"""
        with pytest.raises(ValidationError):
            ScenarioCreate(brief="some brief")

    def test_missing_brief_rejected(self):
        """Missing brief should be rejected"""
        with pytest.raises(ValidationError):
            ScenarioCreate(personality_id="abc")


class TestScenarioUpdate:
    """Tests for ScenarioUpdate request model"""

    def test_empty_update_accepted(self):
        """All fields optional, so empty update should be accepted"""
        update = ScenarioUpdate()
        assert update.backstory is None
        assert update.weight is None

    def test_backstory_min_length(self):
        """Backstory shorter than 10 chars should be rejected"""
        with pytest.raises(ValidationError):
            ScenarioUpdate(backstory="short")

    def test_backstory_at_min_length(self):
        """Backstory of exactly 10 chars should be accepted"""
        update = ScenarioUpdate(backstory="0123456789")
        assert update.backstory == "0123456789"

    def test_backstory_max_length(self):
        """Backstory longer than 2000 chars should be rejected"""
        with pytest.raises(ValidationError):
            ScenarioUpdate(backstory="x" * 2001)

    def test_weight_minimum(self):
        """Weight below 1 should be rejected"""
        with pytest.raises(ValidationError):
            ScenarioUpdate(weight=0)

    def test_weight_maximum(self):
        """Weight above 5 should be rejected"""
        with pytest.raises(ValidationError):
            ScenarioUpdate(weight=6)

    def test_weight_valid_bounds(self):
        """Weights 1 through 5 should all be accepted"""
        for w in range(1, 6):
            update = ScenarioUpdate(weight=w)
            assert update.weight == w

    def test_partial_update_backstory_only(self):
        """Updating only backstory should leave weight as None"""
        update = ScenarioUpdate(backstory="A valid backstory that is long enough.")
        assert update.backstory is not None
        assert update.weight is None

    def test_partial_update_weight_only(self):
        """Updating only weight should leave backstory as None"""
        update = ScenarioUpdate(weight=4)
        assert update.weight == 4
        assert update.backstory is None


class TestScenarioResponse:
    """Tests for ScenarioResponse model"""

    def _valid_payload(self, **overrides):
        payload = {
            "_id": "507f1f77bcf86cd799439011",
            "personality_id": "507f1f77bcf86cd799439012",
            "title": "Anxious Debtor",
            "brief": "just received their first-ever debt notice",
            "backstory": "This debtor has never been in debt before.",
            "objective": "Seek clarification on the debt",
            "weight": 4,
            "created_at": datetime(2025, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
        }
        payload.update(overrides)
        return payload

    def test_valid_response(self):
        """A fully valid response should construct successfully"""
        resp = ScenarioResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439011"
        assert resp.title == "Anxious Debtor"
        assert resp.weight == 4

    def test_populate_by_name_with_underscore_id(self):
        """The _id alias should populate the id field"""
        resp = ScenarioResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439011"

    def test_populate_by_name_with_id_field(self):
        """populate_by_name allows using 'id' directly too"""
        payload = self._valid_payload()
        payload["id"] = payload.pop("_id")
        resp = ScenarioResponse(**payload)
        assert resp.id == "507f1f77bcf86cd799439011"

    def test_weight_default_not_applied_when_provided(self):
        """Weight default of 3 should not override an explicitly provided value"""
        resp = ScenarioResponse(**self._valid_payload(weight=5))
        assert resp.weight == 5

    def test_weight_out_of_range_rejected(self):
        """Weight outside 1-5 should be rejected"""
        with pytest.raises(ValidationError):
            ScenarioResponse(**self._valid_payload(weight=0))
        with pytest.raises(ValidationError):
            ScenarioResponse(**self._valid_payload(weight=6))

    def test_missing_required_field_rejected(self):
        """Missing a required field should be rejected"""
        payload = self._valid_payload()
        del payload["title"]
        with pytest.raises(ValidationError):
            ScenarioResponse(**payload)


class TestScenarioInDB:
    """Tests for ScenarioInDB internal model"""

    def test_default_weight(self):
        """ScenarioInDB should default weight to 3 when not provided"""
        record = ScenarioInDB(
            personality_id="pid",
            title="Title",
            brief="brief",
            backstory="backstory",
            objective="objective",
            created_at=datetime(2025, 10, 4, tzinfo=timezone.utc),
        )
        assert record.weight == 3

    def test_explicit_weight(self):
        """ScenarioInDB should accept an explicit weight"""
        record = ScenarioInDB(
            personality_id="pid",
            title="Title",
            brief="brief",
            backstory="backstory",
            objective="objective",
            weight=5,
            created_at=datetime(2025, 10, 4, tzinfo=timezone.utc),
        )
        assert record.weight == 5

    def test_missing_created_at_rejected(self):
        """Missing created_at should be rejected"""
        with pytest.raises(ValidationError):
            ScenarioInDB(
                personality_id="pid",
                title="Title",
                brief="brief",
                backstory="backstory",
                objective="objective",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
