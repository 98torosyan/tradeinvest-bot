"""
Fetches real crypto market data from CoinGecko's free public API
(no API key required). If the API is unreachable, falls back to
cached data written by the previous successful run so the pipeline
never crashes outright.
"""
import json
import os
import requests

from config import COINGECKO_IDS, OUTPUT_DIR

CACHE_PATH = os.path.join(OUTPUT_DIR, "_market_cache.json")


def fetch_prices():
    """Returns {coin_id: {price, change_24h, change_7d}} for tracked coins."""
    ids = ",".join(COINGECKO_IDS.keys())
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=usd"
        "&include_24hr_change=true&include_last_updated_at=true"
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        raw = resp.json()
        result = {}
        for coin_id, sym in COINGECKO_IDS.items():
            entry = raw.get(coin_id, {})
            result[coin_id] = {
                "symbol": sym,
                "price": entry.get("usd"),
                "change_24h": entry.get("usd_24h_change"),
            }
        # 7-day change needs a separate call (market_chart)
        for coin_id in COINGECKO_IDS:
            result[coin_id]["change_7d"] = _fetch_7d_change(coin_id)
        _save_cache(result)
        return result
    except Exception as exc:  # network blocked, rate-limited, etc.
        print(f"[fetch_market] live fetch failed ({exc}); using cache")
        return _load_cache()


def _fetch_7d_change(coin_id):
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        "?vs_currency=usd&days=7&interval=daily"
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        prices = resp.json().get("prices", [])
        if len(prices) < 2:
            return None
        start, end = prices[0][1], prices[-1][1]
        return round((end - start) / start * 100, 2)
    except Exception:
        return None


def fetch_ohlc(coin_id="bitcoin", days=7):
    """Returns a list of [timestamp, open, high, low, close] for charting."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"[fetch_market] OHLC fetch failed ({exc})")
        return []


def fetch_top_movers(per_page=50, top_n=3):
    """
    Returns {"gainers": [...], "losers": [...]} -- each a list of
    {symbol, name, price, change_7d} for the biggest 7-day movers among
    the top `per_page` coins by market cap. Used for the Friday
    "Weekly Recap" post. Empty lists (not invented data) on failure.
    """
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency=usd&order=market_cap_desc&per_page={per_page}&page=1"
        "&price_change_percentage=7d"
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        coins = resp.json()
        rows = [
            {
                "symbol": c["symbol"].upper(),
                "name": c["name"],
                "price": c["current_price"],
                "change_7d": c.get("price_change_percentage_7d_in_currency"),
            }
            for c in coins
            if c.get("price_change_percentage_7d_in_currency") is not None
        ]
        rows.sort(key=lambda r: r["change_7d"], reverse=True)
        return {"gainers": rows[:top_n], "losers": rows[-top_n:][::-1]}
    except Exception as exc:
        print(f"[fetch_market] top movers fetch failed ({exc})")
        return {"gainers": [], "losers": []}


def fetch_fear_greed():
    """Returns {"value": int, "label": str} from alternative.me (free, no key)."""
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=15)
        resp.raise_for_status()
        item = resp.json()["data"][0]
        return {"value": int(item["value"]), "label": item["value_classification"]}
    except Exception as exc:
        print(f"[fetch_market] fear/greed fetch failed ({exc})")
        return {"value": None, "label": "Unknown"}


def _save_cache(data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def _load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {coin_id: {"symbol": sym, "price": None, "change_24h": None, "change_7d": None}
            for coin_id, sym in COINGECKO_IDS.items()}
