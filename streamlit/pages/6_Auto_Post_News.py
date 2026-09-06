"""
Auto Post News - Manual trigger page

Allows fetching RSS feed articles, browsing candidates, and posting
a selected article to Reddit with a single button click.
"""

import os
import sys
import re
import random
from datetime import datetime
from difflib import SequenceMatcher

import streamlit as st
import feedparser
import praw
from dotenv import load_dotenv

# Add project root to path so we can import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.perplexity import query_perplexity

load_dotenv()

st.set_page_config(page_title="Auto Post News", page_icon="📰", layout="wide")

st.title("📰 Auto Post News")
st.caption("Fetch geopolitics articles from RSS feeds and post to Reddit manually")

# --- Configuration (mirrors auto_post_news.py) ---

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
    "https://www.theguardian.com/world/india/rss",
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://www.firstpost.com/commonfeeds/v1/mfp/rss/world.xml",
    "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
    "https://news.google.com/rss/search?q=site:theprint.in/diplomacy+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=site:https://www.reuters.com/world/india/+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
]

INDIA_PATTERN = re.compile(r"\bindia\b|indian|modi|jaishankar|new delhi", re.IGNORECASE)

GEOPOLITICS_KEYWORDS = re.compile(
    r"geopolit|foreign policy|diplomacy|diplomatic|bilateral"
    r"|china|pakistan|united states|america|\bus\b.*(tariff|trade|sanction|strike)"
    r"|indo.pacific|brics|quad"
    r"|sanctions|trade war|tariff|alliance|treaty|summit"
    r"|military|defence cooperation|defense pact|nuclear|missile|drone strike"
    r"|iran|strait of hormuz|lng export"
    r"|border.*(dispute|tension|clash|standoff)"
    r"|ceasefire|armed conflict|invasion"
    r"|nato|asean|sco|g7|g20|un general assembly"
    r"|embassy|diplomat|extradition|territorial"
    r"|trump|biden|xi jinping|putin"
    r"|state visit|diplomatic.*(row|protest|ties|rift)"
    r"|seafarer|sailor.*(kill|attack|gulf)",
    re.IGNORECASE,
)

EXCLUDE_PATTERN = re.compile(
    r"cricket|\bipl\b|bbl|football|fifa|messi|sport"
    r"|bollywood|film|movie|music|grammy"
    r"|heat.?wave|temperature|weather|flood"
    r"|electric.car|gig.worker|startup|ipo"
    r"|murder|rape|killed.in.crash|deportation|arrested|charged.in.death"
    r"|stock.*(crash|rally|surge|slip|climb|fall|drop)|shares.*(climb|fall|rally|drop|surge)"
    r"|sensex|nifty|bse|nse|brokerage|infosys|tcs|wipro|hcl.tech"
    r"|iphone|android|smartphone|gadget"
    r"|school|college|exam|jee|neet|upsc"
    r"|railway|metro|highway|road.project"
    r"|pollution|waste|water.quality|sewage"
    r"|rupee|forex|currency.*(rise|fall|rebound|slip)",
    re.IGNORECASE,
)

SUBREDDIT = os.environ.get("SUBREDDIT")
DEDUP_THRESHOLD = 0.55
REDDIT_DUP_THRESHOLD = 0.55


# --- Helper functions ---

def title_similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def initialize_reddit():
    return praw.Reddit(
        client_id=os.environ.get("CLIENT_ID"),
        client_secret=os.environ.get("CLIENT_SECRET"),
        user_agent=f'AutoPostNews/1.0 by u/{os.environ.get("REDDIT_USERNAME")}',
        username=os.environ.get("REDDIT_USERNAME"),
        password=os.environ.get("PASSWORD"),
        check_for_async=False,
    )


def decode_google_news_url(url):
    """Resolve Google News redirect URL to the original article URL."""
    if "news.google.com" not in url:
        return url
    try:
        from googlenewsdecoder import new_decoderv1
        result = new_decoderv1(url)
        if result.get("status"):
            return result["decoded_url"]
    except Exception:
        pass
    return url


def fetch_articles_from_rss():
    """Fetch and filter articles from all RSS feeds."""
    entries = []
    total_entries = 0

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        total_entries += len(feed.entries)
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if not link or not title:
                continue
            if (INDIA_PATTERN.search(title)
                    and GEOPOLITICS_KEYWORDS.search(title)
                    and not EXCLUDE_PATTERN.search(title)):
                entries.append({
                    "title": title,
                    "url": link,
                    "_needs_decode": "news.google.com" in link,
                })

    # Decode Google News URLs
    for article in entries:
        if article.pop("_needs_decode", False):
            article["url"] = decode_google_news_url(article["url"])

    # Deduplicate
    unique = []
    for article in entries:
        is_dup = False
        for kept in unique:
            if title_similarity(article["title"], kept["title"]) > DEDUP_THRESHOLD:
                is_dup = True
                break
        if not is_dup:
            unique.append(article)

    return unique, total_entries


def fetch_recent_reddit_posts():
    """Fetch recent post titles from the subreddit."""
    try:
        reddit = initialize_reddit()
        subreddit = reddit.subreddit(SUBREDDIT)
        return [{"title": post.title} for post in subreddit.new(limit=200)]
    except Exception:
        return []


def filter_already_posted(articles, reddit_posts):
    """Filter out articles already posted on Reddit."""
    remaining = []
    already_posted = []
    for article in articles:
        matched = False
        for post in reddit_posts:
            if title_similarity(article["title"], post["title"]) > REDDIT_DUP_THRESHOLD:
                already_posted.append(article["title"])
                matched = True
                break
        if not matched:
            remaining.append(article)
    return remaining, already_posted


def post_article_to_reddit(article, summary):
    """Post the article to Reddit and add submission statement."""
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(SUBREDDIT)

    submission = subreddit.submit(
        title=article["title"],
        url=article["url"],
        send_replies=False,
    )

    ss_comment = f"Submission Statement: {summary}"
    submission.reply(body=ss_comment)

    return submission


# --- Streamlit UI ---

st.markdown("---")

# Step 1: Fetch articles
st.markdown("### 1️⃣ Fetch Articles from RSS Feeds")

if st.button("🔄 Fetch Articles", type="primary"):
    with st.spinner("Fetching RSS feeds and filtering articles..."):
        articles, total_rss = fetch_articles_from_rss()

    st.info(f"RSS total: **{total_rss}** entries → **{len(articles)}** after filtering & dedup")

    if articles:
        with st.spinner("Checking against recent Reddit posts..."):
            reddit_posts = fetch_recent_reddit_posts()
            articles, already_posted = filter_already_posted(articles, reddit_posts)

        if already_posted:
            st.warning(f"{len(already_posted)} article(s) already posted on Reddit (removed)")

        if articles:
            st.session_state["fetched_articles"] = articles
            st.session_state["fetch_time"] = datetime.now().strftime("%H:%M:%S")
            st.success(f"✅ Found **{len(articles)}** candidate articles ready to post")
        else:
            st.warning("All articles have already been posted on Reddit.")
            st.session_state.pop("fetched_articles", None)
    else:
        st.warning("No matching articles found in RSS feeds.")
        st.session_state.pop("fetched_articles", None)

# Step 2: Select article
if "fetched_articles" in st.session_state:
    articles = st.session_state["fetched_articles"]
    fetch_time = st.session_state.get("fetch_time", "")

    st.markdown("---")
    st.markdown("### 2️⃣ Select Article to Post")
    st.caption(f"Fetched at {fetch_time} — {len(articles)} candidates")

    # Display articles as a radio selection
    article_options = [f"**{a['title']}**\n{a['url']}" for a in articles]
    selected_idx = st.radio(
        "Choose an article:",
        range(len(articles)),
        format_func=lambda i: articles[i]["title"],
        key="article_selection",
    )

    selected_article = articles[selected_idx]

    # Show details of selected article
    st.markdown("**Selected:**")
    st.markdown(f"> {selected_article['title']}")
    st.markdown(f"🔗 [{selected_article['url']}]({selected_article['url']})")

    # Step 3: Post
    st.markdown("---")
    st.markdown("### 3️⃣ Post to Reddit")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Summarize", type="primary"):
            # Summarize
            import time as _time
            import logging
            import io

            # Capture perplexity logs into a string buffer
            _log_buffer = io.StringIO()
            _log_handler = logging.StreamHandler(_log_buffer)
            _log_handler.setLevel(logging.DEBUG)
            _log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))
            _perplexity_logger = logging.getLogger("perplexity")
            _perplexity_logger.setLevel(logging.DEBUG)
            _perplexity_logger.addHandler(_log_handler)

            _start = _time.time()
            with st.spinner("Generating summary via Perplexity AI..."):
                summary = query_perplexity(
                    f"Summarize this news article in 2-3 paragraphs for a geopolitics "
                    f"discussion forum: {selected_article['title']} {selected_article['url']}"
                    f"\n\nMake sure to include key facts, context, and implications. "
                    f"Avoid opinions or analysis. Focus on the who, what, when, where, and why. "
                    f"Do not ask any follow up questions."
                )
            _elapsed = _time.time() - _start
            _perplexity_logger.removeHandler(_log_handler)
            _captured_logs = _log_buffer.getvalue()

            if not summary or len(summary) < 160:
                st.error("❌ Failed to generate summary or summary too short. Try again.")
                with st.expander("🐛 Debug Info", expanded=True):
                    st.write(f"**Elapsed time:** {_elapsed:.1f}s")
                    st.write(f"**Summary length:** {len(summary) if summary else 0} chars (minimum: 160)")
                    st.write("**Raw summary returned:**")
                    st.code(repr(summary) if summary else "<empty string>", language=None)
                    st.write("**Perplexity Logs:**")
                    st.code(_captured_logs if _captured_logs else "<no logs captured>", language="log")
            else:
                st.session_state["generated_summary"] = summary
                st.rerun()

    with col2:
        if st.button("🎲 Pick Random Article"):
            random_idx = random.randint(0, len(articles) - 1)
            st.session_state["article_selection"] = random_idx
            st.session_state.pop("generated_summary", None)
            st.rerun()

    # Step 4: Edit & Post (shown after summary is generated)
    if "generated_summary" in st.session_state:
        st.markdown("---")
        st.markdown("### 4️⃣ Edit & Post")

        edited_summary = st.text_area(
            "Submission Statement (edit before posting):",
            value=st.session_state["generated_summary"],
            height=250,
            key="edited_summary",
        )

        char_count = len(edited_summary) if edited_summary else 0
        if char_count < 160:
            st.warning(f"⚠️ Summary too short ({char_count} chars, minimum 160)")

        post_col1, post_col2 = st.columns([1, 3])
        with post_col1:
            if st.button("📤 Post to Reddit", type="primary", disabled=(char_count < 160)):
                with st.spinner("Posting to Reddit..."):
                    try:
                        submission = post_article_to_reddit(selected_article, edited_summary)
                        st.success("✅ Posted successfully!")
                        st.markdown(f"🔗 [View on Reddit](https://www.reddit.com{submission.permalink})")
                        # Remove posted article from list
                        st.session_state["fetched_articles"] = [
                            a for a in articles if a["title"] != selected_article["title"]
                        ]
                        st.session_state.pop("generated_summary", None)
                    except Exception as e:
                        st.error(f"❌ Failed to post: {e}")
        with post_col2:
            if st.button("🗑️ Discard Summary"):
                st.session_state.pop("generated_summary", None)
                st.rerun()

    # Full list view
    st.markdown("---")
    st.markdown("### 📋 All Candidates")
    for i, article in enumerate(articles, 1):
        st.markdown(f"{i}. [{article['title']}]({article['url']})")
