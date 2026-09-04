"""
Unit tests for Prompt Pydantic models
Tests validation logic without any database or API calls
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models.prompt import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptListResponse,
)


class TestPromptCreate:
    """Tests for PromptCreate request model"""

    def _valid_payload(self, **overrides):
        payload = {
            "name": "v1.1-empathetic",
            "prompt_text": "You are an empathetic debt collection agent.",
            "version": "1.1",
        }
        payload.update(overrides)
        return payload

    def test_valid_create(self):
        """A valid prompt create request should construct successfully"""
        p = PromptCreate(**self._valid_payload())
        assert p.name == "v1.1-empathetic"
        assert p.version == "1.1"

    def test_name_min_length(self):
        """Empty name should be rejected"""
        with pytest.raises(ValidationError):
            PromptCreate(**self._valid_payload(name=""))

    def test_name_max_length(self):
        """Name longer than 100 chars should be rejected"""
        with pytest.raises(ValidationError):
            PromptCreate(**self._valid_payload(name="x" * 101))

    def test_prompt_text_min_length(self):
        """Prompt text shorter than 10 chars should be rejected"""
        with pytest.raises(ValidationError):
            PromptCreate(**self._valid_payload(prompt_text="short"))

    def test_prompt_text_at_min_length(self):
        """Prompt text of exactly 10 chars should be accepted"""
        p = PromptCreate(**self._valid_payload(prompt_text="0123456789"))
        assert len(p.prompt_text) == 10

    def test_version_min_length(self):
        """Empty version should be rejected"""
        with pytest.raises(ValidationError):
            PromptCreate(**self._valid_payload(version=""))

    def test_version_max_length(self):
        """Version longer than 50 chars should be rejected"""
        with pytest.raises(ValidationError):
            PromptCreate(**self._valid_payload(version="x" * 51))

    def test_missing_required_fields(self):
        """Missing any required field should be rejected"""
        for field in ("name", "prompt_text", "version"):
            payload = self._valid_payload()
            del payload[field]
            with pytest.raises(ValidationError):
                PromptCreate(**payload)


class TestPromptUpdate:
    """Tests for PromptUpdate request model"""

    def test_empty_update_accepted(self):
        """All fields optional, empty update accepted"""
        update = PromptUpdate()
        assert update.name is None
        assert update.prompt_text is None
        assert update.version is None

    def test_partial_update_name(self):
        """Updating only name should leave others as None"""
        update = PromptUpdate(name="new-name")
        assert update.name == "new-name"
        assert update.prompt_text is None

    def test_name_min_length_on_update(self):
        """Empty name on update should be rejected"""
        with pytest.raises(ValidationError):
            PromptUpdate(name="")

    def test_prompt_text_min_length_on_update(self):
        """Short prompt text on update should be rejected"""
        with pytest.raises(ValidationError):
            PromptUpdate(prompt_text="short")

    def test_version_min_length_on_update(self):
        """Empty version on update should be rejected"""
        with pytest.raises(ValidationError):
            PromptUpdate(version="")


class TestPromptResponse:
    """Tests for PromptResponse model"""

    def _valid_payload(self, **overrides):
        payload = {
            "_id": "507f1f77bcf86cd799439012",
            "name": "v2.1-empathetic",
            "prompt_text": "You are a compassionate debt collection agent.",
            "version": "2.1",
            "created_at": datetime(2025, 10, 4, 10, 30, 0, tzinfo=timezone.utc),
        }
        payload.update(overrides)
        return payload

    def test_valid_response(self):
        """A valid response should construct successfully"""
        resp = PromptResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439012"
        assert resp.version == "2.1"

    def test_populate_by_name(self):
        """The _id alias should populate the id field"""
        resp = PromptResponse(**self._valid_payload())
        assert resp.id == "507f1f77bcf86cd799439012"

    def test_id_field_directly(self):
        """populate_by_name allows using 'id' directly"""
        payload = self._valid_payload()
        payload["id"] = payload.pop("_id")
        resp = PromptResponse(**payload)
        assert resp.id == "507f1f77bcf86cd799439012"

    def test_missing_created_at_rejected(self):
        """Missing created_at should be rejected"""
        payload = self._valid_payload()
        del payload["created_at"]
        with pytest.raises(ValidationError):
            PromptResponse(**payload)

    def test_missing_required_field_rejected(self):
        """Missing a required field should be rejected"""
        for field in ("name", "prompt_text", "version"):
            payload = self._valid_payload()
            del payload[field]
            with pytest.raises(ValidationError):
                PromptResponse(**payload)


class TestPromptListResponse:
    """Tests for PromptListResponse model"""

    def test_empty_list(self):
        """An empty list with total 0 should be accepted"""
        resp = PromptListResponse(prompts=[], total=0)
        assert resp.prompts == []
        assert resp.total == 0

    def test_list_with_items(self):
        """A list with items should be accepted"""
        item = PromptResponse(**{
            "_id": "abc",
            "name": "Test",
            "prompt_text": "A valid prompt text",
            "version": "1.0",
            "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        })
        resp = PromptListResponse(prompts=[item], total=1)
        assert len(resp.prompts) == 1
        assert resp.total == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
