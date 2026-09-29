"""Chart data for chart lessons: 'ideal' teaching patterns (deterministic) and 'real' BTC candles
(ccxt, several exchanges) with automatically detected levels (support/resistance) and indicators (ta)."""
import math
import random

PATTERNS = ("support", "resistance", "uptrend", "downtrend", "range", "breakout", "fakeout", "double_top")


def _bars_from_closes(closes, seed=7, t0=1_700_000_000, step=86400):
    rnd = random.Random(seed)
    bars, prev = [], closes[0]
    for i, c in enumerate(closes):
        o = prev
        hi = max(o, c) * (1 + abs(rnd.gauss(0, 0.004)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.004)))
        bars.append({"time": t0 + i * step, "open": round(o, 2), "high": round(hi, 2), "low": round(lo, 2), "close": round(c, 2)})
        prev = c
    return bars


def ideal(pattern, n=60, base=100.0, seed=3):
    """Clean, readable textbook shapes. Returns (bars, levels[{price,label,kind}], touches[time])."""
    rnd = random.Random(seed)
    xs, lv, touches = [], [], []
    noise = lambda: rnd.gauss(0, 0.6)
    if pattern == "support":
        s = base
        for i in range(n):
            wave = abs(math.sin(i / 7.0)) * 9
            xs.append(s + 1.0 + wave + noise())
        lv = [{"price": s, "label": "Support", "kind": "support"}]
    elif pattern == "resistance":
        r = base + 10
        for i in range(n):
            xs.append(r - 1.0 - abs(math.sin(i / 7.0)) * 9 + noise())
        lv = [{"price": r, "label": "Resistance", "kind": "resistance"}]
    elif pattern == "uptrend":
        for i in range(n):
            xs.append(base + i * 0.45 + math.sin(i / 3.2) * 3 + noise())
    elif pattern == "downtrend":
        for i in range(n):
            xs.append(base + 27 - i * 0.45 + math.sin(i / 3.2) * 3 + noise())
    elif pattern == "range":
        for i in range(n):
            xs.append(base + 5 + math.sin(i / 4.0) * 4.5 + noise() * 0.5)
        lv = [{"price": base + 0.3, "label": "Support", "kind": "support"}, {"price": base + 9.7, "label": "Resistance", "kind": "resistance"}]
    elif pattern in ("breakout", "fakeout"):
        r = base + 10
        for i in range(n):
            if i < n * 0.7:
                xs.append(r - 1.5 - abs(math.sin(i / 5.0)) * 7 + noise() * 0.5)
            elif pattern == "breakout":
                xs.append(r + (i - n * 0.7) * 0.9 + noise() * 0.5)
            else:
                k = i - n * 0.7
                xs.append(r + 2.5 - k * 0.7 if k < 6 else r - 4 - (k - 6) * 0.4 + noise() * 0.5)
        lv = [{"price": r, "label": "Resistance", "kind": "resistance"}]
    elif pattern == "double_top":
        top = base + 14
        for i in range(n):
            f = i / n
            v = top - abs(math.sin(f * math.pi * 2)) * 0 - (abs(f - 0.3) * 40 if f < 0.5 else abs(f - 0.7) * 40)
            xs.append(max(base, v) + noise() * 0.5)
        lv = [{"price": top, "label": "Double Top", "kind": "resistance"}]
    else:
        raise ValueError(pattern)
    bars = _bars_from_closes(xs, seed)
    return bars, lv, touches


def real(symbol="BTC/USDT", timeframe="1d", limit=120):
    """Real candles from the first exchange that answers (ccxt), plus a detected support/resistance."""
    import ccxt
    last = None
    for ex_id, sym in (("kraken", "BTC/USD"), ("coinbase", "BTC/USD"), ("bitstamp", "BTC/USD"), ("okx", symbol)):
        try:
            ex = getattr(ccxt, ex_id)({"enableRateLimit": True, "timeout": 20000})
            rows = ex.fetch_ohlcv(sym, timeframe, limit=limit)
            if len(rows) >= 40:
                bars = [{"time": int(r[0] / 1000), "open": r[1], "high": r[2], "low": r[3], "close": r[4]} for r in rows]
                return bars, detect_levels(bars), ex_id
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise RuntimeError(f"no exchange answered: {last}")


def detect_levels(bars, tol=0.012):
    """Support = lowest price zone touched >=2 times by swing lows; resistance likewise with swing highs."""
    lows = [b["low"] for b in bars]; highs = [b["high"] for b in bars]
    swl = [lows[i] for i in range(2, len(lows) - 2) if lows[i] == min(lows[i - 2:i + 3])]
    swh = [highs[i] for i in range(2, len(highs) - 2) if highs[i] == max(highs[i - 2:i + 3])]

    def cluster(vals, kind, label):
        best = None
        for v in vals:
            members = [x for x in vals if abs(x / v - 1) <= tol]
            if len(members) >= 2 and (best is None or len(members) > best[1]):
                best = (sum(members) / len(members), len(members))
        return [{"price": round(best[0], 2), "label": label, "kind": kind, "touches": best[1]}] if best else []
    return cluster(swl, "support", "Support") + cluster(swh, "resistance", "Resistance")


def rsi_last(bars, window=14):
    import pandas as pd
    from ta.momentum import RSIIndicator
    s = pd.Series([b["close"] for b in bars])
    return float(RSIIndicator(s, window=window).rsi().iloc[-1])
