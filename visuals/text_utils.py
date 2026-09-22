"""
DejaVu Sans (used for every Pillow-rendered card/frame) covers the
Armenian, Latin and common-punctuation blocks but has no color-emoji
glyphs, so an emoji dropped into an image renders as an empty "tofu"
box instead of failing loudly. This strips any character the font
can't draw *before* it reaches an image, so emoji stay only in the
places that display them properly (Telegram messages/captions,
which render emoji natively).
"""
from functools import lru_cache
from fontTools.ttLib import TTFont

_ALWAYS_KEEP = {"\n", "\t"}


@lru_cache(maxsize=4)
def _cmap_for(font_path):
    try:
        return set(TTFont(font_path).getBestCmap().keys())
    except Exception:
        return None  # unknown font -> don't filter anything


def sanitize(text, font_path):
    if not text:
        return text
    cmap = _cmap_for(font_path)
    if cmap is None:
        return text
    kept = [ch for ch in text if ch in _ALWAYS_KEEP or ch == " " or ord(ch) in cmap]
    cleaned = "".join(kept)
    # collapse runs of spaces left behind by stripped emoji
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()
