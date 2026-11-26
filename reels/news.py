"""News 2.0: many outlets → stories grouped across outlets → only stories confirmed by ≥2 independent sources →
Gemini writes the Armenian script from ALL confirming texts → every number in it is checked against the sources.
Script shape: 'News -> What it means -> What it means for you'."""
import calendar
import time
import html
import re
from urllib.parse import urlparse

import feedparser
import requests

from . import gemini
from .builder import ICONS

FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    "https://www.theblock.co/rss.xml",
    "https://cryptoslate.com/feed/",
    "https://cryptonews.com/news/feed/",
    "https://bitcoinist.com/feed/",
    "https://u.today/rss",
]
SOURCE_NAMES = {"coindesk.com": "CoinDesk", "cointelegraph.com": "Cointelegraph", "decrypt.co": "Decrypt",
                "theblock.co": "The Block", "cryptoslate.com": "CryptoSlate", "cryptonews.com": "Cryptonews",
                "bitcoinist.com": "Bitcoinist", "u.today": "U.Today"}
MAX_AGE_H = 18
MIN_SOURCES = 2
NOTES = []


def note(msg):
    print(msg); NOTES.append(msg)


BANNED = ["guarantee", "risk-free", "100%", "երաշխավորված շահույթ", "անպայման կաճ", "անպայման կընկն", "գնիր հիմա", "վաճառիր հիմա"]


def _clean(s, n=600):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    return re.sub(r"\s+", " ", s).strip()[:n]


def fetch_items(exclude, per_feed=25):
    items = []
    for url in FEEDS:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (TradeInvest bot)"}, timeout=25)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            note(f"[news] {url}: {len(feed.entries)} items")
        except Exception as exc:  # noqa: BLE001
            note(f"[news] feed failed {url}: {str(exc)[:150]}"); continue
        for e in feed.entries[:per_feed]:
            link = e.get("link", "")
            if not link or link in exclude:
                continue
            host = urlparse(link).netloc.replace("www.", "")
            tp = e.get("published_parsed") or e.get("updated_parsed")
            age_h = (time.time() - calendar.timegm(tp)) / 3600 if tp else 6.0
            if age_h > MAX_AGE_H:
                continue
            items.append({"title": _clean(e.get("title"), 200), "summary": _clean(e.get("summary") or e.get("description")),
                          "link": link, "source": SOURCE_NAMES.get(host, host), "age_h": round(age_h, 1)})
    return items


# ---------------------------------------------------------------- cross-source confirmation
STOP = set("""the a an and or of to in on for with from by at as is are was were be been has have had will would
can could may might its it this that these those after before over under into amid about than more most new says said
report reports according week today year crypto cryptocurrency market markets price prices token tokens coin coins
analyst analysts first first-ever amid just now could their they them what why how when where which while""".split())
WEIGHTS = {"etf": 4, "sec": 4, "fed": 4, "blackrock": 4, "hack": 4, "hacked": 4, "exploit": 4, "stolen": 4,
           "binance": 3, "coinbase": 3, "tether": 3, "regulation": 3, "law": 3, "bill": 3, "ban": 3, "approve": 3,
           "approves": 3, "approved": 3, "reserve": 3, "record": 2, "bitcoin": 2, "ethereum": 2, "stablecoin": 2,
           "trump": 2, "cpi": 3, "rate": 2, "liquidations": 2, "billion": 2, "lawsuit": 2, "court": 2}


def _keys(it):
    words = re.findall(r"[A-Za-z][A-Za-z0-9.\-]+|\d[\d.,]*", it["title"])
    return {w.lower().strip(".,") for w in words if w.lower() not in STOP and (len(w) > 3 or w[0].isdigit() or w.isupper())}


def clusters(items):
    """Group items about the same story. Two items match when their titles share ≥3 key words, or ≥2 incl. a name/number."""
    for it in items:
        it["keys"] = _keys(it)
    groups = []
    for it in items:
        best = None
        for g in groups:
            common = it["keys"] & g["keys"]
            strong = any(w[0].isdigit() or w in WEIGHTS for w in common) or any(w[:1].isupper() for w in common)
            if len(common) >= 3 or (len(common) >= 2 and strong):
                best = g; break
        if best:
            best["items"].append(it); best["keys"] |= it["keys"]
        else:
            groups.append({"items": [it], "keys": set(it["keys"])})
    out = []
    for g in groups:
        srcs = []
        for it in g["items"]:
            if it["source"] not in srcs:
                srcs.append(it["source"])
        imp = sum(WEIGHTS.get(w, 0) for w in g["keys"])
        fresh = min(it["age_h"] for it in g["items"])
        out.append({"items": g["items"], "sources": srcs, "score": 5 * len(srcs) + min(imp, 12) - fresh / 4})
    return sorted(out, key=lambda c: c["score"], reverse=True)


NUM = re.compile(r"\d+(?:[.,]\d+)?")


def _nums(s):
    return {n.replace(",", ".").rstrip(".0") or "0" for n in NUM.findall(s or "")}


def numbers_ok(d, cluster):
    """Every number in the Armenian script must appear in at least one confirming source text."""
    src = " ".join(it["title"] + " " + it["summary"] for it in cluster["items"])
    have = _nums(src.replace(",", ""))
    blob = " ".join([d.get("headline", ""), d.get("sub", "")] + [p["text"] for st in d.get("steps", []) for p in st.get("paragraphs", [])])
    if d.get("big"):
        blob += f" {d['big'].get('value')}"
    bad = [n for n in _nums(blob.replace(",", "")) if n not in have and n not in ("1", "2", "3")]
    return bad


PROMPT = """You are the editor of TradeInvest (@armtradeinvest), an Armenian-language Instagram page that explains crypto news simply for beginners.

Below are numbered STORIES. Each story was reported by several independent outlets (their texts are listed under it).
Choose ONE story that is most useful and important for an Armenian crypto audience (regulation, major companies, ETFs, adoption, security incidents affecting users, macro events that move crypto).
NEVER choose: deaths, violence, crimes against persons, personal tragedies, rumors, sponsored/press-release content, price predictions, gossip. If no item is suitable, return {{"skip": true}}.

Write a short vertical-video script in modern, simple, natural Eastern Armenian. Keep well-known terms in Latin letters (Bitcoin, Ethereum, ETF, SEC, stablecoin, blockchain).
STRICT FACT RULE: use ONLY facts stated in the chosen story's texts, and prefer facts that more than one outlet states. If outlets disagree on a detail (a number, a name), leave that detail out. Never invent numbers, names, dates, quotes or causes. Copy numbers exactly as the sources write them.
No financial advice, no predictions, no words like "guaranteed", "risk-free", "buy now", "100%".

Return ONLY this JSON:
{{
 "skip": false,
 "index": <number of the chosen story>,
 "headline": "<factual Armenian headline, max 70 characters>",
 "sub": "<optional context line, max 60 characters, or empty string>",
 "big": <null, or {{"value": <number from the text>, "prefix": "<e.g. $ or empty>", "suffix": "<e.g. ' մլն' or '%' or empty>"}} only if one key number is in the text>,
 "steps": [
  {{"title": "<Step 1: explain the key term or who is involved, e.g. 'Ի՞նչ է SEC-ը' or 'Ո՞վ է MoonPay-ը', max 22 characters>", "icon": "<icon>", "paragraphs": [{{"text": "<max 110 characters>", "em": false}}]}},
  {{"title": "Ի՞նչ է նշանակում", "icon": "<icon>", "paragraphs": [{{"text": "<max 110 characters>", "em": false}}, {{"text": "<key takeaway, max 80 characters>", "em": true}}]}},
  {{"title": "Քեզ ի՞նչ", "icon": "<icon>", "paragraphs": [{{"text": "<what it means for an ordinary person, max 110 characters>", "em": false}}, {{"text": "<calm, neutral reminder, max 80 characters>", "em": true}}]}}
 ],
 "broll": "<2-4 English words for a calm cinematic background video that fits this news, e.g. 'city skyline night', 'gold bars', 'server room lights', 'abstract blue light'. No people, no faces, no logos, no brand names, and no screens with numbers or text (they would compete with our own text)>",
 "caption": "<2-4 Armenian sentences summarising the news, then a new line 'Աղբյուր՝ SOURCE', then a new line with 4-5 hashtags like #crypto #bitcoin #կրիպտո #հայերեն>"
}}
Allowed icons: {icons}

Stories:
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
    b = str(d.get("broll") or "")
    if not b or len(b) > 40 or not b.isascii():
        d["broll"] = ""
    if d.get("sub") and len(d["sub"]) > 80:
        d["sub"] = ""
    return errs


def make_spec(exclude, min_sources=MIN_SOURCES):
    items = fetch_items(set(exclude))
    if not items:
        note("[news] no fresh items"); return None
    cl = [c for c in clusters(items) if len(c["sources"]) >= min_sources][:6]
    note(f"[news] {len(items)} fresh items → {len(cl)} stories confirmed by ≥{min_sources} sources")
    if not cl:
        return None
    listing = "\n\n".join(f"[{i}] reported by {', '.join(c['sources'])}\n" +
                           "\n".join(f"    - {it['source']}: {it['title']} — {it['summary'][:350]}" for it in c["items"][:4])
                           for i, c in enumerate(cl))
    prompt = PROMPT.format(icons=", ".join(ICONS), items=listing)
    for attempt in range(3):
        d = gemini.generate_json(prompt)
        if d.get("skip"):
            note("[news] Gemini found nothing suitable"); return None
        errs = _validate(d, len(cl))
        if not errs:
            bad = numbers_ok(d, cl[d["index"]])
            if bad:
                errs.append(f"numbers not found in the sources: {bad} — remove them or copy them exactly")
        if not errs:
            c = cl[d["index"]]
            d["link"] = c["items"][0]["link"]
            d["links"] = [it["link"] for it in c["items"]]
            d["source"] = ", ".join(c["sources"][:3])
            d["n_sources"] = len(c["sources"])
            cap = re.sub(r"\n*Աղբյուր[^\n]*", "", d.get("caption", "")).strip()
            parts = cap.split("\n")
            tags = [l for l in parts if l.strip().startswith("#")]
            body = "\n".join(l for l in parts if not l.strip().startswith("#")).strip()
            d["caption"] = body + f"\n\nԱղբյուրներ՝ {', '.join(c['sources'][:4])}" + ("\n\n" + "\n".join(tags) if tags else "")
            note(f"[news] chosen story confirmed by {len(c['sources'])}: {', '.join(c['sources'])}")
            return d
        note(f"[news] attempt {attempt + 1} invalid: {errs}")
        prompt += "\n\nYour previous answer had these problems, fix them: " + "; ".join(errs)
    return None
