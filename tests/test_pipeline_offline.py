"""
End-to-end smoke test using synthetic data -- no network calls.
Run with: python tests/test_pipeline_offline.py
This exists because the sandbox this project was first built in has
restricted outbound network access; it lets every non-network part
of the pipeline (templates, plan building, chart/card/video
rendering) be verified before the first real run on GitHub Actions.
"""
import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OUTPUT_DIR
from content.generate_plan import build_plan
from content.render_markdown import render
from visuals.charts import render_candlestick, render_comparison_chart
from visuals.cards import render_all_slides, render_slide_card
from video.reel_video import build_reel


def synthetic_ohlc(days=7, start_price=85000):
    now_ms = int(time.time() * 1000)
    day_ms = 24 * 3600 * 1000
    rng = random.Random(42)
    candles = []
    price = start_price * 0.93
    for i in range(days):
        o = price
        c = o * (1 + rng.uniform(-0.03, 0.04))
        h = max(o, c) * (1 + rng.uniform(0, 0.015))
        l = min(o, c) * (1 - rng.uniform(0, 0.015))
        ts = now_ms - (days - i) * day_ms
        candles.append([ts, o, h, l, c])
        price = c
    return candles


def main():
    market = {
        "bitcoin": {"symbol": "BTC", "price": 85511.61, "change_24h": -1.27, "change_7d": 9.99},
        "ethereum": {"symbol": "ETH", "price": 3210.4, "change_24h": 0.8, "change_7d": 5.1},
    }
    ohlc = synthetic_ohlc()
    news = [
        {"title": "Fed raises rates to 3.75-4.00% in surprise September move",
         "link": "https://example.com/fed", "source": "Test Wire", "is_breaking": True},
        {"title": "Spot Bitcoin ETFs see renewed inflows led by FBTC and IBIT",
         "link": "https://example.com/etf", "source": "Test Wire", "is_breaking": False},
        {"title": "Strategy and Strive add to Bitcoin treasury holdings",
         "link": "https://example.com/treasury", "source": "Test Wire", "is_breaking": False},
    ]
    fear_greed = {"value": 71, "label": "Greed"}
    macro = {"fed_funds_rate": "3.75-4.00", "fed_funds_date": "2026-09-16",
             "cpi_yoy_pct": 3.4, "cpi_month": "2026-08-01", "confirmed": True}

    plan = build_plan(market, ohlc, news, fear_greed, macro, date_str="2026-09-22")
    text = render(plan)
    print(text)
    print("\n[OK] plan built + rendered\n")

    day_dir = os.path.join(OUTPUT_DIR, "test-run")
    os.makedirs(day_dir, exist_ok=True)

    chart_path = render_candlestick(ohlc, "BTC", os.path.join(day_dir, "chart.png"), title="BTC/USD — 7D")
    assert os.path.exists(chart_path)
    print(f"[OK] chart rendered -> {chart_path}")

    slide_paths = render_all_slides(plan["post"]["slides"], os.path.join(day_dir, "slides"), eyebrow="Test")
    for p in slide_paths:
        assert os.path.exists(p)
    print(f"[OK] {len(slide_paths)} carousel slides rendered")

    reel_path = build_reel(plan["reel1"], chart_path, os.path.join(day_dir, "reel1"), "reel1.mp4")
    assert os.path.exists(reel_path)
    print(f"[OK] Reel video rendered -> {reel_path}")

    # --- Friday path: Weekly Recap post + BTC vs traditional markets chart ---
    top_movers = {
        "gainers": [
            {"symbol": "SOL", "name": "Solana", "price": 210.5, "change_7d": 18.4},
            {"symbol": "AVAX", "name": "Avalanche", "price": 42.1, "change_7d": 12.9},
            {"symbol": "LINK", "name": "Chainlink", "price": 19.8, "change_7d": 9.7},
        ],
        "losers": [
            {"symbol": "DOGE", "name": "Dogecoin", "price": 0.18, "change_7d": -14.2},
            {"symbol": "XRP", "name": "XRP", "price": 1.9, "change_7d": -9.5},
            {"symbol": "ADA", "name": "Cardano", "price": 0.55, "change_7d": -6.1},
        ],
    }
    # Same 7-point window as synthetic_ohlc() (days=7 by default), matching
    # main.py's real fetch (both call fetch_sp500/fetch_gold with days=7)
    # so the comparison chart's series line up point-for-point.
    traditional = {
        "sp500": [(f"2026-09-{15 + i}", 5700 + i * 12) for i in range(7)],
        "gold": [(f"2026-09-{15 + i}", 2650 + i * 5) for i in range(7)],
    }
    friday_plan = build_plan(market, ohlc, news, fear_greed, macro, date_str="2026-09-25",
                              top_movers=top_movers, traditional=traditional)
    assert "Weekly Recap" in friday_plan["post"]["topic"]
    assert friday_plan["comparison_chart"] is True
    friday_text = render(friday_plan)
    assert "Weekly Recap" in friday_text
    print("\n[OK] Friday weekly-recap plan built (real top-mover data)")

    comparison_dir = os.path.join(day_dir, "friday")
    comparison_path = render_comparison_chart(
        ohlc, traditional["sp500"], traditional["gold"], os.path.join(comparison_dir, "comparison.png"),
    )
    assert os.path.exists(comparison_path)
    print(f"[OK] BTC vs S&P 500 vs Gold comparison chart rendered -> {comparison_path}")

    # --- Saturday path: meme/humor content ------------------------------------
    saturday_plan = build_plan(market, ohlc, news, fear_greed, macro, date_str="2026-09-26")
    assert saturday_plan.get("meme") is not None
    saturday_text = render(saturday_plan)
    assert "MEME OF THE DAY" in saturday_text
    print("[OK] Saturday meme plan built")

    meme_path = render_slide_card(
        saturday_plan["meme"]["concept"], os.path.join(day_dir, "saturday", "meme.png"),
        eyebrow="MEME OF THE DAY",
    )
    assert os.path.exists(meme_path)
    print(f"[OK] meme concept card rendered -> {meme_path}")

    print("\nALL OFFLINE CHECKS PASSED")


if __name__ == "__main__":
    main()
