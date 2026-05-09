# auto_post_news.py

Standalone script to auto-post Indian geopolitics news to Reddit.

## Overview

1. Fetches articles from Google News RSS feeds (queries: "india geopolitics", "india foreign policy").
2. Picks a random article.
3. Summarizes it via Perplexity AI using Selenium.
4. Posts the article URL as a link submission to the configured subreddit.
5. Comments the summary as a Submission Statement.

## Dependencies

```
feedparser
praw
markdownify
selenium
undetected-chromedriver
pyvirtualdisplay  # Linux only
```

## Environment Variables

Uses the same `.env` as the main bot:
- `CLIENT_ID`, `CLIENT_SECRET`, `REDDIT_USERNAME`, `PASSWORD`, `SUBREDDIT`

## Platform Handling

- **macOS**: Firefox via geckodriver (`/opt/homebrew/bin/geckodriver`)
- **Linux (aarch64)**: undetected-chromedriver with Xvfb

## Crontab Setup

Run twice daily (8 AM and 6 PM IST):

```bash
crontab -e
```

Add:
```
0 8 * * * cd /Users/vinayakahk/Projects/MediaBiasFactCheckBot && /Users/vinayakahk/Projects/MediaBiasFactCheckBot/.venv/bin/python auto_post_news.py >> /tmp/auto_post_news.log 2>&1
0 18 * * * cd /Users/vinayakahk/Projects/MediaBiasFactCheckBot && /Users/vinayakahk/Projects/MediaBiasFactCheckBot/.venv/bin/python auto_post_news.py >> /tmp/auto_post_news.log 2>&1
```

## Manual Run

```bash
python auto_post_news.py
```
