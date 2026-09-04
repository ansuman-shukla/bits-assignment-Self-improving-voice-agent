"""
Unit tests for pure helper functions in conversation_moderator service.

These tests cover variable replacement, termination logic, and transcript
formatting without making any API or database calls.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from services.conversation_moderator import (
    replace_variables_in_prompt,
    check_should_terminate,
    format_transcript_for_evaluation,
    HANGUP_KEYWORDS,
    MAX_TURN_PAIRS,
)
from models.evaluation import TranscriptMessage


class TestReplaceVariablesInPrompt:
    """Tests for replace_variables_in_prompt"""

    def test_replace_name_only(self):
        result = replace_variables_in_prompt("Hello {name}", name="John")
        assert result == "Hello John"

    def test_replace_amount_only(self):
        result = replace_variables_in_prompt("You owe {amount}", amount=5000.0)
        assert result == "You owe ₹5,000.00"

    def test_replace_both_variables(self):
        result = replace_variables_in_prompt(
            "Hello {name}, you owe {amount}.", name="Jane", amount=12500.50
        )
        assert result == "Hello Jane, you owe ₹12,500.50."

    def test_no_variables(self):
        result = replace_variables_in_prompt("A generic message.")
        assert result == "A generic message."

    def test_no_args(self):
        result = replace_variables_in_prompt("Hello {name}, you owe {amount}.")
        assert result == "Hello {name}, you owe {amount}."

    def test_multiple_name_occurrences(self):
        result = replace_variables_in_prompt(
            "Dear {name}, calling {name} about debt.", name="Bob"
        )
        assert result == "Dear Bob, calling Bob about debt."

    def test_multiple_amount_occurrences(self):
        result = replace_variables_in_prompt(
            "You owe {amount}. Pay {amount} now.", amount=100.0
        )
        assert result == "You owe ₹100.00. Pay ₹100.00 now."

    def test_amount_integer(self):
        result = replace_variables_in_prompt("Owe {amount}", amount=1000)
        assert result == "Owe ₹1,000.00"

    def test_amount_zero(self):
        result = replace_variables_in_prompt("Owe {amount}", amount=0)
        assert result == "Owe ₹0.00"

    def test_amount_large(self):
        result = replace_variables_in_prompt("Owe {amount}", amount=1000000.0)
        assert result == "Owe ₹1,000,000.00"

    def test_amount_decimal_precision(self):
        result = replace_variables_in_prompt("Owe {amount}", amount=99.999)
        # Formats to 2 decimal places
        assert result == "Owe ₹100.00"

    def test_name_none_leaves_placeholder(self):
        result = replace_variables_in_prompt("Hello {name}", name=None)
        assert result == "Hello {name}"

    def test_amount_none_leaves_placeholder(self):
        result = replace_variables_in_prompt("Owe {amount}", amount=None)
        assert result == "Owe {amount}"

    def test_empty_prompt(self):
        result = replace_variables_in_prompt("", name="X", amount=1.0)
        assert result == ""

    def test_unknown_variable_left_alone(self):
        result = replace_variables_in_prompt(
            "Hello {name}, {unknown_var}", name="X"
        )
        assert result == "Hello X, {unknown_var}"


class TestCheckShouldTerminate:
    """Tests for check_should_terminate"""

    def test_terminate_at_max_turns(self):
        assert check_should_terminate("Hello", MAX_TURN_PAIRS) is True

    def test_not_terminate_before_max(self):
        assert check_should_terminate("Hello", MAX_TURN_PAIRS - 1) is False

    def test_not_terminate_at_zero(self):
        assert check_should_terminate("Hello", 0) is False

    def test_each_hangup_keyword_triggers_termination(self):
        for keyword in HANGUP_KEYWORDS:
            assert check_should_terminate(keyword, 0) is True

    def test_hangup_keyword_case_insensitive(self):
        for keyword in HANGUP_KEYWORDS:
            assert check_should_terminate(keyword.upper(), 0) is True
            assert check_should_terminate(keyword.capitalize(), 0) is True

    def test_hangup_keyword_embedded_in_message(self):
        assert check_should_terminate("I think I'm hanging up now", 0) is True
        assert check_should_terminate("Please don't call me again", 0) is True

    def test_normal_messages_do_not_terminate(self):
        messages = [
            "Hello, how are you?",
            "I want to pay my debt",
            "Can you help me?",
            "Thank you for calling",
            "Let me think about it",
        ]
        for msg in messages:
            assert check_should_terminate(msg, 5) is False

    def test_empty_message_does_not_terminate(self):
        assert check_should_terminate("", 0) is False

    def test_termination_at_exact_max(self):
        """At exactly MAX_TURN_PAIRS, should terminate regardless of message"""
        assert check_should_terminate("normal message", MAX_TURN_PAIRS) is True

    def test_hangup_overrides_normal_at_high_turn(self):
        """Hangup keyword should terminate even at high turn count"""
        assert check_should_terminate("goodbye", MAX_TURN_PAIRS - 1) is True


class TestFormatTranscriptForEvaluation:
    """Tests for format_transcript_for_evaluation (conversation_moderator)"""

    def test_format_basic_transcript(self):
        transcript = [
            TranscriptMessage(speaker="agent", message="Hello."),
            TranscriptMessage(speaker="debtor", message="Hi there."),
        ]
        formatted = format_transcript_for_evaluation(transcript)
        lines = formatted.split("\n")
        assert len(lines) == 2
        assert lines[0] == "AGENT: Hello."
        assert lines[1] == "DEBTOR: Hi there."

    def test_format_empty_transcript(self):
        assert format_transcript_for_evaluation([]) == ""

    def test_format_single_message(self):
        transcript = [TranscriptMessage(speaker="agent", message="Only me.")]
        formatted = format_transcript_for_evaluation(transcript)
        assert formatted == "AGENT: Only me."

    def test_format_speaker_uppercased(self):
        transcript = [TranscriptMessage(speaker="agent", message="msg")]
        assert "AGENT:" in format_transcript_for_evaluation(transcript)

    def test_format_preserves_message_content(self):
        transcript = [
            TranscriptMessage(speaker="debtor", message="I can't pay right now.")
        ]
        formatted = format_transcript_for_evaluation(transcript)
        assert "I can't pay right now." in formatted

    def test_format_long_transcript(self):
        transcript = [
            TranscriptMessage(
                speaker="agent" if i % 2 == 0 else "debtor",
                message=f"Message {i}",
            )
            for i in range(20)
        ]
        formatted = format_transcript_for_evaluation(transcript)
        lines = formatted.split("\n")
        assert len(lines) == 20
        assert lines[0] == "AGENT: Message 0"
        assert lines[19] == "DEBTOR: Message 19"

    def test_format_newlines_in_message_preserved(self):
        transcript = [
            TranscriptMessage(speaker="agent", message="Line 1\nLine 2")
        ]
        formatted = format_transcript_for_evaluation(transcript)
        # The message itself contains a newline; the prefix is on the first line
        assert formatted.startswith("AGENT: Line 1")
        assert "Line 2" in formatted


class TestHangupKeywordsConstant:
    """Tests for the HANGUP_KEYWORDS constant"""

    def test_keywords_is_list(self):
        assert isinstance(HANGUP_KEYWORDS, list)

    def test_keywords_non_empty(self):
        assert len(HANGUP_KEYWORDS) > 0

    def test_all_keywords_are_strings(self):
        for kw in HANGUP_KEYWORDS:
            assert isinstance(kw, str)

    def test_all_keywords_lowercase(self):
        for kw in HANGUP_KEYWORDS:
            assert kw == kw.lower()

    def test_known_keywords_present(self):
        """A few expected keywords should be present"""
        assert "goodbye" in HANGUP_KEYWORDS
        assert "i'm hanging up" in HANGUP_KEYWORDS


class TestMaxTurnPairsConstant:
    """Tests for the MAX_TURN_PAIRS constant"""

    def test_is_positive_integer(self):
        assert isinstance(MAX_TURN_PAIRS, int)
        assert MAX_TURN_PAIRS > 0

    def test_reasonable_value(self):
        """MAX_TURN_PAIRS should be a reasonable conversation length"""
        assert 1 <= MAX_TURN_PAIRS <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
