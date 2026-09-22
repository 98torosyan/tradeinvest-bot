"""
Pulls the latest crypto headlines from free public RSS feeds
(no API key needed). Used to find today's "why it matters" angle
and to flag Breaking News content per the brief.
"""
import feedparser

from config import NEWS_RSS_FEEDS, MAX_HEADLINES

BREAKING_KEYWORDS = [
    "hack", "exploit", "SEC", "lawsuit", "ETF", "approve", "ban",
    "Fed", "FOMC", "rate", "regulation", "halt", "liquidation",
]


def fetch_headlines():
    """Returns a list of {title, link, source, is_breaking} dicts, newest first."""
    headlines = []
    for feed_url in NEWS_RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            source = parsed.feed.get("title", feed_url)
            for entry in parsed.entries[: MAX_HEADLINES]:
                title = entry.get("title", "").strip()
                if not title:
                    continue
                headlines.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "source": source,
                    "is_breaking": any(k.lower() in title.lower() for k in BREAKING_KEYWORDS),
                })
        except Exception as exc:
            print(f"[fetch_news] failed for {feed_url}: {exc}")
    # Breaking items first, then the rest, capped at MAX_HEADLINES total
    headlines.sort(key=lambda h: not h["is_breaking"])
    return headlines[:MAX_HEADLINES]
