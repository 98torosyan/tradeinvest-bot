"""
Shared "premium terminal" visual language used by every rendered asset
(carousel slides, story cards, charts, Reel frames): ambient glow +
fine grid texture background, a custom geometric logomark (instead of
plain brand text), a glass-morphism panel for hero numbers, a
bullish/bearish chip, a live-style ticker strip, a swipe-progress
indicator for carousels, and a breaking-news chyron banner.

Kept in one module so every visual touchpoint (feed posts, Stories,
Reels, charts) looks like one consistent product instead of several
different scripts with their own styling.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import (
    BRAND_NAME, BRAND_BG_COLOR, BRAND_BG_COLOR_2, BRAND_TEXT_COLOR,
    BRAND_MUTED_COLOR, BRAND_ACCENT_COLOR, BRAND_GREEN, BRAND_RED,
    BRAND_ALERT_COLOR, DATA_SOURCE_LABEL,
)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _hex(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


BG1 = _hex(BRAND_BG_COLOR)
BG2 = _hex(BRAND_BG_COLOR_2)
ACCENT = _hex(BRAND_ACCENT_COLOR)
GREEN = _hex(BRAND_GREEN)
RED = _hex(BRAND_RED)
ALERT = _hex(BRAND_ALERT_COLOR)
TEXT = _hex(BRAND_TEXT_COLOR)
MUTED = _hex(BRAND_MUTED_COLOR)


def font(path, size):
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def gradient(w, h, c1=BG1, c2=BG2):
    img = Image.new("RGB", (w, h), c1)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        draw.line([(0, y), (w, y)], fill=tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3)))
    return img


def radial_glow(w, h, center, radius, color, max_alpha=130):
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = center
    steps = 60
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(max_alpha * (1 - i / steps) ** 2)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, a))
    return glow.filter(ImageFilter.GaussianBlur(40))


def fine_grid(w, h, spacing=54, color=(255, 255, 255, 9)):
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, w, spacing):
        gd.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(0, h, spacing):
        gd.line([(0, y), (w, y)], fill=color, width=1)
    return grid


def noise_grain(w, h, amount=6, alpha=12, seed=7):
    rng = random.Random(seed)
    g = Image.new("L", (w, h))
    px = g.load()
    for x in range(0, w, 2):
        for y in range(0, h, 2):
            px[x, y] = 128 + rng.randint(-amount, amount)
    g = g.resize((w, h)).convert("RGBA")
    g.putalpha(alpha)
    return g


def premium_background(w, h, glow_color=ACCENT, glow_pos=None, glow2_pos=None):
    """The standard branded backdrop for every asset: gradient + fine grid
    + two soft ambient glows + subtle film grain. Deterministic (same
    seed every render) so consecutive assets in one run look consistent."""
    glow_pos = glow_pos or (int(w * 0.8), int(h * 0.19))
    glow2_pos = glow2_pos or (int(w * 0.12), int(h * 0.74))
    base = gradient(w, h).convert("RGBA")
    base.alpha_composite(fine_grid(w, h))
    base.alpha_composite(radial_glow(w, h, glow_pos, w * 0.46, glow_color, 130))
    base.alpha_composite(radial_glow(w, h, glow2_pos, w * 0.38, ACCENT, 65))
    base.alpha_composite(noise_grain(w, h))
    return base


def draw_logomark(draw, cx, cy, r, color=ACCENT):
    """Circle + 3 ascending candlestick bars -- the brand mark used
    everywhere instead of plain brand-name text, so the page has one
    consistent, recognizable visual signature."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(2, int(r * 0.09)))
    bw = r * 0.22
    heights = [r * 0.5, r * 0.9, r * 0.65]
    xs = [cx - r * 0.5, cx - r * 0.06, cx + r * 0.38]
    for x, h in zip(xs, heights):
        draw.rounded_rectangle([x, cy + r * 0.5 - h, x + bw, cy + r * 0.5], radius=bw * 0.3, fill=color)


def brand_header(base, cx=None, cy=None, r=34, wordmark=True, wordmark_pos=None):
    """Stamps the logomark (+ optional two-line wordmark) top-left,
    consistently across cards/charts/frames."""
    draw = ImageDraw.Draw(base)
    w = base.size[0]
    cx = cx if cx is not None else int(w * 0.107)
    cy = cy if cy is not None else int(base.size[1] * 0.062) + r
    draw_logomark(draw, cx, cy, r)
    if wordmark:
        wx, wy = wordmark_pos or (cx + r + 16, cy - r * 0.62)
        parts = BRAND_NAME.upper()
        f = font(FONT_BOLD, int(r * 0.62))
        draw.text((wx, wy), parts, font=f, fill=TEXT)
    return draw


def outline_chip(base, box, text, color, fill_alpha=28, border_alpha=190):
    """A small rounded pill with a translucent fill (properly alpha-
    composited onto an RGBA image -- ImageDraw does not blend when
    drawing straight onto an RGBA canvas, so this goes through a
    separate overlay layer first)."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=(*color, fill_alpha), outline=(*color, border_alpha), width=2)
    base.alpha_composite(overlay)
    d = ImageDraw.Draw(base)
    f = font(FONT_BOLD, int((box[3] - box[1]) * 0.42))
    tw = d.textlength(text, font=f)
    x0, y0, x1, y1 = box
    d.text(((x0 + x1 - tw) / 2, y0 + (y1 - y0 - f.size) / 2 - 2), text, font=f, fill=color)


def bull_bear_chip(base, box, change_pct):
    """Bullish/bearish pill sized to `change_pct` (24h or 7d change)."""
    if change_pct is None:
        return
    up = change_pct >= 0
    color = GREEN if up else RED
    arrow = "▲" if up else "▼"
    label = f"{arrow} {'BULLISH' if up else 'BEARISH'}"
    outline_chip(base, box, label, color)


def glass_panel(base, box, radius=40, fill_alpha=26, border_alpha=60):
    """Frosted-glass panel: a blurred copy of what's already behind the
    box, tinted, masked to rounded corners -- the premium "hero card"
    look behind a big price/number."""
    x0, y0, x1, y1 = box
    crop = base.crop(box).filter(ImageFilter.GaussianBlur(18)).convert("RGBA")
    overlay = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], radius=radius, fill=255)
    overlay = Image.composite(crop, overlay, mask)
    tint = Image.new("RGBA", (x1 - x0, y1 - y0), (255, 255, 255, fill_alpha))
    overlay = Image.composite(Image.alpha_composite(overlay, tint), overlay, mask)
    base.alpha_composite(overlay, (x0, y0))
    ImageDraw.Draw(base).rounded_rectangle(box, radius=radius, outline=(255, 255, 255, border_alpha), width=2)


def ticker_strip(base, y, items, height=60):
    """A thin "live terminal" strip of symbol/% chips, e.g. at the
    bottom of a chart or the first carousel slide. `items` is a list
    of (symbol, formatted_pct_str, is_up)."""
    w = base.size[0]
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle([0, y, w, y + height], fill=(255, 255, 255, 14))
    base.alpha_composite(overlay)
    d = ImageDraw.Draw(base)
    f = font(FONT_BOLD, int(height * 0.36))
    x = 40
    for sym, val, up in items:
        color = GREEN if up else RED
        arrow = "▲" if up else "▼"
        txt = f"{sym}  {val}"
        d.text((x, y + height * 0.32), txt, font=f, fill=TEXT)
        tw = d.textlength(txt, font=f)
        d.text((x + tw + 10, y + height * 0.32), arrow, font=f, fill=color)
        x += tw + 90
        if x > w - 80:
            break


def swipe_progress(base, index, total, y=None, margin=80):
    """Thin dash-per-slide progress indicator at the top of a carousel
    card, filled up to the current slide -- the "how much is left"
    cue used by professional carousel formats."""
    if total <= 1:
        return
    w, h = base.size
    y = y if y is not None else int(h * 0.045)
    gap = 10
    dash_w = (w - 2 * margin - gap * (total - 1)) / total
    d = ImageDraw.Draw(base)
    for i in range(total):
        x0 = margin + i * (dash_w + gap)
        color = (*ACCENT, 230) if i < index else (255, 255, 255, 40)
        d.rounded_rectangle([x0, y, x0 + dash_w, y + 6], radius=3, fill=color)


def breaking_chyron(base, y, headline, height=86):
    """Red 'BREAKING' alert banner, Bloomberg/CNBC-style, for the days
    the plan is actually flagged breaking (never applied speculatively)."""
    w = base.size[0]
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle([0, y, w, y + height], fill=(*ALERT, 235))
    base.alpha_composite(overlay)
    d = ImageDraw.Draw(base)
    tag_f = font(FONT_BOLD, int(height * 0.32))
    d.text((40, y + height * 0.16), "● BREAKING", font=tag_f, fill=(255, 255, 255))
    body_f = font(FONT_BOLD, int(height * 0.26))
    max_chars = 46
    text = headline if len(headline) <= max_chars else headline[:max_chars - 1] + "…"
    d.text((320, y + height * 0.20), text, font=body_f, fill=(255, 255, 255))


def source_watermark(base, y=None):
    """Small, honest print naming the real data sources -- a cheap,
    high-trust signal that separates this page from meme accounts."""
    w, h = base.size
    y = y if y is not None else h - 26
    d = ImageDraw.Draw(base)
    f = font(FONT_REG, 18)
    d.text((w - d.textlength(DATA_SOURCE_LABEL, font=f) - 30, y), DATA_SOURCE_LABEL, font=f, fill=MUTED)
