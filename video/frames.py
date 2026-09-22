"""
Renders the individual 1080x1920 (9:16) frame images used to
assemble a Reel: a hook card, one card per script point, a chart
frame, and an outro/CTA card. Uses the same shared "premium terminal"
branding as the feed cards/charts (visuals/branding.py) so a Reel
looks like it belongs to the same product as the rest of the page,
not a separate style.
"""
import os
import textwrap
from PIL import Image, ImageDraw

from config import BRAND_NAME
from visuals.text_utils import sanitize
from visuals import branding
from visuals.branding import FONT_BOLD, FONT_REG, TEXT, MUTED, ACCENT, font

W, H = 1080, 1920


def _bg(glow_pos=None, glow2_pos=None):
    return branding.premium_background(W, H, glow_pos=glow_pos, glow2_pos=glow2_pos)


def _footer(img, watermark=True):
    draw = ImageDraw.Draw(img)
    draw.line([(70, H - 130), (W - 70, H - 130)], fill=(255, 255, 255, 30))
    if watermark:
        branding.source_watermark(img, y=H - 100)
    return draw


def render_hook_card(hook_text, out_path, chip_pct=None, breaking_headline=None):
    img = _bg()
    top_y = 90
    if breaking_headline:
        branding.breaking_chyron(img, 0, breaking_headline, height=100)
        top_y = 170
    branding.brand_header(img, cy=top_y + 40, r=38)
    if chip_pct is not None:
        branding.bull_bear_chip(img, (W - 300, top_y + 4, W - 70, top_y + 76), chip_pct)

    draw = ImageDraw.Draw(img)
    rule_y = H // 2 - 160
    draw.rectangle([(70, rule_y), (230, rule_y + 8)], fill=ACCENT)
    wrapped = textwrap.fill(sanitize(hook_text, FONT_BOLD), width=18)
    draw.multiline_text((70, H // 2 - 100), wrapped, font=font(FONT_BOLD, 64), fill=TEXT, spacing=18)
    _footer(img)
    img.convert("RGB").save(out_path)
    return out_path


def render_point_card(point_text, out_path, eyebrow=None):
    img = _bg()
    branding.brand_header(img, cy=74, r=30)
    draw = ImageDraw.Draw(img)
    if eyebrow:
        draw.text((70, H // 2 - 220), sanitize(eyebrow.upper(), FONT_BOLD), font=font(FONT_BOLD, 30), fill=ACCENT)
    wrapped = textwrap.fill(sanitize(point_text, FONT_BOLD), width=24)
    draw.multiline_text((70, H // 2 - 140), wrapped, font=font(FONT_BOLD, 48), fill=TEXT, spacing=14)
    _footer(img)
    img.convert("RGB").save(out_path)
    return out_path


def render_outro_card(cta_text, out_path):
    img = _bg()
    draw = ImageDraw.Draw(img)
    branding.draw_logomark(draw, W // 2, H // 2 - 260, 60)
    fbrand = font(FONT_BOLD, 52)
    tw = draw.textlength(BRAND_NAME.upper(), font=fbrand)
    draw.text(((W - tw) / 2, H // 2 - 180), BRAND_NAME.upper(), font=fbrand, fill=ACCENT)
    wrapped = textwrap.fill(sanitize(cta_text, FONT_BOLD), width=24)
    draw.multiline_text((70, H // 2 - 80), wrapped, font=font(FONT_BOLD, 46), fill=TEXT, spacing=14)
    _footer(img)
    img.convert("RGB").save(out_path)
    return out_path


def render_chart_frame(chart_image_path, out_path, caption=None):
    """Places the (roughly square/4:5) candlestick chart onto a 9:16 canvas
    with padding, so it fits the Reel format instead of looking stretched.
    The chart image itself already carries the branded header/ticker
    (visuals/charts.py), so this frame only needs its own caption."""
    canvas = _bg()
    if os.path.exists(chart_image_path):
        chart = Image.open(chart_image_path).convert("RGB")
        target_w = W - 120
        ratio = target_w / chart.width
        chart = chart.resize((target_w, int(chart.height * ratio)))
        shadow = Image.new("RGB", chart.size, (0, 0, 0))
        canvas.paste(shadow, (60 + 8, 260 + 8))
        canvas.paste(chart, (60, 260))
    draw = ImageDraw.Draw(canvas)
    if caption:
        wrapped = textwrap.fill(sanitize(caption, FONT_BOLD), width=26)
        draw.multiline_text((70, 120), wrapped, font=font(FONT_BOLD, 40), fill=TEXT, spacing=10)
    # The embedded chart image already carries its own brand header/
    # watermark (visuals/charts.py), so skip a second one here.
    _footer(canvas, watermark=False)
    canvas.convert("RGB").save(out_path)
    return out_path
