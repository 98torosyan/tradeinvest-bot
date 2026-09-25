"""Entry point: python -m reels.run --kind lesson|news [--no-publish]

1. build the script (lesson bank or fresh news via Gemini)
2. render it to MP4 with the next colour palette and music track
3. host it on GitHub Pages (docs/reels/), publish it as an Instagram Reel
4. report the result to Telegram
"""
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

from . import builder, palettes, render, state

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_REELS = os.path.join(ROOT, "docs", "reels")
LESSONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lessons.json")
KEEP_DAYS = 3
HASHTAGS_LESSON = "#crypto #bitcoin #կրիպտո #հայերեն #cryptoeducation"


def notify(text):
    try:
        sys.path.insert(0, ROOT)
        from delivery.telegram_sender import send_text
        send_text(text)
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] {exc}")


def git(*args):
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def cleanup_old(now):
    removed = False
    legacy = os.path.join(ROOT, "docs", "media")  # old daily pipeline output, no longer used
    if os.path.isdir(legacy):
        shutil.rmtree(legacy); removed = True
    if os.path.isdir(DOCS_REELS):
        cutoff = (now - dt.timedelta(days=KEEP_DAYS)).strftime("%Y%m%d")
        for f in os.listdir(DOCS_REELS):
            if f[:8].isdigit() and f[:8] < cutoff:
                os.remove(os.path.join(DOCS_REELS, f)); removed = True
    return removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["lesson", "news"], required=True)
    ap.add_argument("--no-publish", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "output", "reels"))
    a = ap.parse_args()

    now = dt.datetime.now(ZoneInfo("Asia/Yerevan"))
    st = state.load()
    kind = a.kind
    pal_list = palettes.NEWS if kind == "news" else palettes.LESSON
    palette = pal_list[st["palette"][kind] % len(pal_list)]

    if kind == "lesson":
        with open(LESSONS, encoding="utf-8") as f:
            bank = json.load(f)
        spec = bank[st["lesson_index"] % len(bank)]
        html = builder.build_lesson(spec, palette)
        caption = spec["caption"].strip() + "\n\n" + HASHTAGS_LESSON
        label = f"դաս «{spec['title']}»"
    else:
        from . import news
        try:
            spec = news.make_spec(st["posted_links"])
        except Exception as exc:  # noqa: BLE001
            notify(f"⚠️ Լուրերի Reel-ը չստեղծվեց՝ {exc}"); raise
        if not spec:
            print("nothing to publish"); return 0
        html = builder.build_news(spec, palette, builder.arm_date(now))
        caption = spec["caption"].strip()
        label = f"լուր «{spec['headline']}»"

    tracks = render.music_tracks(kind)
    music = tracks[st["music"][kind] % len(tracks)] if tracks else None
    rid = now.strftime("%Y%m%d-%H%M") + f"-{kind}"
    os.makedirs(a.out, exist_ok=True)
    mp4 = os.path.join(a.out, rid + ".mp4")
    t0 = time.time()
    dur = render.render(html, mp4, music)
    with open(os.path.join(a.out, rid + ".txt"), "w", encoding="utf-8") as f:
        f.write(caption)
    print(f"rendered {mp4} ({dur:.1f}s video, {time.time() - t0:.0f}s render, palette={palette['name']}, music={music and os.path.basename(music)})")

    # advance rotation state
    st["palette"][kind] += 1
    st["music"][kind] += 1
    if kind == "lesson":
        st["lesson_index"] += 1
    else:
        st["posted_links"].append(spec["link"])
    if a.no_publish:
        return 0

    os.makedirs(DOCS_REELS, exist_ok=True)
    shutil.copy(mp4, os.path.join(DOCS_REELS, rid + ".mp4"))
    open(os.path.join(ROOT, "docs", ".nojekyll"), "a").close()
    cleanup_old(now)
    state.save(st)
    git("add", "-A", "docs", "reels/state.json")
    git("commit", "-m", f"reel: {rid}")
    git("pull", "--rebase", "--quiet")
    git("push")

    sys.path.insert(0, ROOT)
    from config import PAGES_BASE_URL
    from delivery.media_hosting import wait_until_reachable
    from delivery.instagram_publisher import publish_reel
    url = f"{PAGES_BASE_URL}/reels/{rid}.mp4"
    if not wait_until_reachable(url, timeout=300):
        notify(f"⚠️ Reel-ը չհրապարակվեց. ֆայլը GitHub Pages-ում հասանելի չդարձավ՝ {url}")
        return 1
    try:
        media_id = publish_reel(url, caption)
    except Exception as exc:  # noqa: BLE001
        notify(f"⚠️ Instagram-ը մերժեց Reel-ը ({label})՝ {exc}")
        raise
    if not media_id:
        notify("⚠️ Instagram-ի secret-ները (IG_USER_ID / IG_ACCESS_TOKEN) բացակայում են. Reel-ը չհրապարակվեց")
        return 1
    notify(f"✅ Հրապարակվեց՝ {label}\nԳույն՝ {palette['name']}, տևողություն՝ {dur:.0f} վրկ")
    print("published", media_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
