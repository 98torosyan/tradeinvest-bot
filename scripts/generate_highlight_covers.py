"""
Generates 5 branded Instagram Highlight cover images (📊 Daily, 📖
Learn, 😄 Fun, ❓ FAQ, 📩 Contact), matching the same "premium
terminal" visual language as every other asset this bot produces.

This is the ONE piece of the visual system that genuinely cannot be
automated end-to-end: Instagram's public Graph API has no endpoint to
create or manage Profile Highlights (this is a real platform gap, not
something this code chose to skip). Run this once, then upload each
image as a Highlight cover by hand in the Instagram app (Highlight ->
Edit cover -> choose from library) -- a ~30 second, one-time task.

    python scripts/generate_highlight_covers.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import ImageDraw
from visuals import branding
from visuals.branding import font, FONT_BOLD, TEXT

SIZE = 400  # square source; Instagram crops Highlight covers to a circle itself

COVERS = [
    ("daily", "\U0001F4CA", "DAILY"),
    ("learn", "\U0001F4D6", "LEARN"),
    ("fun", "\U0001F602", "FUN"),
    ("faq", "❓", "FAQ"),
    ("contact", "\U0001F4E9", "CONTACT"),
]


def render_cover(label, out_path):
    img = branding.premium_background(SIZE, SIZE, glow_pos=(SIZE // 2, SIZE // 2))
    draw = ImageDraw.Draw(img)
    branding.draw_logomark(draw, SIZE // 2, SIZE // 2 - 40, 70)
    f = font(FONT_BOLD, 34)
    tw = draw.textlength(label, font=f)
    draw.text(((SIZE - tw) / 2, SIZE // 2 + 90), label, font=f, fill=TEXT)
    img.convert("RGB").save(out_path, quality=95)


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "highlight-covers")
    os.makedirs(out_dir, exist_ok=True)
    for slug, _emoji, label in COVERS:
        out_path = os.path.join(out_dir, f"highlight_{slug}.png")
        render_cover(label, out_path)
        print(f"[highlight-covers] {out_path}")
    print("\nUpload each one by hand: your profile -> Highlight -> Edit cover -> choose from library.")


if __name__ == "__main__":
    main()
