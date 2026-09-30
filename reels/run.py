"""TradeInvest v1.0 entry point:  python -m reels.run --kind lesson|news|story|chart|quiz|carousel [--no-publish]"""
import argparse
import datetime as dt
import os
import subprocess
import sys
import traceback
from zoneinfo import ZoneInfo

from . import (builder, captions, control, curriculum, hosting, lesson_video, music, palettes, qa, render,
               settings, state)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "reels")
LOG = os.path.join(ROOT, "reels", "last_run.md")
RUN_LOG = []
sys.path.insert(0, ROOT)


def summary(text):
    print(text); RUN_LOG.append(str(text))
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        open(p, "a", encoding="utf-8").write(str(text) + "\n\n")


def notify(text):
    summary(text)
    try:
        from delivery.telegram_sender import send_text
        send_text(text)
    except Exception as exc:  # noqa: BLE001
        print("[notify]", exc)


def ping(suffix=""):
    """Healthchecks.io: if no ping arrives for hours, it alerts us independently of GitHub."""
    url = os.environ.get("HEALTHCHECK_URL", "").strip()
    if url:
        try:
            import requests
            requests.get(url.rstrip("/") + suffix, timeout=10)
        except Exception:  # noqa: BLE001
            pass


def write_log(kind, status, now):
    old = open(LOG, encoding="utf-8").read().split("\n---\n")[:20] if os.path.exists(LOG) else []
    entry = f"**{now:%Y-%m-%d %H:%M}** `{kind}` {status}\n" + "\n".join(f"- {l}" for l in RUN_LOG[-25:])
    open(LOG, "w", encoding="utf-8").write("\n---\n".join([entry] + old))


def already_posted(marker_text):
    from . import igapi
    try:
        for m in igapi.recent_media(25):
            if marker_text in (m.get("caption") or ""):
                return m
    except Exception as exc:  # noqa: BLE001
        summary(f"[dedupe] check unavailable: {str(exc)[:120]}")
    return None


def publish_story_file(path, rid, publish):
    urls = hosting.publish([(path, f"reels/{rid}.mp4")])
    from delivery.media_hosting import wait_until_reachable
    url = urls[f"reels/{rid}.mp4"]
    if not wait_until_reachable(url, timeout=300):
        raise RuntimeError(f"not reachable on Pages: {url}")
    if not publish:
        return None
    from . import igapi
    return igapi.publish_story_video(url)


# ---------------------------------------------------------------- lesson
def do_lesson(st, now, rid, publish):
    from delivery.media_hosting import wait_until_reachable
    cur = curriculum.load()
    idx = st.get("course_index", 0)
    lesson, nxt = curriculum.next_lesson(cur, idx)
    if lesson is None:
        notify("🎓 Դասընթացի բոլոր դասերը հրապարակված են։"); return "done"
    errs = qa.pre_render(lesson, cur, set(st.get("published", {})))
    if errs:
        if any("not written" in e for e in errs):
            if st.get("no_script_alert") != now.strftime("%Y-%m-%d"):
                st["no_script_alert"] = now.strftime("%Y-%m-%d")
                notify(f"📚 {lesson['id']} «{lesson['title']}» դասի սցենարը դեռ գրված չէ։ Դասերը կանգնած են, մինչև հաջորդ մոդուլը պատրաստ լինի։")
            return "no-script"
        notify("⚠️ Դասը չանցավ ստուգումը.\n" + "\n".join(errs)); return "qa-fail"
    m = lesson["module"]; size = curriculum.module_size(cur, m)
    marker = f"{captions.marker(lesson, size)} · {lesson['title']}"
    dup = already_posted(marker) if publish else None
    if dup:
        summary(f"[dedupe] {lesson['id']} is already on Instagram ({dup['id']}), only the state is updated")
        st.setdefault("published", {})[lesson["id"]] = {"media": dup["id"], "permalink": dup.get("permalink"),
                                                       "date": now.strftime("%Y-%m-%d"), "hour": now.hour}
        st["course_index"] = idx + 1; return "dedupe"
    pal = palettes.MODULE[m]
    track = music.pick("lesson", m, st, now.strftime("%Y-%m-%d"))
    info = {"module_size": size, "next_title": nxt["title"] if nxt else None}
    mp4, cover = os.path.join(OUT, rid + ".mp4"), os.path.join(OUT, rid + ".jpg")
    cache = st.setdefault("clip_checks", {})
    res = lesson_video.render_lesson(lesson, info, pal, mp4, cover, music=track, used_ids=st.get("used_broll", []),
                                     clip_cache=cache)
    if len(cache) > 600:
        st["clip_checks"] = dict(list(cache.items())[-400:])
    from . import pexels
    RUN_LOG.extend(pexels.NOTES)
    caption, arm = captions.lesson_caption(lesson, size, st)
    from . import music_hunt
    credit = music_hunt.credit_for(track)
    if credit:
        caption = caption.replace("\n\n#", f"\n{credit}\n\n#", 1) if "\n\n#" in caption else caption + "\n" + credit
    errs, warns = qa.post_render(lesson, res, caption)
    for w in warns:
        summary("[qa warning] " + w)
    if errs:
        fails = st.setdefault("qa_fail", {}); fails[lesson["id"]] = fails.get(lesson["id"], 0) + 1
        if fails[lesson["id"]] >= 2:
            st["course_index"] = idx + 1
            notify(f"⏭ {lesson['id']} դասը 2 անգամ չանցավ ստուգումը և բաց է թողնվում.\n" + "\n".join(errs[:6]))
        else:
            notify(f"⚠️ {lesson['id']} դասը չանցավ ստուգումը (կփորձվի նորից).\n" + "\n".join(errs[:6]))
        return "qa-fail"
    teaser = None
    if now.hour in settings.TEASER_HOURS:
        try:
            teaser = os.path.join(OUT, rid + "-teaser.mp4")
            render.make_teaser(mp4, builder.teaser_overlay(pal, "lesson"), teaser)
        except Exception as exc:  # noqa: BLE001
            summary(f"[teaser] {exc}"); teaser = None
    files = [(mp4, f"reels/{rid}.mp4"), (cover, f"reels/{rid}.jpg")] + ([(teaser, f"reels/{rid}-teaser.mp4")] if teaser else [])
    from . import site
    site_dir = os.path.join(OUT, "site"); site.build(cur, st, site_dir)
    if not publish:
        summary(f"[dry-run] {lesson['id']} rendered: {res['duration']:.1f}s, cta={arm}"); return "dry-run"
    urls = hosting.publish(files, site_dir)
    if not wait_until_reachable(urls[f"reels/{rid}.mp4"], timeout=300):
        raise RuntimeError("video is not reachable on GitHub Pages")
    from . import igapi
    wait_until_reachable(urls[f"reels/{rid}.jpg"], timeout=60)
    media = igapi.publish_reel(urls[f"reels/{rid}.mp4"], caption, cover_url=urls[f"reels/{rid}.jpg"], share_to_feed=True)
    st.setdefault("published", {})[lesson["id"]] = {"media": media, "permalink": igapi.permalink(media),
                                                   "date": now.strftime("%Y-%m-%d"), "hour": now.hour, "cta": arm}
    st["course_index"] = idx + 1
    st["used_broll"] = (st.get("used_broll", []) + res["clips"])[-80:]
    summary(f"✅ {lesson['id']} «{lesson['title']}» published ({res['duration']:.0f}s, cta={arm})")
    if teaser:
        try:
            igapi.publish_story_video(urls[f"reels/{rid}-teaser.mp4"]); summary("✅ teaser Story published")
        except Exception as exc:  # noqa: BLE001
            summary(f"⚠️ teaser failed (the Reel is fine): {str(exc)[:160]}")
    left = curriculum.scripted_left(cur, idx + 1)
    if left < settings.COURSE_LOW_WARNING and st.get("low_alert") != now.strftime("%Y-%m-%d"):
        st["low_alert"] = now.strftime("%Y-%m-%d")
        notify(f"📚 Մնացել է {left} պատրաստի սցենար։")
    return "published"


# ---------------------------------------------------------------- news
def do_news(st, now, rid, publish):
    from . import news, pexels
    from delivery.media_hosting import wait_until_reachable
    spec = news.make_spec(st.get("posted_links", []))
    RUN_LOG.extend(news.NOTES)
    if not spec:
        summary("ℹ️ Լուր չհրապարակվեց՝ հարմար նոր լուր չգտնվեց"); return "skipped"
    ok, bad = qa.text_ok(" ".join([spec["headline"], spec.get("sub", "")] +
                                  [p["text"] for stp in spec["steps"] for p in stp["paragraphs"]] + [spec.get("caption", "")]))
    if not ok:
        notify(f"⚠️ Լուրը չհրապարակվեց՝ ուղղագրական ստուգումը չանցավ. {', '.join(bad[:8])}\n"
               f"Եթե բառերը ճիշտ են, գրիր՝ /allow {' '.join(bad[:8])}"); return "qa-fail"
    k = st.setdefault("palette", {}).get("news", 0); pal = palettes.NEWS[k % len(palettes.NEWS)]
    bg, vid = pexels.fetch(spec.get("broll", ""), set(st.get("used_broll", [])), check=lesson_video._clip_ok(False, st.setdefault("clip_checks", {})))
    RUN_LOG.extend(pexels.NOTES)
    html = builder.build_news(spec, pal, builder.arm_date(now), footage=bool(bg))
    mp4 = os.path.join(OUT, rid + ".mp4")
    ntrack = music.pick("news", None, st, now.strftime("%Y-%m-%d"))
    dur = render.render(html, mp4, ntrack, background=bg,
                        tint="0x" + pal["bg"].split("#", 1)[1][:6])
    caption = spec["caption"].strip()
    from . import music_hunt
    if music_hunt.credit_for(ntrack):
        caption += "\n" + music_hunt.credit_for(ntrack)
    if caption.count("#") > settings.MAX_HASHTAGS:
        caption = caption[: caption.find("#")].rstrip() + "\n\n" + " ".join([t for t in caption.split() if t.startswith("#")][:5])
    if not publish:
        summary(f"[dry-run] news rendered {dur:.1f}s"); return "dry-run"
    urls = hosting.publish([(mp4, f"reels/{rid}.mp4")])
    if not wait_until_reachable(urls[f"reels/{rid}.mp4"], timeout=300):
        raise RuntimeError("video is not reachable on GitHub Pages")
    from . import igapi
    media = igapi.publish_reel(urls[f"reels/{rid}.mp4"], caption, share_to_feed=False)   # Reels tab only: grid stays a course library
    st["palette"]["news"] = k + 1
    st.setdefault("posted_links", []).append(spec["link"])
    if vid:
        st["used_broll"] = (st.get("used_broll", []) + [vid])[-80:]
    st.setdefault("news_media", []).append({"media": media, "date": now.strftime("%Y-%m-%d")})
    st["news_media"] = st["news_media"][-60:]
    summary(f"✅ News published: {spec['headline']}"); return "published"


# ---------------------------------------------------------------- stories
def do_story(st, now, rid, publish, chart=False):
    from . import market
    pal = palettes.NEWS[0]
    if chart:
        spec = market.build_chart_spec(); html = builder.build_chart_story(spec, pal, builder.arm_date(now))
    else:
        spec = market.build_spec(); html = builder.build_story(spec, pal, builder.arm_date(now))
    RUN_LOG.extend(market.NOTES)
    mp4 = os.path.join(OUT, rid + ".mp4")
    render.render(html, mp4, music.pick("story", None, st, now.strftime("%Y-%m-%d")))
    if not publish:
        return "dry-run"
    publish_story_file(mp4, rid, publish); summary("✅ Story published"); return "published"


def do_quiz(st, now, rid, publish):
    from . import quiz
    cur = curriculum.load()
    y = (now - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    lesson = quiz.pick(cur, st, y)
    if not lesson:
        summary("ℹ️ Quiz չկա՝ երեկ դաս չի հրապարակվել"); return "skipped"
    mp4 = os.path.join(OUT, rid + ".mp4")
    render.render(quiz.html(lesson, palettes.MODULE[lesson["module"]]), mp4,
                  music.pick("quiz", lesson["module"], st, now.strftime("%Y-%m-%d")))
    if not publish:
        return "dry-run"
    publish_story_file(mp4, rid, publish); st["quiz_count"] = st.get("quiz_count", 0) + 1
    summary(f"✅ Quiz Story from {lesson['id']}"); return "published"


def do_carousel(st, now, rid, publish):
    from . import carousel
    from delivery.media_hosting import wait_until_reachable
    cur = {l["id"]: l for l in curriculum.load()["lessons"]}
    since = (now - dt.timedelta(days=7)).strftime("%Y-%m-%d")
    ls = [cur[i] for i, p in sorted(st.get("published", {}).items(), key=lambda kv: kv[1].get("date", "")) if p.get("date", "") >= since and i in cur]
    if len(ls) < 2:
        summary("ℹ️ Carousel չկա՝ քիչ դասեր այս շաբաթ"); return "skipped"
    ls = ls[-24:]
    pages = carousel.slides(ls, palettes.MODULE[ls[-1]["module"]], f"{since} → {now:%Y-%m-%d}")
    imgs = carousel.render(pages, os.path.join(OUT, rid + "-car"))
    if not publish:
        return "dry-run"
    urls = hosting.publish([(p, f"reels/{rid}-{i}.jpg") for i, p in enumerate(imgs)])
    ordered = [urls[f"reels/{rid}-{i}.jpg"] for i in range(len(imgs))]
    if not wait_until_reachable(ordered[-1], timeout=300):
        raise RuntimeError("carousel images not reachable")
    from . import igapi
    cap = ("Շաբաթը մեկ էջով 📚\nԱյս շաբաթվա դասերի ամփոփումը մեկ տեղում։ Պահիր՝ կրկնելու համար։\n\n"
           "📩 Ուղարկիր նրան, ով սովորում է crypto\n📚 Ամբողջ դասընթացը՝ հղումը bio-ում\n\n#crypto #trading #կրիպտո #հայերեն #cryptoeducation")
    igapi.publish_carousel(ordered, cap); summary("✅ Weekly carousel published"); return "published"


def do_music(st, now, rid, publish):
    from . import music_hunt
    if not settings.MUSIC_HUNT_ENABLED:
        summary("🎵 automatic music search is off (tracks come from the owner via Telegram)"); return "skipped"
    n = music_hunt.hunt() if publish else 0
    summary(f"🎵 music candidates sent to Telegram: {n}"); return "done"


HANDLERS = {"music": do_music, "lesson": do_lesson, "news": do_news, "story": lambda s, n, r, p: do_story(s, n, r, p, False),
            "chart": lambda s, n, r, p: do_story(s, n, r, p, True), "quiz": do_quiz, "carousel": do_carousel}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=list(HANDLERS), required=True)
    ap.add_argument("--no-publish", action="store_true")
    a = ap.parse_args()
    now = dt.datetime.now(ZoneInfo(settings.TZ))
    publish = not a.no_publish
    if publish:
        subprocess.run(["git", "pull", "-q", "--rebase"], cwd=ROOT)
    if control.paused():
        summary("⏸ paused (Telegram /pause) — nothing published"); return 0
    os.makedirs(OUT, exist_ok=True)
    if publish:
        try:
            from . import music_hunt
            added = music_hunt.install_approved() + music_hunt.install_incoming()
            if added:
                notify("🎵 Գրադարանին ավելացան՝ " + ", ".join(added))
        except Exception as exc:  # noqa: BLE001
            print("[music] approved tracks not installed:", exc)
    st = state.load()
    rid = now.strftime("%Y%m%d-%H%M") + f"-{a.kind}"
    status = "❌ failed"
    try:
        status = "✅ " + HANDLERS[a.kind](st, now, rid, publish)
        if publish:
            ping()
        return 0
    except Exception as exc:  # noqa: BLE001
        if publish:
            ping("/fail")
        notify(f"❌ {a.kind} սխալ՝ {type(exc).__name__}: {str(exc)[:300]}")
        print(traceback.format_exc())
        return 1
    finally:
        if publish and status.startswith("❌"):
            ping("/fail")                                            # instant alert from Healthchecks.io
        if publish:
            state.save(st); write_log(a.kind, status, now)
            control.commit(["reels/state.json", "reels/last_run.md", "control", "reels/assets/music"], f"run: {rid} {status}")


if __name__ == "__main__":
    sys.exit(main())
