"""Picks one fresh crypto headline and asks Gemini to turn it into the
'News -> What it means -> What it means for you' Reel script in Armenian."""
import html
import re
from urllib.parse import urlparse

import feedparser

from . import gemini
from .builder import ICONS

FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
]
SOURCE_NAMES = {"coindesk.com": "CoinDesk", "cointelegraph.com": "Cointelegraph", "decrypt.co": "Decrypt"}
BANNED = ["guarantee", "risk-free", "100%", "երաշխավորված շահույթ", "անպայման կաճ", "անպայման կընկն", "գնիր հիմա", "վաճառիր հիմա"]


def _clean(s, n=600):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    return re.sub(r"\s+", " ", s).strip()[:n]


def fetch_items(exclude, per_feed=10):
    items = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[news] feed failed {url}: {exc}"); continue
        for e in feed.entries[:per_feed]:
            link = e.get("link", "")
            if not link or link in exclude:
                continue
            host = urlparse(link).netloc.replace("www.", "")
            items.append({"title": _clean(e.get("title"), 200), "summary": _clean(e.get("summary") or e.get("description")),
                          "link": link, "source": SOURCE_NAMES.get(host, host)})
    return items


PROMPT = """You are the editor of TradeInvest (@armtradeinvest), an Armenian-language Instagram page that explains crypto news simply for beginners.

From the numbered news items below, choose ONE item that is most useful and important for an Armenian crypto audience (regulation, major companies, ETFs, adoption, security incidents affecting users, macro events that move crypto).
NEVER choose: deaths, violence, crimes against persons, personal tragedies, rumors, sponsored/press-release content, price predictions, gossip. If no item is suitable, return {{"skip": true}}.

Write a short vertical-video script in modern, simple, natural Eastern Armenian. Keep well-known terms in Latin letters (Bitcoin, Ethereum, ETF, SEC, stablecoin, blockchain).
STRICT FACT RULE: use ONLY facts stated in the chosen item's title and summary. Never invent numbers, names, dates, quotes or causes. If a detail is not in the text, do not mention it.
No financial advice, no predictions, no words like "guaranteed", "risk-free", "buy now", "100%".

Return ONLY this JSON:
{{
 "skip": false,
 "index": <number of the chosen item>,
 "headline": "<factual Armenian headline, max 70 characters>",
 "sub": "<optional context line, max 60 characters, or empty string>",
 "big": <null, or {{"value": <number from the text>, "prefix": "<e.g. $ or empty>", "suffix": "<e.g. ' մլն' or '%' or empty>"}} only if one key number is in the text>,
 "steps": [
  {{"title": "<Step 1: explain the key term or who is involved, e.g. 'Ի՞նչ է SEC-ը' or 'Ո՞վ է MoonPay-ը', max 22 characters>", "icon": "<icon>", "paragraphs": [{{"text": "<max 110 characters>", "em": false}}]}},
  {{"title": "Ի՞նչ է նշանակում", "icon": "<icon>", "paragraphs": [{{"text": "<max 110 characters>", "em": false}}, {{"text": "<key takeaway, max 80 characters>", "em": true}}]}},
  {{"title": "Քեզ ի՞նչ", "icon": "<icon>", "paragraphs": [{{"text": "<what it means for an ordinary person, max 110 characters>", "em": false}}, {{"text": "<calm, neutral reminder, max 80 characters>", "em": true}}]}}
 ],
 "caption": "<2-4 Armenian sentences summarising the news, then a new line 'Աղբյուր՝ SOURCE', then a new line with 4-5 hashtags like #crypto #bitcoin #կրիպտո #հայերեն>"
}}
Allowed icons: {icons}

News items:
{items}
"""


def _validate(d, n_items):
    errs = []
    if not isinstance(d.get("index"), int) or not (0 <= d["index"] < n_items):
        errs.append("index out of range")
    if not d.get("headline") or len(d["headline"]) > 90:
        errs.append("headline missing or longer than 90 chars")
    steps = d.get("steps") or []
    if len(steps) != 3:
        errs.append("steps must have exactly 3 items")
    for st in steps:
        if not st.get("title") or len(st["title"]) > 30:
            errs.append(f"step title too long: {st.get('title')}")
        ps = st.get("paragraphs") or []
        if not 1 <= len(ps) <= 2:
            errs.append("each step needs 1-2 paragraphs")
        for p in ps:
            if not p.get("text") or len(p["text"]) > 140:
                errs.append(f"paragraph too long: {p.get('text', '')[:40]}")
        if st.get("icon") not in ICONS:
            st["icon"] = "bulb"
    blob = str(d).lower()
    for b in BANNED:
        if b in blob:
            errs.append(f"banned phrase: {b}")
    if d.get("sub") and len(d["sub"]) > 80:
        d["sub"] = ""
    return errs


def make_spec(exclude):
    items = fetch_items(set(exclude))
    if not items:
        print("[news] no fresh items"); return None
    listing = "\n".join(f"[{i}] {it['source']}: {it['title']}\n    {it['summary']}" for i, it in enumerate(items))
    prompt = PROMPT.format(icons=", ".join(ICONS), items=listing)
    for attempt in range(2):
        d = gemini.generate_json(prompt)
        if d.get("skip"):
            print("[news] Gemini found nothing suitable"); return None
        errs = _validate(d, len(items))
        if not errs:
            it = items[d["index"]]
            d["link"], d["source"] = it["link"], it["source"]
            if "Աղբյուր" not in d.get("caption", ""):
                d["caption"] = d.get("caption", "") + f"\n\nԱղբյուր՝ {it['source']}"
            return d
        print(f"[news] attempt {attempt + 1} invalid: {errs}")
        prompt += "\n\nYour previous answer had these problems, fix them: " + "; ".join(errs)
    return None
