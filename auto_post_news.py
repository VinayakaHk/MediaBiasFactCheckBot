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

import feedparser
import praw
from dotenv import load_dotenv
from googlenewsdecoder import new_decoderv1

from src.perplexity import query_perplexity

load_dotenv()

# --- Colorized Logging ---

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: DIM,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: f"{BOLD}{RED}",
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, RESET)
        timestamp = self.formatTime(record, self.datefmt)
        level = f"{color}{record.levelname:<7}{RESET}"
        msg = record.getMessage()
        return f"{DIM}{timestamp}{RESET} {level} {msg}"


handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter(datefmt="%H:%M:%S"))
logging.basicConfig(level=logging.INFO, handlers=[handler])
log = logging.getLogger(__name__)

# --- Configuration ---

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
    "https://www.theguardian.com/world/india/rss",
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://www.firstpost.com/commonfeeds/v1/mfp/rss/world.xml",
    "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
    "https://news.google.com/rss/search?q=site:https://theprint.in/category/diplomacy/&hl=en-US&gl=US&ceid=US%3Aen",
    "https://news.google.com/rss/search?q=site:https://www.reuters.com/world/india/&hl=en-IN&gl=IN&ceid=IN:en",
]

INDIA_PATTERN = re.compile(r"\bindia\b|indian|modi|jaishankar|new delhi", re.IGNORECASE)

GEOPOLITICS_KEYWORDS = re.compile(
    r"geopolit|foreign policy|diplomacy|bilateral"
    r"|china|pakistan|united states|america|\bus\b.*(tariff|trade|deal|sanction)"
    r"|indo.pacific|brics|quad"
    r"|sanctions|trade war|tariff|alliance|treaty|summit"
    r"|military|defence|defense|nuclear|missile|drone"
    r"|iran|gulf|strait|lng"
    r"|border.*(dispute|tension|clash|standoff)"
    r"|war|ceasefire|conflict",
    re.IGNORECASE,
)

EXCLUDE_PATTERN = re.compile(
    r"cricket|ipl|bbl|football|fifa|messi|sport"
    r"|bollywood|film|movie|music|grammy"
    r"|heat.?wave|temperature|weather|flood"
    r"|electric.car|gig.worker|startup|ipo"
    r"|murder|rape|killed.in.crash|deportation|arrested|charged.in.death",
    re.IGNORECASE,
)

SUBREDDIT = os.environ.get("SUBREDDIT")
MAX_RETRIES = 5
RETRY_DELAY = 10
DEDUP_THRESHOLD = 0.55
REDDIT_DUP_THRESHOLD = 0.55


def decode_google_news_url(url):
    """Resolve Google News redirect URL to the original article URL."""
    if "news.google.com" not in url:
        return url
    try:
        result = new_decoderv1(url)
        if result.get("status"):
            return result["decoded_url"]
    except Exception as e:
        log.warning(f"Google News decode failed: {e}")
    return url


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


def deduplicate_articles(articles):
    """Remove articles covering the same story based on title similarity."""
    if not articles:
        return articles

    unique = []
    dropped = []
    for article in articles:
        is_dup = False
        for kept in unique:
            sim = title_similarity(article["title"], kept["title"])
            if sim > DEDUP_THRESHOLD:
                dropped.append((article["title"], kept["title"], sim))
                is_dup = True
                break
        if not is_dup:
            unique.append(article)

    if dropped:
        log.info(f"{CYAN}Cross-source dedup: {len(dropped)} duplicates removed ({len(articles)} → {len(unique)}){RESET}")
        for orig, kept, sim in dropped:
            log.info(f"  {DIM}├ Dropped: \"{orig}\"{RESET}")
            log.info(f"  {DIM}│  ({sim:.0%} match) → \"{kept}\"{RESET}")
    else:
        log.info(f"{CYAN}Cross-source dedup: no duplicates found ({len(articles)} articles){RESET}")

    return unique


# --- Reddit Duplicate Check ---

def fetch_recent_reddit_posts():
    """Fetch recent post titles from the subreddit using PRAW (new listing)."""
    try:
        reddit = initialize_reddit()
        subreddit = reddit.subreddit(SUBREDDIT)
        posts = []
        for post in subreddit.new(limit=200):
            posts.append({"title": post.title})
        log.info(f"{BLUE}Fetched {len(posts)} recent posts from r/{SUBREDDIT}{RESET}")
        return posts
    except Exception as e:
        log.warning(f"Failed to fetch Reddit posts: {e}")
        return []


def filter_already_posted(articles, reddit_posts):
    """Filter out articles already posted on Reddit. Returns (remaining, duplicates)."""
    remaining = []
    duplicates = []

    for article in articles:
        matched = None
        for post in reddit_posts:
            sim = title_similarity(article["title"], post["title"])
            if sim > REDDIT_DUP_THRESHOLD:
                matched = (post["title"], sim)
                break
        if matched:
            duplicates.append((article["title"], matched[0], matched[1]))
        else:
            remaining.append(article)

    if duplicates:
        log.info(f"{MAGENTA}Reddit dedup: {len(duplicates)} already posted ({len(articles)} → {len(remaining)}){RESET}")
        for orig, reddit_title, sim in duplicates:
            log.info(f"  {DIM}├ \"{orig}\"{RESET}")
            log.info(f"  {DIM}│  ({sim:.0%} match) → \"{reddit_title}\"{RESET}")
    else:
        log.info(f"{MAGENTA}Reddit dedup: no duplicates found ({len(articles)} articles){RESET}")

    return remaining


# --- RSS Feed ---

def fetch_news_article():
    """Fetch a deduplicated, non-reposted article from RSS feeds."""
    entries = []
    for feed_url in RSS_FEEDS:
        log.info(f"{DIM}Fetching: {feed_url[:70]}...{RESET}")
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if link and title and INDIA_PATTERN.search(title) and GEOPOLITICS_KEYWORDS.search(title) and not EXCLUDE_PATTERN.search(title):
                entries.append({"title": title, "url": decode_google_news_url(link)})

    log.info(f"{BLUE}Found {len(entries)} matching articles from RSS feeds{RESET}")
    if not entries:
        return None

    # Deduplicate same-story articles from different sources
    entries = deduplicate_articles(entries)
    if not entries:
        return None

    # Check against recent Reddit posts
    reddit_posts = fetch_recent_reddit_posts()
    entries = filter_already_posted(entries, reddit_posts)

    if not entries:
        log.warning("All articles already posted on Reddit")
        return None

    random.shuffle(entries)
    selected = entries[0]
    log.info(f"{GREEN}{BOLD}Selected: \"{selected['title']}\"{RESET}")
    return selected


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

    log.info(f"{GREEN}Posted: {submission.url}{RESET}")
    return submission


# --- Main ---

def main():
    log.info(f"{BOLD}{'═' * 50}{RESET}")
    log.info(f"{BOLD}  Auto Post News{RESET}")
    log.info(f"{BOLD}{'═' * 50}{RESET}")

    article = fetch_news_article()
    if not article:
        log.warning("No suitable article found. Exiting.")
        return

    log.info(f"{BLUE}Summarizing: {article['url']}{RESET}")
    summary = query_perplexity(
        f"Summarize this news article in 2-3 paragraphs for a geopolitics discussion forum: {article['title']} {article['url']} \n\n Make sure to include key facts, context, and implications. Avoid opinions or analysis. Focus on the who, what, when, where, and why. Donot ask any follow up questions."
    )
    if not summary or len(summary) < 160:
        log.error("Failed to get summary or summary too short. Exiting.")
        return

    log.info(f"{BLUE}Posting to Reddit...{RESET}")
    post_to_reddit(article, summary)
    log.info(f"{GREEN}{BOLD}Done ✓{RESET}")


if __name__ == "__main__":
    main()
