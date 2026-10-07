"""Data for the animated trading backgrounds: real candles and tickers when exchanges answer (ccxt),
otherwise a realistic seeded random walk. Never raises."""
import math
import random

COINS = ["BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX", "LINK", "TON", "DOT", "LTC"]


def _synthetic(seed, n=260, start=64000.0):
    rnd = random.Random(seed)
    out, p = [], start
    for i in range(n):
        drift = math.sin(i / 23.0 + seed) * 0.0025
        c = p * (1 + drift + rnd.gauss(0, 0.006))
        h = max(p, c) * (1 + abs(rnd.gauss(0, 0.003)))
        l = min(p, c) * (1 - abs(rnd.gauss(0, 0.003)))
        out.append({"o": round(p, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)})
        p = c
    coins = [{"s": s, "p": "", "ch": round(rnd.gauss(0.3, 3.2), 2)} for s in COINS]   # no invented prices
    return {"symbol": "BTC", "candles": out, "coins": coins, "real": False}


def get(seed):
    try:
        import ccxt
        for ex_id in ("kraken", "coinbase", "bitstamp"):
            try:
                ex = getattr(ccxt, ex_id)({"enableRateLimit": True, "timeout": 15000})
                sym = ["BTC/USD", "ETH/USD", "SOL/USD"][seed % 3]
                rows = ex.fetch_ohlcv(sym, "1h", limit=260)
                if len(rows) < 120:
                    continue
                candles = [{"o": r[1], "h": r[2], "l": r[3], "c": r[4]} for r in rows]
                coins = []
                try:
                    tick = ex.fetch_tickers([f"{c}/USD" for c in COINS[:9]])
                    for k, v in tick.items():
                        if v.get("last"):
                            coins.append({"s": k.split("/")[0], "p": f"{v['last']:,.2f}", "ch": round(float(v.get("percentage") or 0), 2)})
                except Exception:  # noqa: BLE001
                    pass
                base = _synthetic(seed)
                return {"symbol": sym.split("/")[0], "candles": candles, "coins": coins or base["coins"], "real": True}
            except Exception:  # noqa: BLE001
                continue
    except ImportError:
        pass
    return _synthetic(seed)
