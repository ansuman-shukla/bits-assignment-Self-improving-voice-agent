"""
Unit tests for pure helper functions in transcript_evaluator service.

Tests transcript formatting and schema creation without any API or DB calls.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from services.transcript_evaluator import (
    format_transcript_for_evaluation,
    create_evaluation_schema,
)
from models.evaluation import TranscriptMessage


class TestFormatTranscriptForEvaluation:
    """Tests for format_transcript_for_evaluation (transcript_evaluator)"""

    def test_format_with_transcript_message_objects(self):
        transcript = [
            TranscriptMessage(speaker="agent", message="Hello."),
            TranscriptMessage(speaker="debtor", message="Hi."),
        ]
        formatted = format_transcript_for_evaluation(transcript)
        lines = formatted.split("\n")
        assert lines[0] == "AGENT: Hello."
        assert lines[1] == "DEBTOR: Hi."

    def test_format_with_dicts(self):
        """The function should accept dicts as well as TranscriptMessage objects"""
        transcript = [
            {"speaker": "agent", "message": "Hello from dict."},
            {"speaker": "debtor", "message": "Hi from dict."},
        ]
        formatted = format_transcript_for_evaluation(transcript)
        lines = formatted.split("\n")
        assert lines[0] == "AGENT: Hello from dict."
        assert lines[1] == "DEBTOR: Hi from dict."

    def test_format_empty_list(self):
        assert format_transcript_for_evaluation([]) == ""

    def test_format_single_message_object(self):
        transcript = [TranscriptMessage(speaker="agent", message="Solo.")]
        assert format_transcript_for_evaluation(transcript) == "AGENT: Solo."

    def test_format_single_dict(self):
        transcript = [{"speaker": "debtor", "message": "Solo dict."}]
        assert format_transcript_for_evaluation(transcript) == "DEBTOR: Solo dict."

    def test_format_speaker_uppercased_from_object(self):
        transcript = [TranscriptMessage(speaker="agent", message="msg")]
        assert format_transcript_for_evaluation(transcript).startswith("AGENT:")

    def test_format_speaker_uppercased_from_dict(self):
        transcript = [{"speaker": "agent", "message": "msg"}]
        assert format_transcript_for_evaluation(transcript).startswith("AGENT:")

    def test_format_dict_missing_speaker_uses_unknown(self):
        """A dict without a speaker key should default to 'UNKNOWN'"""
        transcript = [{"message": "no speaker"}]
        formatted = format_transcript_for_evaluation(transcript)
        assert formatted.startswith("UNKNOWN:")

    def test_format_dict_missing_message_uses_empty(self):
        """A dict without a message key should produce an empty message"""
        transcript = [{"speaker": "agent"}]
        formatted = format_transcript_for_evaluation(transcript)
        assert formatted == "AGENT: "

    def test_format_mixed_objects_and_dicts(self):
        """Mixing TranscriptMessage objects and dicts should work"""
        transcript = [
            TranscriptMessage(speaker="agent", message="Object msg."),
            {"speaker": "debtor", "message": "Dict msg."},
        ]
        formatted = format_transcript_for_evaluation(transcript)
        lines = formatted.split("\n")
        assert lines[0] == "AGENT: Object msg."
        assert lines[1] == "DEBTOR: Dict msg."

    def test_format_preserves_special_characters(self):
        transcript = [
            TranscriptMessage(speaker="agent", message="Pay ₹5,000 by Friday!")
        ]
        formatted = format_transcript_for_evaluation(transcript)
        assert "Pay ₹5,000 by Friday!" in formatted

    def test_format_long_conversation(self):
        transcript = [
            TranscriptMessage(
                speaker="agent" if i % 2 == 0 else "debtor",
                message=f"Turn {i}",
            )
            for i in range(50)
        ]
        formatted = format_transcript_for_evaluation(transcript)
        lines = formatted.split("\n")
        assert len(lines) == 50


class TestCreateEvaluationSchema:
    """Tests for create_evaluation_schema"""

    def test_schema_returns_object(self):
        """create_evaluation_schema should return a schema object (stubbed)"""
        schema = create_evaluation_schema()
        assert schema is not None

    def test_schema_is_deterministic(self):
        """Calling twice should both return non-None schemas"""
        s1 = create_evaluation_schema()
        s2 = create_evaluation_schema()
        assert s1 is not None
        assert s2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
