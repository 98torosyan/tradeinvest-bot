"""Weekly competitor research (Mondays): the best recent Reels of big trading/crypto education pages via Apify's
Instagram Reel Scraper (apify.com/apify/instagram-reel-scraper, free monthly credit), ranked by views, then Gemini
turns them into concrete takeaways in Armenian (hooks, topics, length) for the owner. Needs APIFY_TOKEN; skips without it.
Only public data is read; nothing is copied — the takeaways are patterns to adapt."""
import os

import requests

ACCOUNTS = ["thetradingchannel", "humbledtrader", "rayner.teo", "tradingwithrayner", "coinbureau", "investanswers",
            "thechartguys", "smartmoneyict", "tradingview", "binance", "cryptojack", "wealthymindset_trading"]
ACTOR = "apify~instagram-reel-scraper"

PROMPT = """You analyse top Instagram Reels of trading/crypto education pages for an Armenian trading education page
(@armtradeinvest; faceless, no voice, motion-graphics Reels; goal: followers and students for a paid course).
Reels (views, likes, comments, seconds, first caption line):
{rows}

Return ONLY JSON: {{"hooks": ["5 hook patterns that worked, each as a short Armenian template"],
"topics": ["5 topics that got the most views"], "length": "best length range in seconds, one Armenian sentence",
"do": ["3 concrete changes for our Reels, Armenian, max 15 words each"]}}"""


def configured():
    return bool(os.environ.get("APIFY_TOKEN"))


def scrape(per_account=8):
    r = requests.post(f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items",
                      params={"token": os.environ["APIFY_TOKEN"], "timeout": 240},
                      json={"username": ACCOUNTS, "resultsLimit": per_account}, timeout=300)
    r.raise_for_status()
    out = []
    for x in r.json():
        views = x.get("videoPlayCount") or x.get("videoViewCount") or 0
        cap = (x.get("caption") or "").strip().split("\n")[0][:140]
        out.append({"user": x.get("ownerUsername"), "views": int(views), "likes": x.get("likesCount") or 0,
                    "comments": x.get("commentsCount") or 0, "sec": round(x.get("videoDuration") or 0), "hook": cap,
                    "url": x.get("url")})
    return sorted(out, key=lambda r: r["views"], reverse=True)


def report(rows):
    from . import gemini
    top = rows[:25]
    table = "\n".join(f"{r['views']} | {r['likes']} | {r['comments']} | {r['sec']}s | {r['hook']}" for r in top)
    d = gemini.generate_json(PROMPT.format(rows=table), 0.3)
    lines = ["🔎 Շաբաթական հետազոտություն՝ աշխարհի top trading Reel-երը", ""]
    lines += ["🎣 Hook-եր, որոնք աշխատում են՝"] + [f"• {h}" for h in d.get("hooks", [])][:5] + [""]
    lines += ["🔥 Թեմաներ՝"] + [f"• {t}" for t in d.get("topics", [])][:5] + [""]
    if d.get("length"):
        lines += [f"⏱ {d['length']}", ""]
    lines += ["✅ Ինչ փոխենք մեզ մոտ՝"] + [f"• {x}" for x in d.get("do", [])][:3] + ["", "Top 3՝"]
    lines += [f"{k}. {r['views']:,} դիտում · {r['sec']}վ · {r['url']}" for k, r in enumerate(top[:3], 1)]
    return "\n".join(lines), d
