"""Unit tests for main.py (retry_sweep logic)"""

import sys
import os
import threading
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import retry_sweep, SWEEP_INTERVAL, STALE_THRESHOLD


class TestRetrySweep:
    @patch("main.SWEEP_INTERVAL", 0)
    @patch("main.get_stale_awaiting_ss")
    def test_no_stale_submissions(self, mock_stale):
        stop = threading.Event()

        def stale_and_stop(*args, **kwargs):
            stop.set()
            return []

        mock_stale.side_effect = stale_and_stop
        retry_sweep(MagicMock(), stop)
        mock_stale.assert_called_once()

    @patch("main.SWEEP_INTERVAL", 0)
    @patch("main.approve_submission")
    @patch("main.transition_to_approved", return_value=True)
    @patch("main.is_valid_submission_statement", return_value=True)
    @patch("main.get_stale_awaiting_ss")
    def test_approves_stale_with_valid_ss(self, mock_stale, mock_valid, mock_transition, mock_approve):
        stop = threading.Event()

        mock_comment = MagicMock()
        mock_comment.is_submitter = True
        mock_comment.parent_id = "t3_abc"
        mock_comment.link_id = "t3_abc"
        mock_comment.id = "comment1"

        mock_submission = MagicMock()
        mock_submission.approved = False
        mock_submission.comments.replace_more = MagicMock()
        mock_submission.comments.__iter__ = MagicMock(return_value=iter([mock_comment]))

        reddit = MagicMock()
        reddit.submission.return_value = mock_submission

        call_count = [0]
        def stale_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"submission_id": "abc"}]
            stop.set()
            return []

        mock_stale.side_effect = stale_side_effect
        retry_sweep(reddit, stop)
        mock_transition.assert_called_once()

    @patch("main.SWEEP_INTERVAL", 0)
    @patch("main.transition_to_approved")
    @patch("main.get_stale_awaiting_ss")
    def test_skips_already_approved_submission(self, mock_stale, mock_transition):
        stop = threading.Event()

        mock_submission = MagicMock()
        mock_submission.approved = True

        reddit = MagicMock()
        reddit.submission.return_value = mock_submission

        call_count = [0]
        def stale_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"submission_id": "abc"}]
            stop.set()
            return []

        mock_stale.side_effect = stale_side_effect
        retry_sweep(reddit, stop)
        mock_transition.assert_called_once_with("abc")


class TestConfig:
    def test_sweep_interval(self):
        assert SWEEP_INTERVAL == 120

    def test_stale_threshold(self):
        assert STALE_THRESHOLD == 300
