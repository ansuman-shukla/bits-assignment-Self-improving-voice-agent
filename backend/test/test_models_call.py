"""
Unit tests for Call Pydantic models
Tests validation logic without any database or API calls
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models.call import (
    CallRequest,
    CallResponse,
    CallRecord,
    CallsResponse,
    TranscriptMessage,
    TranscriptResponse,
    Country,
)


class TestCallRequest:
    """Tests for CallRequest model"""

    def _valid_payload(self, **overrides):
        payload = {
            "phone_number": "9262561716",
            "country_code": "+91",
            "name": "Jayden",
            "amount": 1250.75,
        }
        payload.update(overrides)
        return payload

    def test_valid_request(self):
        """A valid call request should construct successfully"""
        req = CallRequest(**self._valid_payload())
        assert req.phone_number == "9262561716"
        assert req.amount == 1250.75

    def test_transfer_to_optional(self):
        """transfer_to should be optional and default to None"""
        req = CallRequest(**self._valid_payload())
        assert req.transfer_to is None

    def test_transfer_to_provided(self):
        """transfer_to should be stored when provided"""
        req = CallRequest(**self._valid_payload(transfer_to="+916203834111"))
        assert req.transfer_to == "+916203834111"

    def test_missing_phone_number_rejected(self):
        """Missing phone_number should be rejected"""
        payload = self._valid_payload()
        del payload["phone_number"]
        with pytest.raises(ValidationError):
            CallRequest(**payload)

    def test_missing_country_code_rejected(self):
        """Missing country_code should be rejected"""
        payload = self._valid_payload()
        del payload["country_code"]
        with pytest.raises(ValidationError):
            CallRequest(**payload)

    def test_missing_name_rejected(self):
        """Missing name should be rejected"""
        payload = self._valid_payload()
        del payload["name"]
        with pytest.raises(ValidationError):
            CallRequest(**payload)

    def test_missing_amount_rejected(self):
        """Missing amount should be rejected"""
        payload = self._valid_payload()
        del payload["amount"]
        with pytest.raises(ValidationError):
            CallRequest(**payload)

    def test_amount_can_be_zero(self):
        """Amount of 0 should be accepted (no gt constraint)"""
        req = CallRequest(**self._valid_payload(amount=0))
        assert req.amount == 0

    def test_amount_can_be_negative(self):
        """Negative amount should be accepted (no ge/gt constraint on amount)"""
        req = CallRequest(**self._valid_payload(amount=-100.0))
        assert req.amount == -100.0


class TestCallResponse:
    """Tests for CallResponse model"""

    def test_minimal_response(self):
        """Only required fields (success, message) need to be provided"""
        resp = CallResponse(success=True, message="Call dispatched")
        assert resp.success is True
        assert resp.message == "Call dispatched"
        assert resp.call_id is None
        assert resp.room is None
        assert resp.dispatch_id is None
        assert resp.error is None

    def test_full_response(self):
        """A full response with all fields should construct"""
        resp = CallResponse(
            success=True,
            message="ok",
            call_id="call123",
            room="outbound-123",
            dispatch_id="dispatch456",
        )
        assert resp.call_id == "call123"
        assert resp.room == "outbound-123"
        assert resp.dispatch_id == "dispatch456"

    def test_error_response(self):
        """An error response should construct"""
        resp = CallResponse(success=False, message="failed", error="Timeout")
        assert resp.success is False
        assert resp.error == "Timeout"


class TestCallRecord:
    """Tests for CallRecord model"""

    def _valid_payload(self, **overrides):
        payload = {
            "call_id": "call123",
            "room_name": "outbound-123",
            "dispatch_id": "dispatch456",
            "name": "Jayden",
            "phone_number": "9262561716",
            "country_code": "+91",
            "amount": 1250.75,
            "status": "in_progress",
            "created_at": datetime(2025, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
        }
        payload.update(overrides)
        return payload

    def test_valid_record(self):
        """A valid call record should construct"""
        record = CallRecord(**self._valid_payload())
        assert record.call_id == "call123"
        assert record.status == "in_progress"

    def test_optional_fields_default_none(self):
        """Optional fields should default to None"""
        record = CallRecord(**self._valid_payload())
        assert record.completed_at is None
        assert record.transcript_file is None
        assert record.transfer_to is None

    def test_completed_record(self):
        """A completed record with all optional fields should construct"""
        record = CallRecord(**self._valid_payload(
            status="completed",
            completed_at=datetime(2025, 10, 4, 12, 5, 0, tzinfo=timezone.utc),
            transcript_file="transcript_outbound-123_20251004_120000.json",
        ))
        assert record.status == "completed"
        assert record.completed_at is not None
        assert record.transcript_file is not None


class TestCallsResponse:
    """Tests for CallsResponse model"""

    def test_empty_response(self):
        """An empty calls response should construct"""
        resp = CallsResponse(calls=[], total=0)
        assert resp.calls == []
        assert resp.total == 0

    def test_response_with_calls(self):
        """A response with calls should construct"""
        record = CallRecord(**{
            "call_id": "call1",
            "room_name": "room1",
            "dispatch_id": "disp1",
            "name": "Test",
            "phone_number": "123",
            "country_code": "+1",
            "amount": 100.0,
            "status": "completed",
            "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        })
        resp = CallsResponse(calls=[record], total=1)
        assert len(resp.calls) == 1
        assert resp.total == 1


class TestTranscriptMessage:
    """Tests for TranscriptMessage model (call.py version)"""

    def test_valid_message(self):
        """A valid transcript message should construct"""
        msg = TranscriptMessage(role="agent", message="Hello there")
        assert msg.role == "agent"
        assert msg.message == "Hello there"

    def test_timestamp_optional(self):
        """Timestamp should be optional"""
        msg = TranscriptMessage(role="user", message="Hi")
        assert msg.timestamp is None

    def test_timestamp_provided(self):
        """Timestamp should be stored when provided"""
        msg = TranscriptMessage(role="user", message="Hi", timestamp="2025-10-04T12:00:00Z")
        assert msg.timestamp == "2025-10-04T12:00:00Z"


class TestTranscriptResponse:
    """Tests for TranscriptResponse model"""

    def _valid_payload(self, **overrides):
        payload = {
            "call_id": "call123",
            "room_name": "outbound-123",
            "name": "Jayden",
            "phone_number": "9262561716",
            "country_code": "+91",
            "amount": 1250.75,
            "status": "completed",
            "created_at": datetime(2025, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
            "transcript": [],
        }
        payload.update(overrides)
        return payload

    def test_valid_response(self):
        """A valid transcript response should construct"""
        resp = TranscriptResponse(**self._valid_payload())
        assert resp.call_id == "call123"
        assert resp.transcript == []

    def test_optional_scores_default_none(self):
        """All risk scores should default to None"""
        resp = TranscriptResponse(**self._valid_payload())
        assert resp.loan_recovery_score is None
        assert resp.willingness_to_pay_score is None
        assert resp.escalation_risk_score is None
        assert resp.customer_sentiment_score is None
        assert resp.promise_to_pay_reliability_index is None

    def test_response_with_scores(self):
        """A response with risk scores should construct"""
        resp = TranscriptResponse(**self._valid_payload(
            loan_recovery_score=75.5,
            willingness_to_pay_score=60.0,
            escalation_risk_score=80.0,
            customer_sentiment_score=55.0,
            promise_to_pay_reliability_index=70.0,
        ))
        assert resp.loan_recovery_score == 75.5
        assert resp.willingness_to_pay_score == 60.0

    def test_response_with_transcript_messages(self):
        """A response with transcript messages should construct"""
        messages = [
            TranscriptMessage(role="agent", message="Hello"),
            TranscriptMessage(role="user", message="Hi"),
        ]
        resp = TranscriptResponse(**self._valid_payload(transcript=messages))
        assert len(resp.transcript) == 2
        assert resp.transcript[0].role == "agent"


class TestCountry:
    """Tests for Country model"""

    def test_valid_country(self):
        """A valid country should construct"""
        country = Country(code="+91", name="India", flag="🇮🇳", iso="IN")
        assert country.code == "+91"
        assert country.name == "India"
        assert country.flag == "🇮🇳"
        assert country.iso == "IN"

    def test_missing_field_rejected(self):
        """Missing any field should be rejected"""
        with pytest.raises(ValidationError):
            Country(code="+91", name="India", flag="🇮🇳")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
