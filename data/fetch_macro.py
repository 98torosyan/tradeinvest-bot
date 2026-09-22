"""
Fetches macro data (Fed funds rate, CPI YoY) from the free FRED API
(St. Louis Fed). Requires a free API key: sign up in 1 minute at
https://fred.stlouisfed.org/docs/api/api_key.html and set it as the
FRED_API_KEY secret. Without a key, macro facts are simply omitted
from the content plan rather than invented.
"""
import requests

from config import FRED_API_KEY

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# FEDFUNDS = effective federal funds rate; CPIAUCSL = CPI, all urban consumers
SERIES = {
    "fed_funds_rate": "FEDFUNDS",
    "cpi_index": "CPIAUCSL",
}


def _fetch_series(series_id, limit=13):
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    resp = requests.get(FRED_BASE, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json().get("observations", [])


def fetch_macro_snapshot():
    """
    Returns a dict with whatever macro facts could be confirmed.
    Any field that could not be fetched/confirmed is left as None
    -- callers must treat None as "do not mention this number".
    """
    snapshot = {
        "fed_funds_rate": None,
        "fed_funds_date": None,
        "cpi_yoy_pct": None,
        "cpi_month": None,
        "confirmed": False,
    }
    if not FRED_API_KEY:
        print("[fetch_macro] FRED_API_KEY not set; skipping macro facts")
        return snapshot

    try:
        obs = _fetch_series(SERIES["fed_funds_rate"], limit=1)
        if obs:
            snapshot["fed_funds_rate"] = obs[0]["value"]
            snapshot["fed_funds_date"] = obs[0]["date"]
    except Exception as exc:
        print(f"[fetch_macro] fed funds fetch failed: {exc}")

    try:
        obs = _fetch_series(SERIES["cpi_index"], limit=13)
        if len(obs) >= 13:
            latest = float(obs[0]["value"])
            year_ago = float(obs[12]["value"])
            snapshot["cpi_yoy_pct"] = round((latest - year_ago) / year_ago * 100, 1)
            snapshot["cpi_month"] = obs[0]["date"]
    except Exception as exc:
        print(f"[fetch_macro] CPI fetch failed: {exc}")

    snapshot["confirmed"] = snapshot["fed_funds_rate"] is not None or snapshot["cpi_yoy_pct"] is not None
    return snapshot
