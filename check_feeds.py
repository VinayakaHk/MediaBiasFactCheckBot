import re
import feedparser
from googlenewsdecoder import new_decoderv1


def decode_google_news_url(url):
    if "news.google.com" not in url:
        return url
    try:
        result = new_decoderv1(url)
        if result.get("status"):
            return result["decoded_url"]
    except Exception:
        pass
    return url

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

# Fetch all entries
all_entries = []
for url in RSS_FEEDS:
    print(f"\n{'='*80}\n{url}\n{'='*80}")
    feed = feedparser.parse(url)
    for i, e in enumerate(feed.entries, 1):
        title = e.get("title", "")
        link = decode_google_news_url(e.get("link", ""))
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


# --- Filter Validation ---

def should_post(title):
    return (
        bool(INDIA_PATTERN.search(title))
        and bool(GEOPOLITICS_KEYWORDS.search(title))
        and not bool(EXCLUDE_PATTERN.search(title))
    )

reject = [
    # Original test cases
    "Infosys, TCS & other Indian IT stocks crash! How Accenture's warning has led to big sell-off",
    "Indian shares climb on Gulf peace deal tracking global rally - Reuters",
    "Indian officials survey farms around Tata iPhone parts plant after water pollution warning - Reuters",
    "Kids born and raised in America asked to 'tone down a bit' after joining Indian school",
    "Synergy of steel & software: How Indian Railways got on the digital track",
    "India vs Australia 3rd Test: Day 2 highlights from cricket",
    "Indian startup raises $50M in Series B IPO buzz",
    # From live RSS feeds
    "India's cash transfer boom gives relief to the poor but strains budgets",
    "The artificial ice pyramids saving India's mountain villages",
    "Indian teenager dies in horse-drawn carriage accident in New York",
    "India: Why a country of 1.4 billion is not in the football World Cup",
    "Delhi's temperature showed 43.5C. Why did it feel hotter?",
    "India's Nifty IT index at three-year low as bellwether Accenture flags weak outlook - Reuters",
    "India shares drop as IT declines on Accenture shock - Reuters",
    "India's long-delayed NSE IPO sets up $2.6 billion windfall for top investors - Reuters",
    "Gold price prediction: What's the outlook for gold prices on June 19, 2026",
    "Why is stock market down today? BSE Sensex drops over 800 points, Nifty50 below 24,000",
    "How Indian teen tourist's death may lead to ban on New York's 150-year old horse-drawn carriages",
    "Telegram loses bid to overturn India's temporary blocking of the app - Reuters",
    "Indian shares continue to rise as softer oil overpowers hawkish Fed - Reuters",
    "Cactus Pears review - tender and subtle story of forbidden love in India",
    "A year on, six questions still haunt the Air India crash investigation",
    "India temporarily bans Telegram over exam paper leak concerns",
    "Rupee rebounds 20 paise to 94.20 on hopes of India-US trade deal",
]

accept = [
    # Original test cases
    "India-China border standoff: Troops disengage at key LAC points",
    "Modi meets Biden at G20 summit, signs bilateral defence cooperation pact",
    "India imposes sanctions on Pakistan-based terror groups after diplomatic row",
    "Jaishankar at ASEAN: India pushes for Indo-Pacific maritime code",
    "India and Iran sign Chabahar port deal amid US sanctions threat",
    "Indian diplomat expelled from Canada over extradition dispute",
    "India joins BRICS push to challenge dollar dominance in trade",
    # From live RSS feeds
    "Trump says he will visit India as frosty relationship with Modi thaws",
    "Indian outrage over US killing of sailors mounts as leaders attend G7 summit",
    "Delhi issues strong protest after US strikes kill three Indian seafarers in Gulf",
    "Trump, Modi discuss trade, safety of Indian sailors in Gulf region - Reuters",
]

print(f"\n{'='*80}\nFILTER VALIDATION\n{'='*80}")
print("\nShould be REJECTED:")
all_pass = True
for t in reject:
    result = should_post(t)
    status = "FAIL" if result else " ok "
    icon = "✓ POSTED" if result else "✗ blocked"
    print(f"  [{status}] {icon} | {t[:75]}")
    if result:
        all_pass = False

print("\nShould be ACCEPTED:")
for t in accept:
    result = should_post(t)
    status = " ok " if result else "FAIL"
    icon = "✓ POSTED" if result else "✗ blocked"
    print(f"  [{status}] {icon} | {t[:75]}")
    if not result:
        all_pass = False

print(f"\n{'='*80}")
print("ALL TESTS PASSED ✓" if all_pass else "SOME TESTS FAILED ✗")
print(f"{'='*80}")
