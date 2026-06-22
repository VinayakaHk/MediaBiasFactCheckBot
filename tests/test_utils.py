"""Unit tests for src/utils.py"""

import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import (
    is_valid_submission_statement,
    add_prefix_to_paragraphs,
    print_mbfc_text,
    mbfc_political_bias,
)


class TestIsValidSubmissionStatement:
    def test_valid_ss_prefix(self):
        assert is_valid_submission_statement("Submission Statement " + "x" * 200) is True

    def test_valid_ss_short_prefix(self):
        assert is_valid_submission_statement("SS " + "x" * 200) is True

    def test_too_short(self):
        assert is_valid_submission_statement("Submission Statement short") is False

    def test_wrong_prefix(self):
        assert is_valid_submission_statement("This is my comment " + "x" * 200) is False

    def test_case_insensitive(self):
        assert is_valid_submission_statement("submission statement " + "x" * 200) is True

    def test_empty_string(self):
        assert is_valid_submission_statement("") is False


class TestAddPrefixToParagraphs:
    def test_adds_quote_prefix(self):
        result = add_prefix_to_paragraphs("hello\n\nworld")
        assert ">" in result

    def test_handles_empty_string(self):
        assert add_prefix_to_paragraphs("") == ""

    def test_single_paragraph(self):
        result = add_prefix_to_paragraphs("single line")
        assert "single line" in result


class TestPrintMbfcText:
    def test_basic_output(self):
        obj = {
            "name": "BBC News",
            "bias": "LEFT-CENTER",
            "factual": "HIGH",
            "credibility": "HIGH",
            "profile": "https://mediabiasfactcheck.com/bbc/",
        }
        result = print_mbfc_text("bbc.co.uk", obj)
        assert "BBC News" in result
        assert "LEFT-CENTER" in result
        assert "HIGH" in result
        assert "Credibility Rating" in result

    def test_no_credibility(self):
        obj = {
            "name": "Test",
            "bias": "CENTER",
            "factual": "HIGH",
            "credibility": "no credibility rating available",
            "profile": "https://example.com",
        }
        result = print_mbfc_text("test.com", obj)
        assert "Credibility Rating" not in result

    def test_contains_profile_link(self):
        obj = {
            "name": "Reuters",
            "bias": "CENTER",
            "factual": "VERY HIGH",
            "credibility": "HIGH",
            "profile": "https://mediabiasfactcheck.com/reuters/",
        }
        result = print_mbfc_text("reuters.com", obj)
        assert "mediabiasfactcheck.com/reuters/" in result


class TestMbfcPoliticalBias:
    @patch("src.utils._load_mbfc_data")
    def test_returns_text_for_known_domain(self, mock_load):
        mock_load.return_value = {
            "bbc.co.uk": {
                "url": "bbc.co.uk",
                "name": "BBC",
                "bias": "LEFT-CENTER",
                "factual": "HIGH",
                "credibility": "HIGH",
                "profile": "https://mediabiasfactcheck.com/bbc/",
            }
        }
        result = mbfc_political_bias("bbc.co.uk")
        assert result is not None
        assert "BBC" in result

    @patch("src.utils._load_mbfc_data")
    def test_returns_none_for_unknown(self, mock_load):
        mock_load.return_value = {}
        assert mbfc_political_bias("unknown.com") is None
