"""Unit tests for src/submission_handler.py"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.submission_handler import handle_new_submission, scan_existing_comments_for_ss


class TestHandleNewSubmission:
    @patch("src.submission_handler.approve_submission")
    @patch("src.submission_handler.transition_to_approved", return_value=True)
    @patch("src.submission_handler.init_submission_state")
    def test_self_post_long_text_auto_approves(self, mock_init, mock_transition, mock_approve):
        mock_init.return_value = {"state": "pending_review"}
        submission = MagicMock()
        submission.is_self = True
        submission.selftext = "x" * 250
        submission.id = "abc123"
        handle_new_submission(submission)
        mock_approve.assert_called_once()

    @patch("src.submission_handler.scan_existing_comments_for_ss", return_value=None)
    @patch("src.submission_handler.transition_to_awaiting_ss")
    @patch("src.submission_handler.send_to_modqueue")
    @patch("src.submission_handler.init_submission_state")
    def test_link_post_sends_to_modqueue(self, mock_init, mock_send, mock_transition, mock_scan):
        mock_init.return_value = {"state": "pending_review"}
        submission = MagicMock()
        submission.is_self = False
        submission.id = "abc123"
        handle_new_submission(submission)
        mock_send.assert_called_once()
        mock_transition.assert_called_once()

    @patch("src.submission_handler.init_submission_state")
    def test_already_approved_skips(self, mock_init):
        mock_init.return_value = {"state": "approved"}
        submission = MagicMock()
        submission.id = "abc123"
        handle_new_submission(submission)

    @patch("src.submission_handler.init_submission_state")
    def test_no_state_doc_skips(self, mock_init):
        mock_init.return_value = None
        submission = MagicMock()
        submission.id = "abc123"
        handle_new_submission(submission)

    @patch("src.submission_handler.approve_submission")
    @patch("src.submission_handler.transition_to_approved", return_value=True)
    @patch("src.submission_handler.transition_to_awaiting_ss")
    @patch("src.submission_handler.send_to_modqueue")
    @patch("src.submission_handler.scan_existing_comments_for_ss")
    @patch("src.submission_handler.init_submission_state")
    def test_existing_ss_comment_approves(self, mock_init, mock_scan, mock_send, mock_await, mock_transition, mock_approve):
        mock_init.return_value = {"state": "pending_review"}
        mock_comment = MagicMock()
        mock_comment.id = "comment1"
        mock_scan.return_value = mock_comment
        submission = MagicMock()
        submission.is_self = False
        submission.id = "abc123"
        handle_new_submission(submission)
        mock_approve.assert_called_once()


class TestScanExistingCommentsForSs:
    def test_finds_valid_ss(self):
        submission = MagicMock()
        comment = MagicMock()
        comment.is_submitter = True
        comment.parent_id = "t3_abc"
        comment.link_id = "t3_abc"
        comment.body = "Submission Statement " + "x" * 200
        submission.comments.replace_more = MagicMock()
        submission.comments.__iter__ = MagicMock(return_value=iter([comment]))
        result = scan_existing_comments_for_ss(submission)
        assert result == comment

    def test_ignores_non_submitter(self):
        submission = MagicMock()
        comment = MagicMock()
        comment.is_submitter = False
        comment.parent_id = "t3_abc"
        comment.link_id = "t3_abc"
        comment.body = "Submission Statement " + "x" * 200
        submission.comments.replace_more = MagicMock()
        submission.comments.__iter__ = MagicMock(return_value=iter([comment]))
        assert scan_existing_comments_for_ss(submission) is None

    def test_ignores_reply_comments(self):
        submission = MagicMock()
        comment = MagicMock()
        comment.is_submitter = True
        comment.parent_id = "t1_xyz"
        comment.link_id = "t3_abc"
        comment.body = "Submission Statement " + "x" * 200
        submission.comments.replace_more = MagicMock()
        submission.comments.__iter__ = MagicMock(return_value=iter([comment]))
        assert scan_existing_comments_for_ss(submission) is None
