"""Unit tests for src/mongodb.py"""

import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mongodb import MongoDB, STATE_PENDING, STATE_AWAITING_SS, STATE_APPROVED


def _make_db_instance():
    """Create a MongoDB instance with mocked connection."""
    db = MongoDB.__new__(MongoDB)
    db._initialized = True
    db.db = MagicMock()
    return db


class TestMongoDBStates:
    def test_state_constants(self):
        assert STATE_PENDING == "pending_review"
        assert STATE_AWAITING_SS == "awaiting_ss"
        assert STATE_APPROVED == "approved"


class TestInitSubmissionState:
    def test_creates_and_returns_state(self):
        db = _make_db_instance()
        db.db.__getitem__.return_value.find_one.return_value = {
            "submission_id": "test", "state": STATE_PENDING
        }
        result = db.init_submission_state("test")
        assert result["state"] == STATE_PENDING
        db.db.__getitem__.return_value.update_one.assert_called_once()


class TestTransitionToAwaitingSs:
    def test_success(self):
        db = _make_db_instance()
        db.db.__getitem__.return_value.update_one.return_value = MagicMock(modified_count=1)
        assert db.transition_to_awaiting_ss("test") is True

    def test_failure_wrong_state(self):
        db = _make_db_instance()
        db.db.__getitem__.return_value.update_one.return_value = MagicMock(modified_count=0)
        assert db.transition_to_awaiting_ss("test") is False


class TestTransitionToApproved:
    def test_success(self):
        db = _make_db_instance()
        db.db.__getitem__.return_value.update_one.return_value = MagicMock(modified_count=1)
        assert db.transition_to_approved("test", "comment123") is True

    def test_without_comment_id(self):
        db = _make_db_instance()
        db.db.__getitem__.return_value.update_one.return_value = MagicMock(modified_count=1)
        assert db.transition_to_approved("test") is True

    def test_failure(self):
        db = _make_db_instance()
        db.db.__getitem__.return_value.update_one.return_value = MagicMock(modified_count=0)
        assert db.transition_to_approved("test") is False


class TestGetStaleAwaitingSs:
    def test_returns_stale_docs(self):
        db = _make_db_instance()
        db.db.__getitem__.return_value.find.return_value = [
            {"submission_id": "old1", "state": STATE_AWAITING_SS},
            {"submission_id": "old2", "state": STATE_AWAITING_SS},
        ]
        result = db.get_stale_awaiting_ss(300)
        assert len(result) == 2

    def test_returns_empty_when_none_stale(self):
        db = _make_db_instance()
        db.db.__getitem__.return_value.find.return_value = []
        assert db.get_stale_awaiting_ss(300) == []


class TestGetCommentBody:
    def test_returns_parent_body(self):
        db = _make_db_instance()
        collection = db.db.__getitem__.return_value
        collection.find_one.side_effect = [
            {"comment_id": "child", "link_id": "t3_abc", "parent_id": "t1_parent"},
            {"comment_id": "parent", "body": "parent body"},
        ]
        assert db.get_comment_body("child") == "parent body"

    def test_returns_none_for_top_level(self):
        db = _make_db_instance()
        collection = db.db.__getitem__.return_value
        collection.find_one.return_value = {
            "comment_id": "top", "link_id": "t3_abc", "parent_id": "t3_abc"
        }
        assert db.get_comment_body("top") is None
