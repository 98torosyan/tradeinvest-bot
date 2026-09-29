"""Morning market snapshot for the 'Շուկան այսօր' Story.

Every number is cross-checked between independent sources. A value is used
only when at least two sources agree (within a tolerance); a row whose
sources disagree is dropped, and if BTC or ETH cannot be verified the Story
is not published at all."""
import os
import statistics

import requests

UA = {"User-Agent": "Mozilla/5.0 (TradeInvest bot)"}
T = 20
NOTES = []  # diagnostics shown in reels/last_run.md


def note(msg):
    print(msg); NOTES.append(msg)


def _get(url, **kw):
    r = requests.get(url, headers={**UA, **kw.pop("headers", {})}, timeout=T, **kw)
    r.raise_for_status()
    return r.json()


def _safe(fn, *a):
    try:
        return fn(*a)
    except Exception as exc:  # noqa: BLE001
        note(f"[market] {fn.__name__} failed: {str(exc)[:150]}")
        return None


# ---------- sources (each returns {asset: {"price", "chg24", "closes"?}}) ----------
BINANCE = "https://data-api.binance.vision/api/v3"
BIN_SYMBOLS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "GOLD": "PAXGUSDT"}  # PAXG = 1 troy oz of gold


def src_binance():
    out = {}
    for asset, sym in BIN_SYMBOLS.items():
        t = _get(f"{BINANCE}/ticker/24hr", params={"symbol": sym})
        k = _get(f"{BINANCE}/klines", params={"symbol": sym, "interval": "1d", "limit": 8})
        out[asset] = {"price": float(t["lastPrice"]), "chg24": float(t["priceChangePercent"]),
                      "closes": [float(c[4]) for c in k]}
    return out


def src_coingecko():
    ids = {"BTC": "bitcoin", "ETH": "ethereum", "GOLD": "pax-gold"}
    d = _get("https://api.coingecko.com/api/v3/simple/price",
             params={"ids": ",".join(ids.values()), "vs_currencies": "usd", "include_24hr_change": "true"})
    return {a: {"price": float(d[i]["usd"]), "chg24": float(d[i]["usd_24h_change"])} for a, i in ids.items() if i in d}


def src_cmc():
    key = os.environ.get("CMC_API_KEY", "")
    if not key:
        return None
    d = _get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
             params={"symbol": "BTC,ETH,PAXG"}, headers={"X-CMC_PRO_API_KEY": key})["data"]
    m = {"BTC": "BTC", "ETH": "ETH", "GOLD": "PAXG"}
    return {a: {"price": float(d[s]["quote"]["USD"]["price"]), "chg24": float(d[s]["quote"]["USD"]["percent_change_24h"])}
            for a, s in m.items() if s in d}


def _yahoo(symbol):
    d = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", params={"range": "15d", "interval": "1d"})
    res = d["chart"]["result"][0]
    closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
    price = float(res["meta"]["regularMarketPrice"])
    prev = closes[-2] if len(closes) >= 2 else price
    return {"price": price, "chg24": (price / prev - 1) * 100, "closes": closes[-8:]}


def src_yahoo():
    return {"SPX": _yahoo("^GSPC"), "GOLD": _yahoo("GC=F")}


def src_stooq():
    out = {}
    for asset, sym in (("SPX", "^spx"), ("GOLD", "xauusd")):
        r = requests.get("https://stooq.com/q/d/l/", params={"s": sym, "i": "d"}, headers=UA, timeout=T)
        rows = [l.split(",") for l in r.text.strip().splitlines()[1:] if l.count(",") >= 4]
        closes = [float(x[4]) for x in rows[-8:]]
        if len(closes) >= 2:
            out[asset] = {"price": closes[-1], "chg24": (closes[-1] / closes[-2] - 1) * 100, "closes": closes}
    return out


def src_ccxt():
    """Extra independent source through ccxt (Coinbase spot)."""
    import ccxt
    ex = ccxt.coinbase({"enableRateLimit": True, "timeout": 20000})
    out = {}
    for asset, sym in (("BTC", "BTC/USD"), ("ETH", "ETH/USD")):
        t = ex.fetch_ticker(sym)
        if t.get("last") and t.get("percentage") is not None:
            out[asset] = {"price": float(t["last"]), "chg24": float(t["percentage"])}
    return out


def fear_greed():
    d = _get("https://api.alternative.me/fng/", params={"limit": 1})["data"][0]
    return int(d["value"])


# ---------- consensus ----------
TOLERANCE = {"BTC": 1.0, "ETH": 1.0, "GOLD": 2.0, "SPX": 1.0}  # % difference allowed between sources


def consensus(asset, cands):
    cands = [c for c in cands if c and c.get("price", 0) > 0]
    if len(cands) < 2:
        return None
    med = statistics.median(c["price"] for c in cands)
    ok = [c for c in cands if abs(c["price"] / med - 1) * 100 <= TOLERANCE[asset]]
    if len(ok) < 2:
        return None
    closes = next((c["closes"] for c in ok if c.get("closes")), None)
    return {"price": statistics.median(c["price"] for c in ok),
            "chg24": statistics.median(c["chg24"] for c in ok),
            "closes": closes, "sources": len(ok)}


def mood(rows, fng):
    """Transparent rule, not a forecast: +1/-1 points from BTC & ETH 24h moves,
    BTC 7-day trend and the Fear & Greed index."""
    score = 0
    for a in ("BTC", "ETH"):
        c = rows[a]["chg24"]
        score += 1 if c > 1 else -1 if c < -1 else 0
    cl = rows["BTC"].get("closes")
    if cl and len(cl) >= 2:
        w = (cl[-1] / cl[0] - 1) * 100
        score += 1 if w > 2 else -1 if w < -2 else 0
    if fng is not None:
        score += 1 if fng >= 55 else -1 if fng <= 45 else 0
    if score >= 2:
        return "bull"
    if score <= -2:
        return "bear"
    return "neutral"


def build_spec():
    srcs = {n: _safe(f) for n, f in (("binance", src_binance), ("coingecko", src_coingecko), ("cmc", src_cmc),
                                     ("yahoo", src_yahoo), ("stooq", src_stooq), ("ccxt", src_ccxt))}
    rows = {}
    for asset in ("BTC", "ETH", "GOLD", "SPX"):
        r = consensus(asset, [s.get(asset) for s in srcs.values() if s])
        if r:
            rows[asset] = r
        else:
            got = {n: round(v[asset]["price"], 2) for n, v in srcs.items() if v and asset in v}
            note(f"[market] {asset} row dropped, sources: {got}")
    if "BTC" not in rows or "ETH" not in rows:
        raise RuntimeError("BTC/ETH գները չհաջողվեց ստուգել առնվազն երկու աղբյուրով")
    fng = _safe(fear_greed)
    return {"rows": rows, "fng": fng, "mood": mood(rows, fng)}


# ---------- 24h candles for the "Bitcoin 24 ժամում" Story ----------
def candles_binance():
    k = _get(f"{BINANCE}/klines", params={"symbol": "BTCUSDT", "interval": "1h", "limit": 24})
    return [{"t": int(c[0]) // 1000, "o": float(c[1]), "h": float(c[2]), "l": float(c[3]), "c": float(c[4])} for c in k]


def candles_kraken():
    d = _get("https://api.kraken.com/0/public/OHLC", params={"pair": "XBTUSD", "interval": 60})
    if d.get("error"):
        raise RuntimeError(d["error"])
    rows = next(v for k, v in d["result"].items() if k != "last")[-24:]
    return [{"t": int(r[0]), "o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4])} for r in rows]


def price_coingecko_btc():
    return float(_get("https://api.coingecko.com/api/v3/simple/price",
                      params={"ids": "bitcoin", "vs_currencies": "usd"})["bitcoin"]["usd"])


def build_chart_spec():
    """24 hourly BTC candles, used only if the latest price is confirmed by a second source."""
    NOTES.clear()
    sets = {"binance": _safe(candles_binance), "kraken": _safe(candles_kraken)}
    ref = _safe(price_coingecko_btc)
    chosen = None
    for name in ("binance", "kraken"):
        cs = sets[name]
        if not cs or len(cs) < 20:
            continue
        last = cs[-1]["c"]
        others = [v for v in [ref] + [s[-1]["c"] for n, s in sets.items() if n != name and s] if v]
        if any(abs(last / o - 1) * 100 <= 1.0 for o in others):
            chosen = (name, cs); break
        note(f"[chart] {name} last close {last} not confirmed by {others}")
    if not chosen:
        raise RuntimeError("BTC-ի մոմերը չհաջողվեց հաստատել երկրորդ աղբյուրով")
    name, cs = chosen
    hi = max(cs, key=lambda c: c["h"]); lo = min(cs, key=lambda c: c["l"])
    big = max(cs, key=lambda c: abs(c["c"] / c["o"] - 1))
    return {"candles": cs, "source": name, "price": cs[-1]["c"],
            "chg": (cs[-1]["c"] / cs[0]["o"] - 1) * 100,
            "high": hi["h"], "high_t": hi["t"], "low": lo["l"], "low_t": lo["t"],
            "big_t": big["t"], "big_pct": (big["c"] / big["o"] - 1) * 100}
