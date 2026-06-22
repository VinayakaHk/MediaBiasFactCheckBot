# auto_post_news.py

Standalone script to auto-post Indian geopolitics news to Reddit.

## Overview

1. Fetches articles from multiple RSS feeds (BBC, Guardian, The Hindu, Firstpost, TOI, Hindustan Times, ThePrint, Reuters).
2. Filters articles using a 3-step regex system:
   - **INDIA_PATTERN**: Must mention India/Indian/Modi/Jaishankar/New Delhi.
   - **GEOPOLITICS_KEYWORDS**: Must match geopolitics terms (diplomacy, tariff, war, etc.).
   - **EXCLUDE_PATTERN**: Rejects sports, entertainment, weather, crime, and domestic stories.
3. Deduplicates articles across sources using title similarity (55% threshold).
4. Checks against the last 200 Reddit posts to avoid reposting (URL + title similarity).
5. Summarizes the selected article via Perplexity AI.
6. Posts the article URL as a link submission and adds the summary as a Submission Statement comment.

## RSS Feeds

- BBC News India: `https://feeds.bbci.co.uk/news/world/asia/india/rss.xml`
- The Guardian India: `https://www.theguardian.com/world/india/rss`
- The Hindu International: `https://www.thehindu.com/news/international/feeder/default.rss`
- Firstpost World: `https://www.firstpost.com/commonfeeds/v1/mfp/rss/world.xml`
- Times of India: `https://timesofindia.indiatimes.com/rssfeeds/1898055.cms`
- Hindustan Times World: `https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml`
- ThePrint Diplomacy (via Google News): `https://news.google.com/rss/search?q=site:theprint.in/diplomacy`
- Reuters India (via Google News): `https://news.google.com/rss/search?q=site:https://www.reuters.com/world/india/`

Google News redirect URLs are automatically decoded to original article URLs using `googlenewsdecoder`.

## Dependencies

```
feedparser
praw
python-dotenv
googlenewsdecoder
```

Also requires `src/perplexity.py` (Perplexity AI query module).

## Environment Variables

Uses the same `.env` as the main bot:
- `CLIENT_ID`, `CLIENT_SECRET`, `REDDIT_USERNAME`, `PASSWORD`, `SUBREDDIT`

## Article Filtering

### INDIA_PATTERN (title must match)
Matches: `india`, `indian`, `modi`, `jaishankar`, `new delhi`

### GEOPOLITICS_KEYWORDS (title must match)
- Diplomacy: geopolitics, foreign policy, diplomacy, diplomatic, bilateral
- Countries: china, pakistan, united states, america, US (only with tariff/trade/sanction/strike)
- Groupings: indo-pacific, brics, quad
- Trade: sanctions, trade war, tariff, alliance, treaty, summit
- Security: military, defence cooperation, defense pact, nuclear, missile, drone strike
- Energy/Middle East: iran, strait of hormuz, lng export
- Conflict: border (with dispute/tension/clash/standoff), ceasefire, armed conflict, invasion
- Organizations: nato, asean, sco, g7, g20, un general assembly
- Diplomatic terms: embassy, diplomat, extradition, territorial
- Leaders: trump, biden, xi jinping, putin
- Events: state visit, diplomatic (row/protest/ties/rift)
- Maritime: seafarer/sailor (with kill/attack/gulf)

### EXCLUDE_PATTERN (title must NOT match)
- Sports: cricket, ipl, bbl, football, fifa, messi, sport
- Entertainment: bollywood, film, movie, music, grammy
- Weather: heatwave, temperature, weather, flood
- Domestic/Tech: electric car, gig worker, startup, ipo
- Crime: murder, rape, killed in crash, deportation, arrested, charged in death
- Stocks/Finance: stock (crash/rally/surge/slip/fall/drop), shares (climb/fall/rally/drop/surge), sensex, nifty, bse, nse, brokerage, infosys, tcs, wipro, hcl tech
- Gadgets: iphone, android, smartphone, gadget
- Education: school, college, exam, jee, neet, upsc
- Infrastructure: railway, metro, highway, road project
- Environment: pollution, waste, water quality, sewage
- Currency: rupee, forex, currency (rise/fall/rebound/slip)

## Deduplication

- **Cross-source**: Articles from different feeds covering the same story are deduplicated using SequenceMatcher title similarity (>55% = duplicate).
- **Reddit check**: Fetches last 200 posts from the subreddit and compares by normalized URL (exact match) and title similarity (>55%).

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

### Dry Run

Test filtering and deduplication without summarizing or posting:

```bash
python auto_post_news.py --dry-run
```
