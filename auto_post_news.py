"""
auto_post_news.py - Standalone script to fetch Indian geopolitics news from RSS feeds,
summarize via Perplexity AI (Selenium), and post to Reddit as a link submission with SS comment.

Usage: python auto_post_news.py
Intended to run via crontab twice daily (morning + evening).
"""

import os
import re
import time
import random
import platform
import urllib.parse

import feedparser
import praw
from dotenv import load_dotenv
from markdownify import markdownify as md

from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

try:
    from pyvirtualdisplay import Display
except ImportError:
    Display = None

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
FIREFOX_DRIVER_PATH = "/opt/homebrew/bin/geckodriver"
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


# --- Perplexity Summarization ---

def summarize_with_perplexity(article_url, article_title):
    """Use Selenium to query Perplexity AI for a summary of the article."""
    query = f"Summarize this news article in 2-3 paragraphs for a geopolitics discussion forum: {article_title} {article_url}"
    encoded_url = urllib.parse.quote(query)
    perplexity_url = f"https://www.perplexity.ai/search?q={encoded_url}"

    driver = None
    display = None
    answer = ""

    try:
        for attempt in range(MAX_RETRIES):
            try:
                if platform.machine() == "aarch64" and platform.system() == "Linux" and Display:
                    display = Display(visible=False, size=(800, 600))
                    display.start()
                if platform.system() == "Darwin":
                    service = Service(FIREFOX_DRIVER_PATH)
                    driver = webdriver.Firefox(options=firefox_options, service=service)
                elif platform.system() == "Linux":
                    options = uc.ChromeOptions()
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--window-size=1920,1080")
                    options.add_argument("--headless=new")
                    options.binary_location = "/usr/bin/chromium-browser"
                    driver = uc.Chrome(options=options, driver_executable_path="/usr/bin/chromedriver")
                else:
                    driver = uc.Chrome()

                driver.get(perplexity_url)

                WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Follow-ups')]"))
                )
                dynamic_elements = WebDriverWait(driver, 40).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "prose"))
                )

                if dynamic_elements:
                    for element in dynamic_elements:
                        html_content = element.get_attribute("innerHTML")
                        answer = md(html_content)
                    break

            except (WebDriverException, TimeoutException) as e:
                print(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                time.sleep(RETRY_DELAY)
            finally:
                if driver:
                    driver.quit()
                    driver = None
                if display:
                    display.stop()
                    display = None

    except Exception as e:
        print(f"Summarization error: {e}")

    return format_for_reddit(answer) if answer else ""


def format_for_reddit(text):
    """Clean up Perplexity output for Reddit."""
    # Remove citation links [number](url) -> [[domain]](url)
    pattern = r'\[(\d+)\]\((https?://[^)]+)\)'

    def replace_citation(match):
        url = match.group(2)
        domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if domain:
            return f" [[{domain.group(1)}]]({url}) "
        return match.group(0)

    text = re.sub(pattern, replace_citation, text)
    text = re.sub(r'\w*\+\d+', '', text)
    return text.strip()


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
    summary = summarize_with_perplexity(article["url"], article["title"])
    if not summary or len(summary) < 160:
        print("Failed to get summary or summary too short. Exiting.")
        return

    print("Posting to Reddit...")
    post_to_reddit(article, summary)
    print("Done.")


if __name__ == "__main__":
    main()
