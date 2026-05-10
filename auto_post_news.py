"""
auto_post_news.py - Standalone script to fetch Indian geopolitics news from RSS feeds,
summarize via Perplexity AI, and post to Reddit as a link submission with SS comment.

Usage: python auto_post_news.py
Intended to run via crontab twice daily (morning + evening).
"""

import os
import re
import random
import platform

import feedparser
import praw
from dotenv import load_dotenv

from src.perplexity import query_perplexity

load_dotenv()

# --- Configuration ---

RSS_FEEDS = [
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://indianexpress.com/section/india/feed/",
    "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",  # TOI World
    "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
]

# Articles must match at least one of these patterns in the title
GEOPOLITICS_KEYWORDS = re.compile(
    r"geopolit|foreign policy|diplomacy|bilateral|strategic|defence|defense|military"
    r"|border|china|pakistan|us.india|indo.pacific|jaishankar|modi|nato|brics"
    r"|sanctions|trade war|alliance|treaty|nuclear|missile|navy|airforce",
    re.IGNORECASE,
)

SUBREDDIT = os.environ.get("SUBREDDIT")
MAX_RETRIES = 5
RETRY_DELAY = 10


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


# --- RSS Feed ---

def fetch_news_article():
    """Fetch a random recent article from RSS feeds about Indian geopolitics."""
    entries = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if link and title and re.search(r"india", title, re.IGNORECASE) and GEOPOLITICS_KEYWORDS.search(title):
                entries.append({"title": title, "url": link})

    if not entries:
        print("No geopolitics articles found in RSS feeds.")
        return None

    random.shuffle(entries)
    return entries[0]


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

    print(f"Posted: {submission.url}")
    print(f"Title: {article['title']}")
    return submission


# --- Main ---

def main():
    print("Fetching news article...")
    article = fetch_news_article()
    if not article:
        print("No suitable article found. Exiting.")
        return

    print(f"Found: {article['title']}")
    print(f"URL: {article['url']}")

    print("Summarizing with Perplexity...")
    summary = query_perplexity(
        f"Summarize this news article in 2-3 paragraphs for a geopolitics discussion forum: {article['title']} {article['url']} \n\n Make sure to include key facts, context, and implications. Avoid opinions or analysis. Focus on the who, what, when, where, and why. Donot ask any follow up questions."
    )
    if not summary or len(summary) < 160:
        print("Failed to get summary or summary too short. Exiting.")
        return

    print("Posting to Reddit...")
    post_to_reddit(article, summary)
    print("Done.")


if __name__ == "__main__":
    main()
