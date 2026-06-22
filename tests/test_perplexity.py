"""Unit tests for src/perplexity.py"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.perplexity import format_for_reddit


class TestFormatForReddit:
    def test_converts_citations_to_domain_links(self):
        text = "Some claim [1](https://www.reuters.com/article/123) is important"
        result = format_for_reddit(text)
        assert "reuters.com" in result
        assert "[1]" not in result

    def test_multiple_citations(self):
        text = "First [1](https://bbc.co.uk/news) then [2](https://reuters.com/art)"
        result = format_for_reddit(text)
        assert "bbc.co.uk" in result
        assert "reuters.com" in result

    def test_removes_plus_numbers(self):
        assert "+5" not in format_for_reddit("something+5 here")

    def test_strips_whitespace(self):
        assert format_for_reddit("  hello  ") == "hello"

    def test_empty_string(self):
        assert format_for_reddit("") == ""

    def test_no_citations_passthrough(self):
        text = "Plain text with no citations"
        assert format_for_reddit(text) == text
