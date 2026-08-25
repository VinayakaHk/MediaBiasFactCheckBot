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
    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_perplexity_cookies")
    @patch("src.perplexity._get_driver")
    def test_successful_query(self, mock_get_driver, mock_cookies, mock_sleep):
        """Test that query_perplexity scrapes and formats correctly."""
        mock_element = MagicMock()
        mock_element.text = "India signed a deal with Iran. This is a long enough text to pass the 50 char check."
        mock_element.get_attribute.return_value = "<p>India signed a deal [1](https://reuters.com/article) with Iran.</p>"

        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_cookies.return_value = [{"name": "test", "value": "val", "domain": ".perplexity.ai", "path": "/", "secure": True}]

        # find_elements returns the prose element with stable text (triggers after 2 stable polls)
        mock_driver.find_elements.return_value = [mock_element]

        result = query_perplexity("test query")

        assert "India signed a deal" in result
        assert "reuters.com" in result
        mock_driver.quit.assert_called()

    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_perplexity_cookies")
    @patch("src.perplexity._get_driver")
    def test_retries_on_timeout(self, mock_get_driver, mock_cookies, mock_sleep):
        """Test that it retries on TimeoutException."""
        from selenium.common.exceptions import TimeoutException

        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_cookies.return_value = []

        # driver.get raises TimeoutException (even the initial perplexity.ai load)
        mock_driver.get.side_effect = TimeoutException("timeout")
        # find_elements returns nothing (no prose)
        mock_driver.find_elements.return_value = []

        result = query_perplexity("test query")

        assert result == ""
        assert mock_get_driver.call_count == 3  # MAX_RETRIES

    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_perplexity_cookies")
    @patch("src.perplexity._get_driver")
    def test_retries_on_webdriver_exception(self, mock_get_driver, mock_cookies, mock_sleep):
        """Test that it retries on WebDriverException."""
        from selenium.common.exceptions import WebDriverException

        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_cookies.return_value = []

        mock_driver.get.side_effect = WebDriverException("crash")

        result = query_perplexity("test query")

        assert result == ""
        assert mock_driver.quit.call_count == 3  # MAX_RETRIES

    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_perplexity_cookies")
    @patch("src.perplexity._get_driver")
    def test_returns_empty_on_no_elements(self, mock_get_driver, mock_cookies, mock_sleep):
        """Test returns empty string when no prose elements found."""
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_cookies.return_value = []

        # find_elements always returns empty
        mock_driver.find_elements.return_value = []

        result = query_perplexity("test query")

        assert result == ""

    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_perplexity_cookies")
    @patch("src.perplexity._get_driver")
    def test_constructs_correct_url(self, mock_get_driver, mock_cookies, mock_sleep):
        """Test that the URL is correctly encoded."""
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_cookies.return_value = []
        mock_driver.find_elements.return_value = []

        query_perplexity("india china border")

        # Second call to driver.get is the search URL (first is perplexity.ai home)
        calls = mock_driver.get.call_args_list
        search_url = calls[1][0][0]
        assert "perplexity.ai/search?q=" in search_url
        assert "india%20china%20border" in search_url

    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_perplexity_cookies")
    @patch("src.perplexity._get_driver")
    def test_driver_quit_called_in_finally(self, mock_get_driver, mock_cookies, mock_sleep):
        """Test driver is always cleaned up."""
        mock_element = MagicMock()
        mock_element.text = "This is a response that is long enough to pass the fifty character minimum check."
        mock_element.get_attribute.return_value = "<p>text</p>"

        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_cookies.return_value = []
        mock_driver.find_elements.return_value = [mock_element]

        query_perplexity("test")

        mock_driver.quit.assert_called()

    @patch("src.perplexity.time.sleep")
    @patch("src.perplexity._get_perplexity_cookies")
    @patch("src.perplexity._get_driver")
    def test_sign_in_wall_triggers_retry(self, mock_get_driver, mock_cookies, mock_sleep):
        """Test that sign-in wall message triggers a retry."""
        mock_element = MagicMock()
        mock_element.text = "Sign up and repeat your request."

        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_cookies.return_value = []
        mock_driver.find_elements.return_value = [mock_element]

        result = query_perplexity("test query")

        assert result == ""
        assert mock_get_driver.call_count == 3  # MAX_RETRIES
