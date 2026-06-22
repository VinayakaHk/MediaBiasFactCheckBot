"""Unit tests for src/reddit_utils.py"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reddit_utils import fetchDomainsandUrls, get_reply_text


class TestFetchDomainsAndUrls:
    def test_extracts_urls_from_link_post(self):
        submission = MagicMock()
        submission.url = "https://www.thehindu.com/news/article123.ece"
        submission.selftext = ""
        urls, domains = fetchDomainsandUrls(submission, is_self=False)
        assert "https://www.thehindu.com/news/article123.ece" in urls
        assert "www.thehindu.com" in domains

    def test_extracts_urls_from_self_post(self):
        submission = MagicMock()
        submission.selftext = "Check this: https://reuters.com/article/123 and https://bbc.co.uk/news/456"
        urls, domains = fetchDomainsandUrls(submission, is_self=True)
        assert len(urls) == 2
        assert "reuters.com" in domains
        assert "bbc.co.uk" in domains

    def test_no_urls(self):
        submission = MagicMock()
        submission.selftext = "No URLs here"
        urls, domains = fetchDomainsandUrls(submission, is_self=True)
        assert urls == []
        assert domains == []

    def test_deduplicates_urls(self):
        submission = MagicMock()
        submission.selftext = "https://example.com/1 and https://example.com/1 again"
        urls, domains = fetchDomainsandUrls(submission, is_self=True)
        assert len(urls) == 1


class TestGetReplyText:
    @patch("src.reddit_utils.mbfc_political_bias", return_value=None)
    @patch("src.reddit_utils.add_prefix_to_paragraphs", return_value="> quoted")
    def test_includes_archive_links(self, mock_prefix, mock_mbfc):
        comment = MagicMock()
        comment.body = "SS text"
        comment.permalink = "/r/test/comments/abc/def/ghi"
        result = get_reply_text(["thehindu.com"], ["https://thehindu.com/article"], comment)
        assert "archive.is" in result
        assert "thehindu.com" in result

    @patch("src.reddit_utils.mbfc_political_bias", return_value=None)
    def test_without_comment(self, mock_mbfc):
        result = get_reply_text(["bbc.co.uk"], ["https://bbc.co.uk/news/123"], None)
        assert "archive.is" in result
        assert "Submission Statement by OP" not in result

    @patch("src.reddit_utils.mbfc_political_bias", return_value="\n\n**MBFC Rating**: CENTER")
    @patch("src.reddit_utils.add_prefix_to_paragraphs", return_value="> text")
    def test_includes_mbfc_when_available(self, mock_prefix, mock_mbfc):
        comment = MagicMock()
        comment.body = "SS"
        comment.permalink = "/r/test/abc"
        result = get_reply_text(["reuters.com"], ["https://reuters.com/article"], comment)
        assert "MBFC" in result

    @patch("src.reddit_utils.mbfc_political_bias", return_value=None)
    def test_includes_community_reminder(self, mock_mbfc):
        result = get_reply_text(["x.com"], ["https://x.com/post"], None)
        assert "Community Reminder" in result

    @patch("src.reddit_utils.mbfc_political_bias", return_value=None)
    def test_includes_moderator_contact(self, mock_mbfc):
        result = get_reply_text(["x.com"], ["https://x.com/post"], None)
        assert "Contact our moderators" in result
