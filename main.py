"""
Entry point: fetches real data, builds the day's content plan,
renders every visual/video asset, and delivers everything to
Telegram. Run daily by the GitHub Actions workflow in
.github/workflows/daily-content.yml, or manually with:

    python main.py
"""
import json
import os
import traceback
from datetime import datetime

from config import OUTPUT_DIR, PRIMARY_COIN, BRAND_NAME, COINGECKO_IDS
from data.fetch_market import fetch_prices, fetch_ohlc, fetch_fear_greed, fetch_top_movers
from data.fetch_news import fetch_headlines
from data.fetch_macro import fetch_macro_snapshot
from data.fetch_traditional import fetch_sp500, fetch_gold
from content.generate_plan import build_plan
from content.render_markdown import render
from visuals.charts import render_candlestick, render_comparison_chart
from visuals.cards import render_all_slides, render_slide_card
from video.reel_video import build_reel
from video.frames import render_point_card
from delivery import telegram_sender


def _ticker_items(market):
    """Builds the small live-ticker strip shown on charts/hero visuals
    from real fetched prices -- symbols with no confirmed 24h change
    are simply left out, never filled with a placeholder."""
    items = []
    for coin_id, sym in COINGECKO_IDS.items():
        chg = market.get(coin_id, {}).get("change_24h")
        if chg is not None:
            items.append((sym, f"{chg:+.1f}%", chg >= 0))
    return items


def run():
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    day_dir = os.path.join(OUTPUT_DIR, date_str)
    os.makedirs(day_dir, exist_ok=True)
    print(f"[main] === {BRAND_NAME} daily content run: {date_str} ===")

    print("[main] fetching market data...")
    market = fetch_prices()
    ohlc = fetch_ohlc(PRIMARY_COIN, days=7)
    fear_greed = fetch_fear_greed()

    print("[main] fetching news...")
    news = fetch_headlines()

    print("[main] fetching macro data...")
    macro = fetch_macro_snapshot()

    weekday = datetime.strptime(date_str, "%Y-%m-%d").weekday()
    top_movers = fetch_top_movers() if weekday == 4 else {"gainers": [], "losers": []}  # Friday only
    traditional = {}
    if weekday == 4:
        print("[main] fetching S&P 500 / Gold for the weekly comparison chart...")
        # Same 7-point window as the BTC OHLC fetch above (days=7), so all
        # three series line up point-for-point on the comparison chart
        # instead of silently plotting mismatched lengths against a bare
        # index axis.
        traditional = {"sp500": fetch_sp500(days=7), "gold": fetch_gold(days=7)}

    print("[main] building content plan...")
    plan = build_plan(market, ohlc, news, fear_greed, macro, date_str,
                       top_movers=top_movers, traditional=traditional)

    plan_text = render(plan)
    plan_path = os.path.join(day_dir, "plan.md")
    with open(plan_path, "w", encoding="utf-8") as fh:
        fh.write(plan_text)
    print(f"[main] plan written to {plan_path}")

    chip_pct = plan["market_snapshot"]["change_24h"]
    breaking_headline = plan.get("breaking_headline")
    ticker_items = _ticker_items(market)

    print("[main] rendering chart...")
    chart_path = os.path.join(day_dir, "chart.png")
    render_candlestick(ohlc, plan["market_snapshot"]["symbol"], chart_path,
                        title=f"{plan['market_snapshot']['symbol']}/USD — 7D",
                        chip_pct=chip_pct, ticker_items=ticker_items)

    print("[main] rendering carousel slides...")
    slide_paths = render_all_slides(plan["post"]["slides"], os.path.join(day_dir, "slides"),
                                     eyebrow=plan["post"]["topic"],
                                     chip_pct=chip_pct, breaking_headline=breaking_headline)

    comparison_path = None
    if plan.get("comparison_chart"):
        print("[main] rendering BTC vs traditional markets comparison chart...")
        comparison_path = os.path.join(day_dir, "comparison.png")
        render_comparison_chart(ohlc, traditional.get("sp500", []), traditional.get("gold", []), comparison_path,
                                 ticker_items=ticker_items)
        slide_paths_extra = [comparison_path]
    else:
        slide_paths_extra = []

    meme_path = None
    if plan.get("meme"):
        print("[main] rendering meme concept card...")
        meme_path = render_slide_card(
            plan["meme"]["concept"], os.path.join(day_dir, "meme.png"),
            eyebrow="MEME OF THE DAY",
        )

    print("[main] rendering story cards...")
    stories_dir = os.path.join(day_dir, "stories")
    os.makedirs(stories_dir, exist_ok=True)
    story_paths = []
    for i, st in enumerate(plan["stories"], start=1):
        p = render_point_card(st["content"], os.path.join(stories_dir, f"story_{i}.png"), eyebrow=st["type"])
        story_paths.append(p)

    reel1_path = None
    reel2_path = None
    try:
        print("[main] building Reel #1 video (this can take a minute)...")
        reel1_path = build_reel(plan["reel1"], chart_path, os.path.join(day_dir, "reel1"), "reel1.mp4",
                                 chip_pct=chip_pct, breaking_headline=breaking_headline)
    except Exception:
        print("[main] Reel #1 video failed, continuing without it:")
        traceback.print_exc()

    try:
        print("[main] building Reel #2 video...")
        # Reel #2 has no chart hook by design (macro/news recap) -- reuse the same chart as a light backdrop
        reel2_path = build_reel(
            {**plan["reel2"], "script": [f"{i+1}. {p}" for i, p in enumerate(plan["reel2"]["points"])]},
            chart_path, os.path.join(day_dir, "reel2"), "reel2.mp4",
        )
    except Exception:
        print("[main] Reel #2 video failed, continuing without it:")
        traceback.print_exc()

    print("[main] sending to Telegram...")
    telegram_sender.send_text(f"📅 {BRAND_NAME} — {date_str}\n\n" + plan_text)
    telegram_sender.send_photo(chart_path, caption="Chart of the day")
    for i, sp in enumerate(slide_paths, start=1):
        telegram_sender.send_photo(sp, caption=f"Post slide {i}/{len(slide_paths)}")
    if comparison_path:
        telegram_sender.send_photo(comparison_path, caption="BTC vs S&P 500 vs Gold — weekly comparison")
    if reel1_path:
        telegram_sender.send_video(reel1_path, caption="Reel #1")
    if reel2_path:
        telegram_sender.send_video(reel2_path, caption="Reel #2")
    for i, sp in enumerate(story_paths, start=1):
        telegram_sender.send_photo(sp, caption=f"Story {i}/10 (poll/quiz stickers must be added by hand)")
    if meme_path:
        telegram_sender.send_photo(meme_path, caption="Meme of the day 😄")

    # Manifest for scripts/publish_to_instagram.py: relative paths + captions,
    # so the Instagram-publish step (which runs after this run's media is
    # pushed to GitHub Pages) knows what to publish and with which caption.
    carousel_images = [os.path.relpath(p, day_dir) for p in slide_paths]
    carousel_images += [os.path.relpath(p, day_dir) for p in slide_paths_extra]
    manifest = {
        "date": date_str,
        "chart": os.path.relpath(chart_path, day_dir) if os.path.exists(chart_path) else None,
        "carousel": {
            "images": carousel_images,
            "caption": plan["post"]["caption"] + "\n\n" + plan["disclaimer"],
        },
        "reel1": {
            "video": os.path.relpath(reel1_path, day_dir) if reel1_path else None,
            "caption": plan["reel1"]["caption"] + " " + plan["reel1"]["hashtags"],
        },
        "reel2": {
            "video": os.path.relpath(reel2_path, day_dir) if reel2_path else None,
            "caption": plan["reel2"]["caption"] + " " + plan["reel2"]["hashtags"],
        },
        "stories": [os.path.relpath(p, day_dir) for p in story_paths],
        # Real headline links used for the auto-posted "sources" comment
        # (delivery/instagram_publisher.py) -- credibility signal, not a
        # design flourish: whoever reads the comment can verify the numbers.
        "sources": plan.get("sources", []),
    }
    if meme_path:
        manifest["meme"] = {
            "image": os.path.relpath(meme_path, day_dir),
            "caption": plan["meme"]["caption"] + " " + plan["meme"]["hashtags"],
        }
    manifest_path = os.path.join(day_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(f"[main] manifest written to {manifest_path}")

    print("[main] done.")


if __name__ == "__main__":
    run()
