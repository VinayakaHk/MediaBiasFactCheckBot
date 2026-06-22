"""Unit tests for src/comment_handler.py"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.comment_handler import has_submission_statement, handle_comment


class TestHasSubmissionStatement:
    @patch("src.comment_handler.remove_and_reply")
    def test_valid_ss(self, mock_remove):
        comment = MagicMock()
        comment.body = "Submission Statement " + "x" * 200
        comment.removed = False
        assert has_submission_statement(comment) is True
        mock_remove.assert_not_called()

    @patch("src.comment_handler.remove_and_reply")
    def test_too_short_ss(self, mock_remove):
        comment = MagicMock()
        comment.body = "Submission Statement too short"
        comment.removed = False
        assert has_submission_statement(comment) is False
        mock_remove.assert_called_once()

    @patch("src.comment_handler.remove_and_reply")
    def test_wrong_format(self, mock_remove):
        comment = MagicMock()
        comment.body = "This is not an SS " + "x" * 200
        comment.removed = False
        assert has_submission_statement(comment) is False
        mock_remove.assert_called_once()

    @patch("src.comment_handler.remove_and_reply")
    def test_already_removed_no_reply(self, mock_remove):
        comment = MagicMock()
        comment.body = "wrong format"
        comment.removed = True
        assert has_submission_statement(comment) is False
        mock_remove.assert_not_called()


class TestHandleComment:
    @patch("src.comment_handler.approve_submission")
    @patch("src.comment_handler.transition_to_approved", return_value=True)
    @patch("src.comment_handler.get_submission_state")
    def test_approves_on_valid_ss(self, mock_state, mock_transition, mock_approve):
        mock_state.return_value = {"state": "awaiting_ss"}
        comment = MagicMock()
        comment.is_submitter = True
        comment.parent_id = "t3_abc"
        comment.link_id = "t3_abc"
        comment.body = "Submission Statement " + "x" * 200
        comment.removed = False
        comment.submission = MagicMock()
        comment.submission.id = "abc"
        comment.submission.is_self = False
        handle_comment(comment)
        mock_approve.assert_called_once()

    @patch("src.comment_handler.get_submission_state")
    def test_ignores_non_submitter(self, mock_state):
        comment = MagicMock()
        comment.is_submitter = False
        comment.parent_id = "t3_abc"
        comment.link_id = "t3_abc"
        handle_comment(comment)
        mock_state.assert_not_called()

    @patch("src.comment_handler.get_submission_state")
    def test_ignores_reply_to_comment(self, mock_state):
        comment = MagicMock()
        comment.is_submitter = True
        comment.parent_id = "t1_xyz"
        comment.link_id = "t3_abc"
        handle_comment(comment)
        mock_state.assert_not_called()

    @patch("src.comment_handler.get_submission_state")
    def test_ignores_already_approved(self, mock_state):
        mock_state.return_value = {"state": "approved"}
        comment = MagicMock()
        comment.is_submitter = True
        comment.parent_id = "t3_abc"
        comment.link_id = "t3_abc"
        comment.submission = MagicMock()
        comment.submission.id = "abc"
        handle_comment(comment)

    @patch("src.comment_handler.get_submission_state")
    def test_ignores_no_state_doc(self, mock_state):
        mock_state.return_value = None
        comment = MagicMock()
        comment.is_submitter = True
        comment.parent_id = "t3_abc"
        comment.link_id = "t3_abc"
        comment.submission = MagicMock()
        comment.submission.id = "abc"
        handle_comment(comment)
