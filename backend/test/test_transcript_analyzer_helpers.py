"""
Unit tests for transcript_analyzer formatting logic.

Tests the _format_transcript_for_analysis method which converts raw transcript
JSON into formatted text for LLM analysis. No API or DB calls are made.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from services.transcript_analyzer import TranscriptAnalyzer


class TestFormatTranscriptForAnalysis:
    """Tests for TranscriptAnalyzer._format_transcript_for_analysis"""

    def _make_analyzer(self):
        """Create an analyzer instance without calling the real __init__.

        The real __init__ requires a Gemini API key and creates a client. We
        bypass it and create a bare instance so we can test the pure
        formatting method in isolation.
        """
        analyzer = TranscriptAnalyzer.__new__(TranscriptAnalyzer)
        return analyzer

    def test_format_basic_transcript(self):
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": ["Hello, how can I help?"],
                },
                {
                    "type": "message",
                    "role": "user",
                    "content": ["I have a question."],
                },
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0] == "Agent: Hello, how can I help?"
        assert lines[1] == "Customer: I have a question."

    def test_format_empty_items(self):
        analyzer = self._make_analyzer()
        result = analyzer._format_transcript_for_analysis({"items": []})
        assert result == ""

    def test_format_missing_items_key(self):
        analyzer = self._make_analyzer()
        result = analyzer._format_transcript_for_analysis({})
        assert result == ""

    def test_format_assistant_role_labeled_agent(self):
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {"type": "message", "role": "assistant", "content": ["Hi"]},
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        assert result.startswith("Agent:")

    def test_format_user_role_labeled_customer(self):
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {"type": "message", "role": "user", "content": ["Hi"]},
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        assert result.startswith("Customer:")

    def test_format_unknown_role_labeled_customer(self):
        """Any role that isn't 'assistant' should be labeled 'Customer'"""
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {"type": "message", "role": "system", "content": ["Hi"]},
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        assert result.startswith("Customer:")

    def test_format_missing_role_defaults_to_unknown(self):
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {"type": "message", "content": ["No role here"]},
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        assert result.startswith("Customer:")

    def test_format_content_as_string(self):
        """When content is a string instead of a list, it should be used directly"""
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {"type": "message", "role": "assistant", "content": "Plain string content"},
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        assert "Plain string content" in result

    def test_format_content_multiple_parts_joined(self):
        """Multiple content parts should be joined with spaces"""
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": ["Hello", "world", "foo"],
                },
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        assert "Hello world foo" in result

    def test_format_skips_non_message_items(self):
        """Items with type != 'message' should be skipped"""
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {"type": "function_call", "role": "assistant", "content": ["skip"]},
                {"type": "message", "role": "assistant", "content": ["keep"]},
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        assert "keep" in result
        assert "skip" not in result

    def test_format_empty_content_list(self):
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {"type": "message", "role": "assistant", "content": []},
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        # Empty list joined produces empty string
        assert result == "Agent: "

    def test_format_missing_content(self):
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {"type": "message", "role": "assistant"},
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        # Missing content defaults to empty list -> empty string
        assert result == "Agent: "

    def test_format_long_transcript(self):
        analyzer = self._make_analyzer()
        items = [
            {
                "type": "message",
                "role": "assistant" if i % 2 == 0 else "user",
                "content": [f"Message {i}"],
            }
            for i in range(30)
        ]
        result = analyzer._format_transcript_for_analysis({"items": items})
        lines = result.split("\n")
        assert len(lines) == 30

    def test_format_preserves_special_characters(self):
        analyzer = self._make_analyzer()
        data = {
            "items": [
                {
                    "type": "message",
                    "role": "user",
                    "content": ["I owe ₹5,000 — can I pay Friday?"],
                },
            ]
        }
        result = analyzer._format_transcript_for_analysis(data)
        assert "₹5,000" in result
        assert "Friday" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
