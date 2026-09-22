"""
Publishes one day's already-generated content to Instagram.

Run AFTER main.py has produced output/<date>/manifest.json AND after
that day's media has been pushed to GitHub Pages (the workflow does
both, in that order) -- this script only builds public URLs from the
manifest, waits for each to be live, and calls the Graph API.

    python scripts/publish_to_instagram.py [YYYY-MM-DD]   # default: today (UTC)

Each item is published independently and failures are logged, not
fatal -- e.g. if Reel #2 fails to process, the carousel post and
Reel #1 still go out.
"""
import json
import os
import sys
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OUTPUT_DIR
from delivery import instagram_publisher as ig
from delivery.media_hosting import public_url_for, wait_until_reachable
from delivery import telegram_sender


def _url(date_str, relpath):
    url = public_url_for(date_str, relpath)
    ok = wait_until_reachable(url)
    if not ok:
        raise RuntimeError(f"media not reachable in time: {url}")
    return url


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.utcnow().strftime("%Y-%m-%d")
    day_dir = os.path.join(OUTPUT_DIR, date_str)
    manifest_path = os.path.join(day_dir, "manifest.json")
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    results = []
    sources = manifest.get("sources", [])

    # 1) Carousel (feed Post)
    try:
        urls = [_url(date_str, p) for p in manifest["carousel"]["images"]]
        media_id = ig.publish_carousel(urls, caption=manifest["carousel"]["caption"])
        results.append(("Carousel post", "OK", media_id))
        if media_id:
            ig.post_sources_comment(media_id, sources)
    except Exception as exc:
        traceback.print_exc()
        results.append(("Carousel post", "FAILED", str(exc)))

    # 2) Reel #1
    if manifest.get("reel1", {}).get("video"):
        try:
            url = _url(date_str, manifest["reel1"]["video"])
            media_id = ig.publish_reel(url, caption=manifest["reel1"]["caption"])
            results.append(("Reel #1", "OK", media_id))
            if media_id:
                ig.post_sources_comment(media_id, sources)
        except Exception as exc:
            traceback.print_exc()
            results.append(("Reel #1", "FAILED", str(exc)))

    # 3) Reel #2
    if manifest.get("reel2", {}).get("video"):
        try:
            url = _url(date_str, manifest["reel2"]["video"])
            media_id = ig.publish_reel(url, caption=manifest["reel2"]["caption"])
            results.append(("Reel #2", "OK", media_id))
        except Exception as exc:
            traceback.print_exc()
            results.append(("Reel #2", "FAILED", str(exc)))

    # 4) Stories (plain image -- no interactive stickers, see instagram_publisher.py)
    for i, relpath in enumerate(manifest.get("stories", []), start=1):
        try:
            url = _url(date_str, relpath)
            media_id = ig.publish_story_image(url)
            results.append((f"Story {i}", "OK", media_id))
        except Exception as exc:
            traceback.print_exc()
            results.append((f"Story {i}", "FAILED", str(exc)))

    # 5) Saturday bonus: meme/humor feed post, when the day's plan has one
    if manifest.get("meme", {}).get("image"):
        try:
            url = _url(date_str, manifest["meme"]["image"])
            media_id = ig.publish_feed_image(url, caption=manifest["meme"]["caption"])
            results.append(("Meme post", "OK", media_id))
        except Exception as exc:
            traceback.print_exc()
            results.append(("Meme post", "FAILED", str(exc)))

    summary = "\n".join(f"{name}: {status} ({detail})" for name, status, detail in results)
    print(summary)
    telegram_sender.send_text(f"📤 Instagram publish report — {date_str}\n\n{summary}")


if __name__ == "__main__":
    main()
