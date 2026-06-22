"""Unit tests for auto_post_news.py"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_post_news import (
    decode_google_news_url,
    title_similarity,
    deduplicate_articles,
    filter_already_posted,
    INDIA_PATTERN,
    GEOPOLITICS_KEYWORDS,
    EXCLUDE_PATTERN,
)


class TestRegexFilters:
    def should_post(self, title):
        return (
            bool(INDIA_PATTERN.search(title))
            and bool(GEOPOLITICS_KEYWORDS.search(title))
            and not bool(EXCLUDE_PATTERN.search(title))
        )

    def test_accepts_geopolitics_articles(self):
        accept = [
            "India-China border standoff: Troops disengage at key LAC points",
            "Modi meets Biden at G20 summit, signs bilateral defence cooperation pact",
            "India imposes sanctions on Pakistan-based terror groups after diplomatic row",
            "Jaishankar at ASEAN: India pushes for Indo-Pacific maritime code",
            "India and Iran sign Chabahar port deal amid US sanctions threat",
            "Indian diplomat expelled from Canada over extradition dispute",
            "India joins BRICS push to challenge dollar dominance in trade",
            "Trump says he will visit India as frosty relationship with Modi thaws",
            "Delhi issues strong protest after US strikes kill three Indian seafarers in Gulf",
            "Trump, Modi discuss trade, safety of Indian sailors in Gulf region - Reuters",
        ]
        for title in accept:
            assert self.should_post(title), f"Should accept: {title}"

    def test_rejects_non_geopolitics_articles(self):
        reject = [
            "Infosys, TCS & other Indian IT stocks crash!",
            "Indian shares climb on Gulf peace deal tracking global rally - Reuters",
            "India vs Australia 3rd Test: Day 2 highlights from cricket",
            "Indian startup raises $50M in Series B IPO buzz",
            "Delhi's temperature showed 43.5C. Why did it feel hotter?",
            "India's Nifty IT index at three-year low - Reuters",
            "Rupee rebounds 20 paise to 94.20 on hopes of India-US trade deal",
            "India: Why a country of 1.4 billion is not in the football World Cup",
        ]
        for title in reject:
            assert not self.should_post(title), f"Should reject: {title}"

    def test_india_pattern_matches(self):
        assert INDIA_PATTERN.search("India signs deal")
        assert INDIA_PATTERN.search("Indian diplomat expelled")
        assert INDIA_PATTERN.search("Modi meets Biden")
        assert INDIA_PATTERN.search("Jaishankar at ASEAN")
        assert INDIA_PATTERN.search("New Delhi protests")

    def test_india_pattern_no_match(self):
        assert not INDIA_PATTERN.search("China and Pakistan sign trade deal")
        assert not INDIA_PATTERN.search("US imposes tariffs on EU")


class TestTitleSimilarity:
    def test_identical(self):
        assert title_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self):
        assert title_similarity("abc", "xyz") < 0.3

    def test_similar(self):
        sim = title_similarity(
            "Three Indian-flagged oil tankers transit through Strait of Hormuz",
            "Three Indian-flagged oil tankers clear Strait of Hormuz, minister says",
        )
        assert sim > 0.55


class TestDeduplicateArticles:
    def test_removes_duplicates(self):
        articles = [
            {"title": "India-China border standoff escalates", "url": "http://a.com"},
            {"title": "India-China border standoff escalates further", "url": "http://b.com"},
            {"title": "Modi meets Biden at G20", "url": "http://c.com"},
        ]
        result = deduplicate_articles(articles)
        assert len(result) <= 2

    def test_keeps_unique(self):
        articles = [
            {"title": "India signs deal with Iran", "url": "http://a.com"},
            {"title": "Modi meets Biden at G20 summit", "url": "http://b.com"},
            {"title": "Jaishankar visits Japan for Quad meeting", "url": "http://c.com"},
        ]
        assert len(deduplicate_articles(articles)) == 3

    def test_empty(self):
        assert deduplicate_articles([]) == []


class TestFilterAlreadyPosted:
    def test_filters_exact(self):
        articles = [
            {"title": "India signs deal with Iran", "url": "http://a.com"},
            {"title": "Modi meets Biden at G20", "url": "http://b.com"},
        ]
        reddit_posts = [{"title": "India signs deal with Iran"}]
        result = filter_already_posted(articles, reddit_posts)
        assert len(result) == 1
        assert result[0]["title"] == "Modi meets Biden at G20"

    def test_keeps_all_when_no_posts(self):
        articles = [{"title": "A", "url": "http://a.com"}, {"title": "B", "url": "http://b.com"}]
        assert len(filter_already_posted(articles, [])) == 2


class TestDecodeGoogleNewsUrl:
    def test_non_google_passthrough(self):
        url = "https://www.thehindu.com/article/123"
        assert decode_google_news_url(url) == url

    @patch("auto_post_news.new_decoderv1")
    def test_decodes_successfully(self, mock_decoder):
        mock_decoder.return_value = {"status": True, "decoded_url": "https://real.com/story"}
        assert decode_google_news_url("https://news.google.com/rss/articles/abc") == "https://real.com/story"

    @patch("auto_post_news.new_decoderv1")
    def test_returns_original_on_failure(self, mock_decoder):
        mock_decoder.side_effect = Exception("fail")
        url = "https://news.google.com/rss/articles/abc"
        assert decode_google_news_url(url) == url


class TestFetchNewsArticle:
    @patch("auto_post_news.filter_already_posted")
    @patch("auto_post_news.fetch_recent_reddit_posts")
    @patch("auto_post_news.feedparser.parse")
    def test_returns_article_when_available(self, mock_parse, mock_reddit, mock_filter):
        mock_parse.return_value = MagicMock(
            entries=[{"title": "India-China border tensions rise amid diplomatic standoff", "link": "http://example.com/1"}]
        )
        mock_reddit.return_value = []
        mock_filter.side_effect = lambda articles, posts: articles

        from auto_post_news import fetch_news_article
        result = fetch_news_article()
        assert result is not None
        assert "India-China" in result["title"]

    @patch("auto_post_news.feedparser.parse")
    def test_returns_none_when_no_matching(self, mock_parse):
        mock_parse.return_value = MagicMock(
            entries=[{"title": "Cricket World Cup final", "link": "http://example.com/1"}]
        )
        from auto_post_news import fetch_news_article
        assert fetch_news_article() is None


class TestThePrintBypass:
    """ThePrint articles bypass regex filtering, only checked against Reddit duplicates."""

    @patch("auto_post_news.filter_already_posted")
    @patch("auto_post_news.fetch_recent_reddit_posts")
    @patch("auto_post_news.decode_google_news_url")
    @patch("auto_post_news.feedparser.parse")
    def test_theprint_bypasses_regex(self, mock_parse, mock_decode, mock_reddit, mock_filter):
        """A ThePrint article that wouldn't pass regex filters should still be included."""
        mock_parse.return_value = MagicMock(
            entries=[{"title": "Why Southeast Asia matters more than ever", "link": "https://news.google.com/rss/articles/abc"}]
        )
        # Decode resolves to theprint.in URL
        mock_decode.return_value = "https://theprint.in/diplomacy/why-southeast-asia-matters/123"
        mock_reddit.return_value = []
        mock_filter.side_effect = lambda articles, posts: articles

        from auto_post_news import fetch_news_article
        result = fetch_news_article()
        assert result is not None
        assert "Southeast Asia" in result["title"]

    @patch("auto_post_news.filter_already_posted")
    @patch("auto_post_news.fetch_recent_reddit_posts")
    @patch("auto_post_news.decode_google_news_url")
    @patch("auto_post_news.feedparser.parse")
    def test_theprint_still_filtered_by_reddit_dedup(self, mock_parse, mock_decode, mock_reddit, mock_filter):
        """A ThePrint article already posted on Reddit should be filtered out."""
        mock_parse.return_value = MagicMock(
            entries=[{"title": "ThePrint exclusive on India diplomacy", "link": "https://news.google.com/rss/articles/xyz"}]
        )
        mock_decode.return_value = "https://theprint.in/diplomacy/exclusive/456"
        mock_reddit.return_value = [{"title": "ThePrint exclusive on India diplomacy"}]
        mock_filter.return_value = []  # Reddit dedup removes it

        from auto_post_news import fetch_news_article
        result = fetch_news_article()
        assert result is None
