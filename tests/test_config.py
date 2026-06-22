"""Unit tests for src/config.py"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import MIN_SUBMISSION_STATEMENT_LENGTH, MBFC_JSON_PATH


class TestConfig:
    def test_min_ss_length(self):
        assert MIN_SUBMISSION_STATEMENT_LENGTH == 150

    def test_mbfc_json_path(self):
        assert "MBFC" in MBFC_JSON_PATH
        assert MBFC_JSON_PATH.endswith(".json")
