import feedparser
from googlenewsdecoder import new_decoderv1

feed = feedparser.parse("https://news.google.com/rss/search?q=site:https://www.reuters.com/world/india/&hl=en-IN&gl=IN&ceid=IN:en")
for e in feed.entries[:5]:
    google_url = e.get("link")
    result = new_decoderv1(google_url)
    real_url = result.get("decoded_url", google_url) if result.get("status") else google_url
    print(f"{e.get('title')}\n  -> {real_url}\n")
