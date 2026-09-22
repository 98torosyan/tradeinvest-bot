"""
Fetches free, no-key daily closing prices for traditional-market
benchmarks (S&P 500, Gold) from Stooq's public CSV endpoint, so the
"BTC vs traditional markets" comparison chart uses real numbers for
all three series, not just BTC.
"""
import io
import requests
import pandas as pd

STOOQ_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"

SYMBOLS = {
    "sp500": "^spx",
    "gold": "xauusd",
}


def fetch_close_series(symbol, days=8):
    """Returns a list of (date_str, close) for the last `days` trading days, oldest first."""
    try:
        resp = requests.get(STOOQ_URL.format(symbol=symbol), timeout=20)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        if df.empty or "Close" not in df.columns:
            return []
        df = df.tail(days)
        return list(zip(df["Date"].astype(str), df["Close"].astype(float)))
    except Exception as exc:
        print(f"[fetch_traditional] {symbol} fetch failed: {exc}")
        return []


def fetch_sp500(days=8):
    return fetch_close_series(SYMBOLS["sp500"], days)


def fetch_gold(days=8):
    return fetch_close_series(SYMBOLS["gold"], days)
