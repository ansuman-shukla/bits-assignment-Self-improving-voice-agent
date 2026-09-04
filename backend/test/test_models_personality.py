"""
Unit tests for Personality Pydantic models
Tests validation logic without any database or API calls
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models.personality import (
    PersonalityCreate,
    PersonalityUpdate,
    PersonalityResponse,
    PersonalityListResponse,
)


class TestPersonalityCreate:
    """Tests for PersonalityCreate request model"""

    def _valid_payload(self, **overrides):
        payload = {
            "name": "Willful Defaulter",
            "description": "A person who has the means to pay but is avoiding payment",
            "core_traits": {
                "Attitude": "Cynical",
                "Communication Style": "Evasive",
            },
            "system_prompt": "You are a debtor who avoids payment.",
        }
        payload.update(overrides)
        return payload

    def test_valid_create(self):
        """A valid personality create request should construct successfully"""
        p = PersonalityCreate(**self._valid_payload())
        assert p.name == "Willful Defaulter"
        assert p.amount is None

    def test_valid_create_with_amount(self):
        """Creating with an amount should store it"""
        p = PersonalityCreate(**self._valid_payload(amount=5000.0))
        assert p.amount == 5000.0

    def test_name_min_length(self):
        """Empty name should be rejected"""
        with pytest.raises(ValidationError):
            PersonalityCreate(**self._valid_payload(name=""))

    def test_name_max_length(self):
        """Name longer than 100 chars should be rejected"""
        with pytest.raises(ValidationError):
            PersonalityCreate(**self._valid_payload(name="x" * 101))

    def test_description_min_length(self):
        """Empty description should be rejected"""
        with pytest.raises(ValidationError):
            PersonalityCreate(**self._valid_payload(description=""))

    def test_description_max_length(self):
        """Description longer than 500 chars should be rejected"""
        with pytest.raises(ValidationError):
            PersonalityCreate(**self._valid_payload(description="x" * 501))

    def test_system_prompt_min_length(self):
        """System prompt shorter than 10 chars should be rejected"""
        with pytest.raises(ValidationError):
            PersonalityCreate(**self._valid_payload(system_prompt="short"))

    def test_amount_must_be_positive(self):
        """Amount must be greater than 0"""
        with pytest.raises(ValidationError):
            PersonalityCreate(**self._valid_payload(amount=0))
        with pytest.raises(ValidationError):
            PersonalityCreate(**self._valid_payload(amount=-10.0))

    def test_core_traits_required(self):
        """Missing core_traits should be rejected"""
        payload = self._valid_payload()
        del payload["core_traits"]
        with pytest.raises(ValidationError):
            PersonalityCreate(**payload)

    def test_core_traits_accepts_empty_dict(self):
        """An empty dict is a valid Dict[str, str]"""
        p = PersonalityCreate(**self._valid_payload(core_traits={}))
        assert p.core_traits == {}


class TestPersonalityUpdate:
    """Tests for PersonalityUpdate request model"""

    def test_empty_update_accepted(self):
        """All fields optional, empty update accepted"""
        update = PersonalityUpdate()
        assert update.name is None
        assert update.amount is None

    def test_partial_update(self):
        """Updating only some fields should leave others as None"""
        update = PersonalityUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.description is None

    def test_name_min_length_on_update(self):
        """Empty name on update should be rejected"""
        with pytest.raises(ValidationError):
            PersonalityUpdate(name="")

    def test_system_prompt_min_length_on_update(self):
        """Short system prompt on update should be rejected"""
        with pytest.raises(ValidationError):
            PersonalityUpdate(system_prompt="short")

    def test_amount_positive_on_update(self):
        """Amount on update must be positive"""
        with pytest.raises(ValidationError):
            PersonalityUpdate(amount=-1.0)

    def test_amount_zero_rejected_on_update(self):
        """Zero amount on update should be rejected (gt=0)"""
        with pytest.raises(ValidationError):
            PersonalityUpdate(amount=0)


class TestPersonalityResponse:
    """Tests for PersonalityResponse model"""

    def _valid_payload(self, **overrides):
        payload = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "Anxious First-Time Debtor",
            "description": "Nervous about debt",
            "core_traits": {"Attitude": "Fearful"},
            "system_prompt": "You are a person who has just received their first debt notice.",
            "created_at": datetime(2025, 10, 4, 10, 30, 0, tzinfo=timezone.utc),
        }
        payload.update(overrides)
        return payload

    def test_valid_response(self):
        """A valid response should construct successfully"""
        resp = PersonalityResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439011"
        assert resp.name == "Anxious First-Time Debtor"

    def test_populate_by_name(self):
        """The _id alias should populate the id field"""
        resp = PersonalityResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439011"

    def test_id_field_directly(self):
        """populate_by_name allows using 'id' directly"""
        payload = self._valid_payload()
        payload["id"] = payload.pop("_id")
        resp = PersonalityResponse(**payload)
        assert resp.id == "507f1f77bcf86cd799439011"

    def test_optional_amount_defaults_to_none(self):
        """Amount should default to None when not provided"""
        resp = PersonalityResponse(**self._valid_payload())
        assert resp.amount is None

    def test_amount_provided(self):
        """Amount should be stored when provided"""
        resp = PersonalityResponse(**self._valid_payload(amount=7500.0))
        assert resp.amount == 7500.0

    def test_missing_created_at_rejected(self):
        """Missing created_at should be rejected"""
        payload = self._valid_payload()
        del payload["created_at"]
        with pytest.raises(ValidationError):
            PersonalityResponse(**payload)


class TestPersonalityListResponse:
    """Tests for PersonalityListResponse model"""

    def test_empty_list(self):
        """An empty list with total 0 should be accepted"""
        resp = PersonalityListResponse(personalities=[], total=0)
        assert resp.personalities == []
        assert resp.total == 0

    def test_list_with_items(self):
        """A list with items should be accepted"""
        item = PersonalityResponse(**{
            "_id": "abc",
            "name": "Test",
            "description": "desc",
            "core_traits": {},
            "system_prompt": "A valid system prompt",
            "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        })
        resp = PersonalityListResponse(personalities=[item], total=1)
        assert len(resp.personalities) == 1
        assert resp.total == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
