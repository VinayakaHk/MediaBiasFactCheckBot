import re
import feedparser

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
    "https://www.theguardian.com/world/india/rss",
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://www.firstpost.com/commonfeeds/v1/mfp/rss/world.xml",
    "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
]

# Option A: India-relational compound patterns
OPTION_A = re.compile(
    r"india.*(geopolit|foreign policy|diplomacy|bilateral|strategic|sanctions|trade war|alliance|treaty|border)"
    r"|india.*(china|pakistan|us|indo.pacific|brics|quad)"
    r"|(china|pakistan|us|indo.pacific|brics|quad).*india"
    r"|jaishankar|modi.*(diplomacy|foreign|bilateral|summit|trade|tariff)"
    r"|indo.pacific|india.us|us.india|india.china|india.pakistan"
    r"|indian.foreign.policy|indian.diplomacy|india.*tariff|tariff.*india",
    re.IGNORECASE,
)

# Option B (refined): Two-step check with tighter keywords + negative filter
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

# Fetch all entries
all_entries = []
for url in RSS_FEEDS:
    print(f"\n{'='*80}\n{url}\n{'='*80}")
    feed = feedparser.parse(url)
    for i, e in enumerate(feed.entries, 1):
        title = e.get("title", "")
        link = e.get("link", "")
        print(f"  {i}. {title} | {link}")
        all_entries.append({"title": title, "url": link})

# Filter with Option A
filtered_a = [a for a in all_entries if a["title"] and OPTION_A.search(a["title"])]

# Filter with Option B (refined)
filtered_b = [a for a in all_entries if a["title"] and INDIA_PATTERN.search(a["title"]) and GEOPOLITICS_KEYWORDS.search(a["title"]) and not EXCLUDE_PATTERN.search(a["title"])]

print(f"\n{'='*80}\nOption A (compound patterns): {len(filtered_a)} articles\n{'='*80}")
for i, a in enumerate(filtered_a, 1):
    print(f"  {i}. {a['title']}\n     {a['url']}")

print(f"\n{'='*80}\nOption B (India check + geopolitics keywords): {len(filtered_b)} articles\n{'='*80}")
for i, a in enumerate(filtered_b, 1):
    print(f"  {i}. {a['title']}\n     {a['url']}")
