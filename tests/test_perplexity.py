"""Unit tests for src/perplexity.py"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.perplexity import format_for_reddit, query_perplexity


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


class TestQueryPerplexity:
    @patch("src.perplexity._get_driver")
    def test_successful_query(self, mock_get_driver):
        """Test that query_perplexity scrapes and formats correctly."""
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "<p>India signed a deal [1](https://reuters.com/article) with Iran.</p>"

        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # WebDriverWait returns elements
        with patch("src.perplexity.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = [mock_element]
            result = query_perplexity("test query")

        assert "India signed a deal" in result
        assert "reuters.com" in result
        mock_driver.get.assert_called_once()
        mock_driver.quit.assert_called()

    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_driver")
    def test_retries_on_timeout(self, mock_get_driver, mock_sleep):
        """Test that it retries on TimeoutException."""
        from selenium.common.exceptions import TimeoutException

        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        with patch("src.perplexity.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.side_effect = TimeoutException("timeout")
            result = query_perplexity("test query")

        assert result == ""
        assert mock_get_driver.call_count == 10  # MAX_RETRIES

    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_driver")
    def test_retries_on_webdriver_exception(self, mock_get_driver, mock_sleep):
        """Test that it retries on WebDriverException."""
        from selenium.common.exceptions import WebDriverException

        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        with patch("src.perplexity.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.side_effect = WebDriverException("crash")
            result = query_perplexity("test query")

        assert result == ""
        assert mock_driver.quit.call_count == 10

    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_driver")
    def test_returns_empty_on_no_elements(self, mock_get_driver, mock_sleep):
        """Test returns empty string when dynamic_elements is empty."""
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        with patch("src.perplexity.WebDriverWait") as mock_wait:
            # .until() always returns empty list — `if dynamic_elements` is False
            mock_wait.return_value.until.return_value = []
            result = query_perplexity("test query")

        assert result == ""

    @patch("src.perplexity._get_driver")
    def test_constructs_correct_url(self, mock_get_driver):
        """Test that the URL is correctly encoded."""
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        with patch("src.perplexity.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = []
            query_perplexity("india china border")

        call_url = mock_driver.get.call_args[0][0]
        assert "perplexity.ai/search?q=" in call_url
        assert "india%20china%20border" in call_url

    @patch("src.perplexity._get_driver")
    def test_driver_quit_called_in_finally(self, mock_get_driver):
        """Test driver is always cleaned up."""
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        with patch("src.perplexity.WebDriverWait") as mock_wait:
            mock_element = MagicMock()
            mock_element.get_attribute.return_value = "<p>text</p>"
            mock_wait.return_value.until.return_value = [mock_element]
            query_perplexity("test")

        mock_driver.quit.assert_called()

