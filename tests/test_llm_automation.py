"""Unit tests for src/llm_automation.py with mocked Selenium."""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLlmDetection:
    def _make_comment(self, body="test comment", parent_id="t3_abc", link_id="t3_abc"):
        comment = MagicMock()
        comment.body = body
        comment.author = "testuser"
        comment.id = "comment1"
        comment.parent_id = parent_id
        comment.link_id = link_id
        comment.link_permalink = "https://reddit.com/r/test/comments/abc/"
        comment.mod = MagicMock()
        comment.mod.send_removal_message.return_value = MagicMock()
        return comment

    @patch("src.llm_automation.store_llm_in_comments")
    @patch("src.llm_automation.time.sleep")
    @patch("src.llm_automation.webdriver.Chrome")
    @patch("src.llm_automation.Display")
    def test_violation_detected_removes_comment(self, mock_display, mock_chrome, mock_sleep, mock_store):
        """When LLM returns 'True. abusive language', comment is removed."""
        from src.llm_automation import llm_detection

        mock_element = MagicMock()
        mock_element.text = "True. Contains abusive language targeting a group"

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        with patch("src.llm_automation.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = [mock_element]

            comment = self._make_comment(body="you are an idiot")
            llm_detection(comment, MagicMock(), "parent context")

        comment.mod.remove.assert_called_once()
        comment.save.assert_called_once()
        mock_store.assert_called_once()

    @patch("src.llm_automation.store_llm_in_comments")
    @patch("src.llm_automation.time.sleep")
    @patch("src.llm_automation.webdriver.Chrome")
    @patch("src.llm_automation.Display")
    def test_no_violation_saves_comment(self, mock_display, mock_chrome, mock_sleep, mock_store):
        """When LLM returns 'False', comment is just saved."""
        from src.llm_automation import llm_detection

        mock_element = MagicMock()
        mock_element.text = "False. The comment is a valid criticism."

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        with patch("src.llm_automation.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = [mock_element]

            comment = self._make_comment(body="I disagree with this policy")
            llm_detection(comment, MagicMock(), "parent context")

        comment.mod.remove.assert_not_called()
        comment.save.assert_called_once()

    @patch("src.llm_automation.store_llm_in_comments")
    @patch("src.llm_automation.time.sleep")
    @patch("src.llm_automation.webdriver.Chrome")
    @patch("src.llm_automation.Display")
    def test_unexpected_response_logs_warning(self, mock_display, mock_chrome, mock_sleep, mock_store):
        """When LLM returns unexpected text, it logs a warning."""
        from src.llm_automation import llm_detection

        mock_element = MagicMock()
        mock_element.text = "I cannot determine this."

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        with patch("src.llm_automation.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = [mock_element]

            comment = self._make_comment()
            llm_detection(comment, MagicMock(), "parent context")

        comment.mod.remove.assert_not_called()
        comment.save.assert_not_called()

    @patch("src.llm_automation.store_llm_in_comments")
    @patch("src.llm_automation.time.sleep")
    @patch("src.llm_automation.webdriver.Chrome")
    @patch("src.llm_automation.Display")
    def test_true_with_does_not_is_not_violation(self, mock_display, mock_chrome, mock_sleep, mock_store):
        """'True. does not violate' should NOT remove the comment."""
        from src.llm_automation import llm_detection

        mock_element = MagicMock()
        mock_element.text = "True. The comment does not violate any rules."

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        with patch("src.llm_automation.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = [mock_element]

            comment = self._make_comment()
            llm_detection(comment, MagicMock(), "parent context")

        comment.mod.remove.assert_not_called()

    @patch("src.llm_automation.store_llm_in_comments")
    @patch("src.llm_automation.time.sleep")
    @patch("src.llm_automation.webdriver.Chrome")
    @patch("src.llm_automation.Display")
    def test_retries_on_webdriver_exception(self, mock_display, mock_chrome, mock_sleep, mock_store):
        """Test that it retries on WebDriverException."""
        from selenium.common.exceptions import WebDriverException
        from src.llm_automation import llm_detection

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        with patch("src.llm_automation.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.side_effect = WebDriverException("crash")

            comment = self._make_comment()
            llm_detection(comment, MagicMock(), "parent context")

        assert mock_chrome.call_count == 3  # MAX_RETRIES

    @patch("src.llm_automation.store_llm_in_comments")
    @patch("src.llm_automation.time.sleep")
    @patch("src.llm_automation.webdriver.Chrome")
    @patch("src.llm_automation.Display")
    def test_non_top_level_comment_not_removed(self, mock_display, mock_chrome, mock_sleep, mock_store):
        """Violation on a reply (not top-level) should not call mod.remove."""
        from src.llm_automation import llm_detection

        mock_element = MagicMock()
        mock_element.text = "True. Abusive language used"

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        with patch("src.llm_automation.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = [mock_element]

            # parent_id != link_id means it's a reply, not top-level
            comment = self._make_comment(parent_id="t1_xyz", link_id="t3_abc")
            llm_detection(comment, MagicMock(), "parent context")

        comment.mod.remove.assert_not_called()
        comment.save.assert_called_once()


class TestElementStrip:
    def test_strips_text(self):
        from src.llm_automation import element_strip
        elem = MagicMock()
        elem.text = "  hello world  "
        assert element_strip(elem) == "hello world"
