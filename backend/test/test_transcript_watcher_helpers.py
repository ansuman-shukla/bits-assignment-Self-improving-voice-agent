"""
Unit tests for transcript_watcher filename parsing logic.

Tests the regex-based room_name extraction from transcript filenames
without any file system, database, or API calls.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from services.transcript_watcher import (
    TRANSCRIPT_FILENAME_PATTERN,
    TranscriptFileHandler,
)


def make_handler():
    """Create a TranscriptFileHandler without a real event loop."""
    return TranscriptFileHandler(loop=None)


class TestTranscriptFilenamePattern:
    """Tests for the TRANSCRIPT_FILENAME_PATTERN regex"""

    def test_pattern_compiled(self):
        """The pattern should be a compiled regex"""
        assert hasattr(TRANSCRIPT_FILENAME_PATTERN, "match")

    def test_valid_filename_matches(self):
        filename = "transcript_outbound-4986973328_20251003_231604.json"
        match = TRANSCRIPT_FILENAME_PATTERN.match(filename)
        assert match is not None

    def test_valid_filename_extracts_room_name(self):
        filename = "transcript_outbound-4986973328_20251003_231604.json"
        match = TRANSCRIPT_FILENAME_PATTERN.match(filename)
        assert match.group(1) == "outbound-4986973328"

    def test_room_name_with_dashes(self):
        filename = "transcript_outbound-1234567890_20251004_235618.json"
        match = TRANSCRIPT_FILENAME_PATTERN.match(filename)
        assert match.group(1) == "outbound-1234567890"

    def test_phone_number_room_name(self):
        """Room names that are phone numbers (no dashes) should also match"""
        filename = "transcript_919262561716_20251003_150915.json"
        match = TRANSCRIPT_FILENAME_PATTERN.match(filename)
        assert match.group(1) == "919262561716"

    def test_missing_prefix_does_not_match(self):
        match = TRANSCRIPT_FILENAME_PATTERN.match("outbound-123_20251003_231604.json")
        assert match is None

    def test_missing_extension_does_not_match(self):
        match = TRANSCRIPT_FILENAME_PATTERN.match("transcript_outbound-123_20251003_231604")
        assert match is None

    def test_wrong_extension_does_not_match(self):
        match = TRANSCRIPT_FILENAME_PATTERN.match("transcript_outbound-123_20251003_231604.txt")
        assert match is None

    def test_missing_date_does_not_match(self):
        match = TRANSCRIPT_FILENAME_PATTERN.match("transcript_outbound-123.json")
        assert match is None

    def test_malformed_date_does_not_match(self):
        match = TRANSCRIPT_FILENAME_PATTERN.match("transcript_outbound-123_2025100_231604.json")
        assert match is None

    def test_malformed_time_does_not_match(self):
        match = TRANSCRIPT_FILENAME_PATTERN.match("transcript_outbound-123_20251003_23160.json")
        assert match is None

    def test_uppercase_extension_does_not_match(self):
        """The pattern expects lowercase .json"""
        match = TRANSCRIPT_FILENAME_PATTERN.match("transcript_outbound-123_20251003_231604.JSON")
        assert match is None

    def test_extra_prefix_does_not_match(self):
        """Pattern is anchored at start; extra prefix should not match"""
        match = TRANSCRIPT_FILENAME_PATTERN.match("prefix_transcript_outbound-123_20251003_231604.json")
        assert match is None


class TestExtractRoomName:
    """Tests for TranscriptFileHandler._extract_room_name"""

    def test_extract_valid_filename(self):
        handler = make_handler()
        room = handler._extract_room_name("transcript_outbound-4986973328_20251003_231604.json")
        assert room == "outbound-4986973328"

    def test_extract_phone_room_name(self):
        handler = make_handler()
        room = handler._extract_room_name("transcript_919262561716_20251003_150915.json")
        assert room == "919262561716"

    def test_extract_invalid_filename_returns_none(self):
        handler = make_handler()
        assert handler._extract_room_name("random_file.json") is None

    def test_extract_non_json_returns_none(self):
        handler = make_handler()
        assert handler._extract_room_name("transcript_outbound-123_20251003_231604.txt") is None

    def test_extract_empty_string_returns_none(self):
        handler = make_handler()
        assert handler._extract_room_name("") is None

    def test_extract_no_extension_returns_none(self):
        handler = make_handler()
        assert handler._extract_room_name("transcript_outbound-123_20251003_231604") is None

    def test_extract_complex_room_name(self):
        """Room names can contain dashes and digits"""
        handler = make_handler()
        room = handler._extract_room_name("transcript_outbound-9999999999_20251231_235959.json")
        assert room == "outbound-9999999999"

    def test_extract_boundary_date(self):
        """Date 00000000 and time 000000 should still match the pattern"""
        handler = make_handler()
        room = handler._extract_room_name("transcript_room1_00000000_000000.json")
        assert room == "room1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
