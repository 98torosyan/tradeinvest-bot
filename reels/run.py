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


def summary(text):
    """Written to the GitHub run page, so problems are visible without logs."""
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n\n")


def notify(text):
    summary(text)
    try:
        sys.path.insert(0, ROOT)
        from delivery.telegram_sender import send_text
        send_text(text)
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] {exc}")


def make_cover(html, out_jpg):
    """Screenshot of the moment the title is fully on screen -> Reel cover
    (otherwise Instagram picks the first, still-empty frame)."""
    import re
    from playwright.sync_api import sync_playwright
    m = re.search(r'data-out="([\d.]+)"', html)
    t = max(1.5, float(m.group(1)) - 0.9) if m else 3.0
    path = out_jpg + ".html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(f"file://{path}")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(400)
        pg.evaluate(f"seek({t})")
        pg.screenshot(path=out_jpg, type="jpeg", quality=92)
        b.close()
    os.remove(path)


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
    ap.add_argument("--kind", choices=["lesson", "news", "story"], required=True)
    ap.add_argument("--no-publish", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "output", "reels"))
    a = ap.parse_args()

    now = dt.datetime.now(ZoneInfo("Asia/Yerevan"))
    st = state.load()
    kind = a.kind
    st["palette"].setdefault(kind, 0); st["music"].setdefault(kind, 0)
    pal_list = palettes.LESSON if kind == "lesson" else palettes.NEWS
    palette = palettes.NEWS[0] if kind == "story" else pal_list[st["palette"][kind] % len(pal_list)]

    if kind == "lesson":
        with open(LESSONS, encoding="utf-8") as f:
            course = json.load(f)
        idx = st.get("course_index", 0)
        if idx >= len(course):
            notify("📚 Դասընթացի պատրաստի դասերը վերջացան։ Պետք է ավելացնել հաջորդ մակարդակը (տես reels/curriculum.md)։")
            print("course finished"); return 0
        left = len(course) - idx - 1
        if left < 10:
            notify(f"📚 Դասընթացում մնացել է {left} պատրաստի դաս։ Ժամանակն է պատրաստել հաջորդ մակարդակը։")
        spec = course[idx]
        html = builder.build_lesson(spec, palette)
        head = f"Մակարդակ {spec['level']}՝ {spec['level_name']} | Դաս {spec['n']}/{spec['total']}"
        caption = head + "\n\n" + spec["caption"].strip() + "\n\n" + HASHTAGS_LESSON
        label = f"դաս «{spec['title']}» ({head})"
    elif kind == "story":
        from . import market
        try:
            spec = market.build_spec()
        except Exception as exc:  # noqa: BLE001
            notify(f"⚠️ «Շուկան այսօր» Story-ն չհրապարակվեց՝ {exc}"); raise
        html = builder.build_story(spec, palette, builder.arm_date(now))
        caption = ""
        label = "Story «Շուկան այսօր»"
    else:
        from . import news
        try:
            spec = news.make_spec(st["posted_links"])
        except Exception as exc:  # noqa: BLE001
            notify(f"⚠️ Լուրերի Reel-ը չստեղծվեց՝ {exc}"); raise
        if not spec:
            summary("ℹ️ Լուր չհրապարակվեց՝ հարմար նոր լուր չգտնվեց"); return 0
        html = builder.build_news(spec, palette, builder.arm_date(now))
        caption = spec["caption"].strip()
        label = f"լուր «{spec['headline']}»"

    tracks = render.music_tracks("news" if kind == "story" else kind)
    music = tracks[st["music"][kind] % len(tracks)] if tracks else None
    rid = now.strftime("%Y%m%d-%H%M") + f"-{kind}"
    os.makedirs(a.out, exist_ok=True)
    mp4 = os.path.join(a.out, rid + ".mp4")
    t0 = time.time()
    dur = render.render(html, mp4, music)
    cover = os.path.join(a.out, rid + ".jpg")
    make_cover(html, cover)
    with open(os.path.join(a.out, rid + ".txt"), "w", encoding="utf-8") as f:
        f.write(caption)
    print(f"rendered {mp4} ({dur:.1f}s video, {time.time() - t0:.0f}s render, palette={palette['name']}, music={music and os.path.basename(music)})")

    # advance rotation state
    st["palette"][kind] += 1
    st["music"][kind] += 1
    if kind == "lesson":
        st["course_index"] = st.get("course_index", 0) + 1
    elif kind == "news":
        st["posted_links"].append(spec["link"])
    if a.no_publish:
        return 0

    os.makedirs(DOCS_REELS, exist_ok=True)
    shutil.copy(mp4, os.path.join(DOCS_REELS, rid + ".mp4"))
    shutil.copy(cover, os.path.join(DOCS_REELS, rid + ".jpg"))
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
    from config import IG_USER_ID
    from delivery import instagram_publisher as ig
    url = f"{PAGES_BASE_URL}/reels/{rid}.mp4"
    cover_url = f"{PAGES_BASE_URL}/reels/{rid}.jpg"
    if not wait_until_reachable(url, timeout=300):
        notify(f"⚠️ Reel-ը չհրապարակվեց. ֆայլը GitHub Pages-ում հասանելի չդարձավ՝ {url}")
        return 1
    try:
        if not ig._configured():
            media_id = None
        else:
            if kind == "story":
                params = dict(media_type="STORIES", video_url=url)
            else:
                params = dict(media_type="REELS", video_url=url, caption=caption)
                if wait_until_reachable(cover_url, timeout=120):
                    params["cover_url"] = cover_url
            container = ig._post(f"{IG_USER_ID}/media", **params)
            ig._wait_until_finished(container["id"])
            media_id = ig._publish(container["id"])
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
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        summary(f"❌ Սխալ՝ {type(exc).__name__}: {exc}")
        raise
