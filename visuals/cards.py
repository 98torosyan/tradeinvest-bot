"""
Renders branded, typographic carousel-slide cards using the shared
"premium terminal" visual language in visuals/branding.py: ambient
glow + grid background, a custom logomark instead of plain brand
text, a swipe-progress indicator, and per-slide "kind" treatments
(hero / quote / bottom_line / normal) so a carousel reads like a
designed sequence, not repeated identical templates.
"""
import os
import textwrap
from PIL import ImageDraw

from visuals.text_utils import sanitize
from visuals import branding
from visuals.branding import (
    FONT_BOLD, FONT_REG, TEXT, MUTED, ACCENT, font,
)

W, H = 1080, 1350


def _slide_text_kind(slide):
    """Slides can be a plain string (kind='normal') or a
    {"text": ..., "kind": ...} dict -- kept backward compatible so
    older callers/tests that just pass strings keep working."""
    if isinstance(slide, dict):
        return slide.get("text", ""), slide.get("kind", "normal")
    return slide, "normal"


def render_slide_card(slide, out_path, index=1, total=1, eyebrow=None, chip_pct=None, breaking_headline=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    text, kind = _slide_text_kind(slide)

    glow = branding.ACCENT if kind != "quote" else branding.ACCENT
    img = branding.premium_background(W, H, glow_color=glow)

    top_y = 100
    if breaking_headline:
        branding.breaking_chyron(img, 0, breaking_headline, height=80)
        top_y = 150

    branding.brand_header(img, cy=top_y + 34, r=30)

    if total > 1:
        branding.swipe_progress(img, index, total)

    draw = ImageDraw.Draw(img)

    if eyebrow:
        draw.text((80, top_y + 78), sanitize(eyebrow.upper(), FONT_BOLD), font=font(FONT_BOLD, 24), fill=ACCENT)

    if chip_pct is not None:
        branding.bull_bear_chip(img, (W - 260, top_y - 6, W - 70, top_y + 50), chip_pct)

    body_top = top_y + 140

    if kind == "hero":
        panel_box = (70, body_top, W - 70, body_top + 330)
        branding.glass_panel(img, panel_box, radius=40)
        draw = ImageDraw.Draw(img)
        body_font = font(FONT_BOLD, 58)
        wrapped = textwrap.fill(sanitize(text, FONT_BOLD), width=17)
        draw.multiline_text((110, body_top + 46), wrapped, font=body_font, fill=TEXT, spacing=16)
    elif kind == "quote":
        quote_font = font(FONT_BOLD, 130)
        draw.text((72, body_top - 40), "“", font=quote_font, fill=ACCENT)
        body_font = font(FONT_BOLD, 44)
        wrapped = textwrap.fill(sanitize(text, FONT_BOLD), width=26)
        draw.multiline_text((88, body_top + 90), wrapped, font=body_font, fill=TEXT, spacing=14)
    elif kind == "bottom_line":
        body_font = font(FONT_REG, 38)
        wrapped = textwrap.fill(sanitize(text, FONT_REG), width=30)
        draw.multiline_text((80, body_top + 60), wrapped, font=body_font, fill=MUTED, spacing=14)
    else:
        body_font = font(FONT_BOLD, 50)
        wrapped = textwrap.fill(sanitize(text, FONT_BOLD), width=22)
        draw.multiline_text((80, body_top + 20), wrapped, font=body_font, fill=TEXT, spacing=16)

    draw = ImageDraw.Draw(img)
    draw.line([(80, H - 130), (W - 80, H - 130)], fill=(255, 255, 255, 30))
    draw.text((80, H - 92), f"{index}/{total}", font=font(FONT_REG, 26), fill=MUTED)
    branding.source_watermark(img, y=H - 92)

    img.convert("RGB").save(out_path, quality=95)
    return out_path


def render_all_slides(slides, out_dir, eyebrow=None, chip_pct=None, breaking_headline=None):
    """`slides` may be plain strings or {"text","kind"} dicts (see
    _slide_text_kind). `chip_pct`/`breaking_headline` are applied only
    to the first slide (the "cover"), matching how a real feed post's
    opening slide is the one that has to stop the scroll."""
    paths = []
    total = len(slides)
    for i, slide in enumerate(slides, start=1):
        out_path = os.path.join(out_dir, f"slide_{i}.png")
        render_slide_card(
            slide, out_path, index=i, total=total, eyebrow=eyebrow,
            chip_pct=chip_pct if i == 1 else None,
            breaking_headline=breaking_headline if i == 1 else None,
        )
        paths.append(out_path)
    return paths
