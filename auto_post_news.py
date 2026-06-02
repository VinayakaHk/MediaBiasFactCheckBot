"""
auto_post_news.py - Standalone script to fetch Indian geopolitics news from RSS feeds,
summarize via Perplexity AI, and post to Reddit as a link submission with SS comment.

Usage: python auto_post_news.py
Intended to run via crontab twice daily (morning + evening).
"""

import os
import re
import random
import logging
from difflib import SequenceMatcher
from urllib.parse import urlparse

import feedparser
import praw
from dotenv import load_dotenv

from src.perplexity import query_perplexity

load_dotenv()

# --- Logging ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# --- Configuration ---

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
    "https://www.theguardian.com/world/india/rss",
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://www.firstpost.com/commonfeeds/v1/mfp/rss/world.xml",
    "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",  
    "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
]

GEOPOLITICS_KEYWORDS = re.compile(
    r"geopolit|foreign policy|diplomacy|bilateral|strategic"
    r"|border|china|pakistan|us.india|indo.pacific|jaishankar|modi|brics|quad"
    r"|sanctions|trade war|alliance|treaty",
    re.IGNORECASE,
)

SUBREDDIT = os.environ.get("SUBREDDIT")
MAX_RETRIES = 5
RETRY_DELAY = 10
DEDUP_THRESHOLD = 0.55  # title similarity threshold for deduplication
REDDIT_DUP_THRESHOLD = 0.55  # similarity threshold for Reddit duplicate check


# --- Reddit ---

def initialize_reddit():
    return praw.Reddit(
        client_id=os.environ.get("CLIENT_ID"),
        client_secret=os.environ.get("CLIENT_SECRET"),
        user_agent=f'AutoPostNews/1.0 by u/{os.environ.get("REDDIT_USERNAME")}',
        username=os.environ.get("REDDIT_USERNAME"),
        password=os.environ.get("PASSWORD"),
        check_for_async=False,
    )


# --- Deduplication ---

def title_similarity(a, b):
    """Compute similarity ratio between two titles (0-1)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def normalize_url(url):
    """Strip query params and fragments for URL comparison."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def deduplicate_articles(articles):
    """Remove articles covering the same story based on title similarity."""
    if not articles:
        return articles

    unique = []
    for article in articles:
        is_dup = False
        for kept in unique:
            sim = title_similarity(article["title"], kept["title"])
            if sim > DEDUP_THRESHOLD:
                log.info(
                    "Dedup: dropping '%s' (%.0f%% similar to '%s')",
                    article["title"], sim * 100, kept["title"],
                )
                is_dup = True
                break
        if not is_dup:
            unique.append(article)

    log.info("Deduplication: %d -> %d articles", len(articles), len(unique))
    return unique


# --- Reddit Duplicate Check ---

def fetch_recent_reddit_posts():
    """Fetch recent posts from the subreddit using PRAW (new listing)."""
    try:
        reddit = initialize_reddit()
        subreddit = reddit.subreddit(SUBREDDIT)
        posts = []
        for post in subreddit.new(limit=200):
            post_url = getattr(post, "url_overridden_by_dest", None) or post.url
            posts.append({"title": post.title, "url": post_url})
        log.info("Fetched %d recent posts from r/%s (new)", len(posts), SUBREDDIT)
        return posts
    except Exception as e:
        log.warning("Failed to fetch Reddit posts: %s", e)
        return []


def is_already_posted(article, reddit_posts):
    """Check if article URL or title already exists on the subreddit."""
    article_url_norm = normalize_url(article["url"])

    for post in reddit_posts:
        # Exact URL match
        if normalize_url(post["url"]) == article_url_norm:
            log.info("Reddit dup (URL match): '%s'", article["title"])
            return True
        # Title similarity match
        sim = title_similarity(article["title"], post["title"])
        if sim > REDDIT_DUP_THRESHOLD:
            log.info(
                "Reddit dup (title %.0f%%): '%s' ~ '%s'",
                sim * 100, article["title"], post["title"],
            )
            return True
    return False


# --- RSS Feed ---

def fetch_news_article():
    """Fetch a deduplicated, non-reposted article from RSS feeds."""
    entries = []
    for feed_url in RSS_FEEDS:
        log.info("Fetching feed: %s", feed_url)
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if link and title and re.search(r"india", title, re.IGNORECASE) and GEOPOLITICS_KEYWORDS.search(title):
                entries.append({"title": title, "url": link})

    log.info("Found %d matching articles from RSS feeds", len(entries))
    if not entries:
        return None

    # Deduplicate same-story articles from different sources
    entries = deduplicate_articles(entries)
    if not entries:
        return None

    # Check against recent Reddit posts
    reddit_posts = fetch_recent_reddit_posts()
    random.shuffle(entries)

    for article in entries:
        if not is_already_posted(article, reddit_posts):
            log.info("Selected article: '%s'", article["title"])
            return article
        log.info("Skipping (already on Reddit): '%s'", article["title"])

    log.warning("All articles already posted on Reddit")
    return None


# --- Post to Reddit ---

def post_to_reddit(article, summary):
    """Post the article as a link submission and add the SS as a comment."""
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(SUBREDDIT)

    submission = subreddit.submit(
        title=article["title"],
        url=article["url"],
        send_replies=False,
    )

    ss_comment = f"Submission Statement: {summary}"
    submission.reply(body=ss_comment)

    log.info("Posted: %s", submission.url)
    log.info("Title: %s", article["title"])
    return submission


# --- Main ---

def main():
    log.info("=== Auto Post News started ===")

    article = fetch_news_article()
    if not article:
        log.warning("No suitable article found. Exiting.")
        return

    log.info("Summarizing with Perplexity: %s", article["url"])
    summary = query_perplexity(
        f"Summarize this news article in 2-3 paragraphs for a geopolitics discussion forum: {article['title']} {article['url']} \n\n Make sure to include key facts, context, and implications. Avoid opinions or analysis. Focus on the who, what, when, where, and why. Donot ask any follow up questions."
    )
    if not summary or len(summary) < 160:
        log.error("Failed to get summary or summary too short. Exiting.")
        return

    log.info("Posting to Reddit...")
    post_to_reddit(article, summary)
    log.info("=== Done ===")


if __name__ == "__main__":
    main()
