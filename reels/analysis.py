"""Daily analysis Reel ("Օրվա վերլուծություն") rendered with Remotion from REAL candles.

One asset per day (rotation below). Levels are computed here in code:
  - the last big swing in the window (high -> low or low -> high),
  - the zone the price is testing now (support after a fall, resistance after a rise) and how many times it held,
  - the opposite level (the highest high / lowest low since the swing extreme),
  - Fibonacci 0.5 / 0.618 of that swing.
The Reel shows if/then scenarios, never buy/sell calls, and always carries the disclaimer."""
import datetime as dt
import json
import os
import shutil
import subprocess

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTION = os.path.join(ROOT, "remotion")
ASSETS = os.path.join(ROOT, "reels", "assets")
UA = {"User-Agent": "Mozilla/5.0 (TradeInvest analysis)"}
T = 25
DISCLAIMER = "Կրթական վերլուծություն է, ոչ թե ֆինանսական խորհուրդ"

ASSETS_INFO = {
    "BTC":  {"symbol": "BTCUSD", "tf": "4H", "src": ("binance", "BTCUSDT"), "tags": "#bitcoin #btc #crypto"},
    "ETH":  {"symbol": "ETHUSD", "tf": "4H", "src": ("binance", "ETHUSDT"), "tags": "#ethereum #eth #crypto"},
    "GOLD": {"symbol": "XAUUSD", "tf": "1D", "src": ("yahoo", "GC=F", "xauusd"), "tags": "#gold #xauusd #ոսկի"},
    "SPX":  {"symbol": "S&P 500", "tf": "1D", "src": ("yahoo", "^GSPC", "^spx"), "tags": "#sp500 #stocks #spx"},
    "NDX":  {"symbol": "NASDAQ 100", "tf": "1D", "src": ("yahoo", "^NDX", "^ndx"), "tags": "#nasdaq #stocks #ndx"},
}
# Mon..Sun. Stock indices and gold only on weekdays (their markets are closed at the weekend).
ROTATION = ["GOLD", "BTC", "GOLD", "ETH", "NDX", "BTC", "ETH"]   # gold is the most watched chart topic (Apify study, Nov 2026)
NAME_HY = {"BTC": "Bitcoin", "ETH": "Ethereum", "GOLD": "Ոսկի", "SPX": "S&P 500", "NDX": "Nasdaq 100"}


# ------------------------------------------------------------------ data
def _binance(sym, n=60):
    for base in ("https://data-api.binance.vision/api/v3", "https://api.binance.com/api/v3"):
        try:
            rows = requests.get(f"{base}/klines", params={"symbol": sym, "interval": "4h", "limit": n + 1}, headers=UA, timeout=T).json()
            cs = [{"o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4])} for r in rows]
            return cs[:-1]                                   # drop the candle that is still forming
        except Exception as exc:  # noqa: BLE001
            print("[analysis] binance", base, exc)
    raise RuntimeError("no crypto candles")


def _yahoo(sym, n=60):
    d = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}", params={"range": "6mo", "interval": "1d"},
                     headers=UA, timeout=T).json()["chart"]["result"][0]
    q = d["indicators"]["quote"][0]
    cs = [{"o": o, "h": h, "l": l, "c": c} for o, h, l, c in zip(q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]
    return cs[-n:]


def _stooq(sym, n=60):
    r = requests.get("https://stooq.com/q/d/l/", params={"s": sym, "i": "d"}, headers=UA, timeout=T)
    rows = [l.split(",") for l in r.text.strip().splitlines()[1:] if l.count(",") >= 4]
    return [{"o": float(x[1]), "h": float(x[2]), "l": float(x[3]), "c": float(x[4])} for x in rows[-n:]]


def candles(asset):
    src = ASSETS_INFO[asset]["src"]
    if src[0] == "binance":
        return _binance(src[1])
    try:
        cs = _yahoo(src[1])
        if len(cs) >= 40:
            return cs
    except Exception as exc:  # noqa: BLE001
        print("[analysis] yahoo", exc)
    return _stooq(src[2])


# ------------------------------------------------------------------ levels
def levels(cs):
    n = len(cs)
    hi_i = max(range(n), key=lambda i: cs[i]["h"])
    lo_i = min(range(n), key=lambda i: cs[i]["l"])
    H, L = cs[hi_i]["h"], cs[lo_i]["l"]
    rng = H - L
    tol = rng * 0.06
    if hi_i < lo_i:                                          # last big move was down -> price tests support
        kind, ext_i, zone = "S", lo_i, (L, L + tol)
        cand = [i for i in range(hi_i + 1, n) if cs[i]["l"] <= L + tol]
        cand = [i for i in cand if cs[i]["l"] <= min(cs[j]["l"] for j in range(max(hi_i + 1, i - 2), min(n, i + 3)))]
        after = range(lo_i + 1, n)
        other = max((cs[i]["h"] for i in after), default=H)
        if other <= cs[-1]["c"] * 1.002:
            other = H
        fib = {"0.5": L + rng * 0.5, "0.618": L + rng * 0.618}
    else:                                                    # last big move was up -> price tests resistance
        kind, ext_i, zone = "R", hi_i, (H - tol, H)
        cand = [i for i in range(lo_i + 1, n) if cs[i]["h"] >= H - tol]
        cand = [i for i in cand if cs[i]["h"] >= max(cs[j]["h"] for j in range(max(lo_i + 1, i - 2), min(n, i + 3)))]
        after = range(hi_i + 1, n)
        other = min((cs[i]["l"] for i in after), default=L)
        if other >= cs[-1]["c"] * 0.998:
            other = L
        fib = {"0.5": H - rng * 0.5, "0.618": H - rng * 0.618}
    touches = []
    for i in cand:                                           # merge neighbouring candles into one touch
        if not touches or i - touches[-1] > 2:
            touches.append(i)
    start = max(0, min(hi_i, lo_i) - 6)
    return {"kind": kind, "zone": zone, "touches": touches, "other": other, "fib": fib, "start": start,
            "H": H, "L": L, "last": cs[-1]["c"]}


# ------------------------------------------------------------------ text
def fmt(asset, v, short=False):
    if asset in ("BTC", "ETH") and v >= 10000:
        return f"${v / 1000:.1f}K" if short else f"{v:,.0f}".replace(",", " ")
    if asset in ("SPX", "NDX"):
        return f"{v:,.0f}".replace(",", " ")
    return (f"${v:,.0f}" if short else f"{v:,.0f}").replace(",", " ")


def texts(asset, lv):
    s_or_r = lv["kind"] == "S"
    edge = lv["zone"][0] if s_or_r else lv["zone"][1]
    k = len(lv["touches"])
    word = "Աջակցությունը" if s_or_r else "Դիմադրությունը"
    if k >= 2:
        head, acc = f"{word} պահեց", f"{k} անգամ"
    else:
        head, acc = "Գինը մոտեցավ", "աջակցությանը" if s_or_r else "դիմադրությանը"
    e, o = fmt(asset, edge, True), fmt(asset, lv["other"], True)
    if s_or_r:
        sc = [{"text": f"Եթե պահի {e}-ը", "strong": o, "accent": False},
              {"text": f"Եթե կոտրի {e}-ը", "strong": "անկում", "accent": True}]
    else:
        sc = [{"text": f"Եթե պահի {e}-ը", "strong": o, "accent": False},
              {"text": f"Եթե կոտրի {e}-ը", "strong": "աճ", "accent": True}]
    return head, acc, sc, e, o


def caption(asset, info, lv, head, acc, sc):
    fib = " / ".join(f"{k} → {fmt(asset, v, True)}" for k, v in lv["fib"].items())
    lines = [
        f"📊 {info['symbol']} · {info['tf']} — օրվա վերլուծություն",
        "",
        f"{head} {acc}։",
        "",
        *[f"{'⚪' if n == 0 else '🟠'} {s['text']} → {s['strong']}" for n, s in enumerate(sc)],
        f"📐 Fibonacci՝ {fib}",
        "",
        "Մակարդակները հաշվարկված են իրական գրաֆիկից։",
        f"⚠️ {DISCLAIMER}։",
        "",
        "💬 ⚪ թե՞ 🟠։ Գրիր comment-ում քո սցենարը",
        "📚 Ուզում ես ինքդ կարդալ գրաֆիկը՝ գրիր DM «ԴԱՍ»",
        "",
        f"{info['tags']} #trading #վերլուծություն #հայերեն #technicalanalysis",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ render
def pick_asset(now):
    return ROTATION[now.weekday()]


def build(now, asset=None):
    asset = asset or pick_asset(now)
    info = ASSETS_INFO[asset]
    cs = candles(asset)
    if len(cs) < 30:
        raise RuntimeError(f"{asset}: too few candles ({len(cs)})")
    lv = levels(cs)
    head, acc, sc, e, o = texts(asset, lv)
    props = {
        "symbol": info["symbol"], "tf": info["tf"], "asset": asset, "date": now.strftime("%d.%m"),
        "subtitle": "ՕՐՎԱ ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ", "candles": cs, "start": lv["start"],
        "zone": list(lv["zone"]), "zoneKind": lv["kind"], "touches": lv["touches"], "other": lv["other"],
        "fib": lv["fib"], "last": lv["last"], "head": head, "headAccent": acc, "scenarios": sc,
        "fmt": {"other": fmt(asset, lv["other"]), "zone": fmt(asset, lv["zone"][0] if lv["kind"] == "S" else lv["zone"][1]),
                "last": fmt(asset, lv["last"])},
    }
    return asset, info, lv, props, caption(asset, info, lv, head, acc, sc)


def _npx(*args):
    extra = [f"--browser-executable={os.environ['REMOTION_BROWSER']}"] if os.environ.get("REMOTION_BROWSER") else []
    subprocess.run(["npx", "--yes", "remotion", *args, "--public-dir", ASSETS, *extra], cwd=MOTION, check=True)


def render(props, mp4, cover, music=None):
    if not os.path.isdir(os.path.join(MOTION, "node_modules")):
        subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--silent"], cwd=MOTION, check=True)
    pj = os.path.join(MOTION, "props.json")
    json.dump(props, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
    raw = mp4 + ".raw.mp4"
    _npx("render", "src/index.tsx", "Analysis", raw, f"--props={pj}", "--crf=18")
    _npx("still", "src/index.tsx", "Analysis", cover, f"--props={pj}", "--frame=299", "--image-format=jpeg")
    if music:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-i", music, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-af", "afade=t=in:d=0.3,afade=t=out:st=8.8:d=1.2,loudnorm=I=-15:TP=-1.5:LRA=11", "-shortest", mp4], check=True)
        os.remove(raw)
    else:
        shutil.move(raw, mp4)
    return mp4, cover
