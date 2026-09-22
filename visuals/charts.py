"""
Renders a dark, premium-styled candlestick chart from OHLC data
(mplfinance) and stamps the TradeInvest wordmark on it with Pillow.
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
from PIL import Image, ImageDraw, ImageFont

from config import BRAND_NAME, BRAND_BG_COLOR, BRAND_TEXT_COLOR, BRAND_ACCENT_COLOR, BRAND_MUTED_COLOR
from visuals import branding

DARK_STYLE = mpf.make_mpf_style(
    base_mpf_style="nightclouds",
    facecolor=BRAND_BG_COLOR,
    figcolor=BRAND_BG_COLOR,
    gridcolor="#1E2634",
    marketcolors=mpf.make_marketcolors(
        up="#22C55E", down="#EF4444", edge="inherit", wick="inherit", volume="in",
    ),
    rc={"font.size": 11},
)


def ohlc_to_dataframe(ohlc_raw):
    """CoinGecko /ohlc returns [[ts, open, high, low, close], ...]."""
    df = pd.DataFrame(ohlc_raw, columns=["ts", "open", "high", "low", "close"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms")
    df.set_index("date", inplace=True)
    return df[["open", "high", "low", "close"]]


def render_candlestick(ohlc_raw, symbol, out_path, title=None, chip_pct=None, ticker_items=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if not ohlc_raw:
        _render_placeholder(out_path, f"{symbol} chart unavailable")
        return out_path

    df = ohlc_to_dataframe(ohlc_raw)
    fig, _ = mpf.plot(
        df, type="candle", style=DARK_STYLE, returnfig=True,
        figsize=(10.8, 13.5),  # renders ~1080x1350 at dpi=100, good for feed post
        title=title or f"{symbol}/USD",
        tight_layout=True,
    )
    fig.savefig(out_path, dpi=100, facecolor=BRAND_BG_COLOR)
    _stamp_branding(out_path, chip_pct=chip_pct, ticker_items=ticker_items)
    return out_path


def _short_date_label(date_like, from_ms=False):
    try:
        ts = pd.to_datetime(date_like, unit="ms") if from_ms else pd.to_datetime(date_like)
        return ts.strftime("%b %d")
    except Exception:
        return str(date_like)


def render_comparison_chart(btc_ohlc, sp500_series, gold_series, out_path,
                             title="BTC vs S&P 500 vs Gold — 7D (% change)", ticker_items=None):
    """
    Normalizes each series to 0% at its first available point and plots
    them together, so the "who actually outperformed this week" story is
    visual. Any series that failed to fetch is simply omitted -- never
    faked with placeholder numbers.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    series_to_plot = []
    if btc_ohlc:
        btc_closes = [row[4] for row in btc_ohlc]
        series_to_plot.append(("BTC", btc_closes, "#F7931A"))
    if sp500_series:
        series_to_plot.append(("S&P 500", [c for _, c in sp500_series], "#3B82F6"))
    if gold_series:
        series_to_plot.append(("Gold", [c for _, c in gold_series], "#E5C158"))

    # Real calendar-date labels for the x-axis instead of bare point
    # indices (0,1,2...) -- prefer whichever series carries actual trading
    # dates (S&P 500/Gold from Stooq), falling back to BTC's own OHLC
    # timestamps. An unlabeled numeric axis reads as a broken/placeholder
    # chart on content meant to look like a real financial product.
    date_labels = None
    if sp500_series:
        date_labels = [_short_date_label(d) for d, _ in sp500_series]
    elif gold_series:
        date_labels = [_short_date_label(d) for d, _ in gold_series]
    elif btc_ohlc:
        date_labels = [_short_date_label(row[0], from_ms=True) for row in btc_ohlc]

    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100)
    fig.patch.set_facecolor(BRAND_BG_COLOR)
    ax.set_facecolor(BRAND_BG_COLOR)

    if not series_to_plot:
        ax.text(0.5, 0.5, "Comparison data unavailable", color=BRAND_TEXT_COLOR,
                 ha="center", va="center", fontsize=18)
    max_len = 0
    for label, closes, color in series_to_plot:
        base = closes[0]
        pct = [(c - base) / base * 100 for c in closes]
        ax.plot(range(len(pct)), pct, label=label, color=color, linewidth=2.6)
        max_len = max(max_len, len(pct))

    ax.axhline(0, color=BRAND_MUTED_COLOR, linewidth=0.8, linestyle="--")
    ax.set_title(title, color=BRAND_TEXT_COLOR, fontsize=15, fontweight="bold", pad=16)
    ax.set_ylabel("% change", color=BRAND_MUTED_COLOR)
    ax.tick_params(colors=BRAND_MUTED_COLOR)
    if date_labels:
        tick_positions = list(range(min(len(date_labels), max_len)))
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([date_labels[i] for i in tick_positions], rotation=30, ha="right")
    for spine in ax.spines.values():
        spine.set_color("#1E2634")
    ax.grid(color="#1E2634", linewidth=0.6)
    if series_to_plot:
        legend = ax.legend(facecolor=BRAND_BG_COLOR, edgecolor="#1E2634", labelcolor=BRAND_TEXT_COLOR)

    # Leave clean headroom/footroom so the brand bar (top) and ticker
    # strip (bottom), stamped afterwards, never collide with the title,
    # legend, rotated date labels, or axis tick labels.
    fig.subplots_adjust(top=0.87, bottom=0.24 if ticker_items else 0.17)
    fig.savefig(out_path, facecolor=BRAND_BG_COLOR)
    plt.close(fig)
    _stamp_branding(out_path, ticker_items=ticker_items)
    return out_path


def _stamp_branding(path, chip_pct=None, ticker_items=None):
    """Replaces the old plain-text wordmark stamp with the shared brand
    logomark, an optional bullish/bearish chip, and an optional live
    ticker strip -- so charts match the same "premium terminal" look
    as the carousel/story cards instead of being their own style."""
    img = Image.open(path).convert("RGBA")
    w, h = img.size

    # Solid backing bar behind the logomark so it stays legible over
    # whatever chart content happens to sit underneath it.
    top_bar = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(top_bar).rectangle([(0, 0), (w, 74)], fill=(*branding.BG1, 235))
    img.alpha_composite(top_bar)
    branding.brand_header(img, cy=40, r=26)

    if chip_pct is not None:
        branding.bull_bear_chip(img, (w - 240, 12, w - 24, 62), chip_pct)

    bottom_h = 56 + (60 if ticker_items else 0)
    bottom_bar = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(bottom_bar).rectangle([(0, h - bottom_h), (w, h)], fill=(*branding.BG1, 235))
    img.alpha_composite(bottom_bar)
    if ticker_items:
        branding.ticker_strip(img, h - bottom_h, ticker_items, height=60)
    branding.source_watermark(img, y=h - 34)

    img.convert("RGB").save(path)


def _render_placeholder(out_path, message):
    img = Image.new("RGB", (1080, 1350), BRAND_BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = _load_font(36)
    draw.text((60, 620), message, font=font, fill=BRAND_TEXT_COLOR)
    img.save(out_path)


def _load_font(size):
    for candidate in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()
