"""TradeInvest v1.0 entry point:  python -m reels.run --kind lesson|news|story|chart|quiz|carousel|analysis [--no-publish]"""
import argparse
import datetime as dt
import json
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


def teaser_due(now):
    """True for the teaser slots, even when GitHub starts the run late (its cron is often 10-60 min behind)."""
    m = now.hour * 60 + now.minute
    return any(-30 <= m - (h * 60 + mm) <= 100 for h, mm in settings.TEASER_SLOTS)   # windows never touch 19:07


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


# ---------------------------------------------------------------- standalone trading Reels ("hits")
def do_hit(st, now, rid, publish):
    from delivery.media_hosting import wait_until_reachable
    cur = json.load(open(HITS, encoding="utf-8"))
    done = set(st.get("published", {}))
    todo = [l for l in cur["lessons"] if l["id"] not in done]
    left = len(todo)
    if left <= settings.COURSE_LOW_WARNING and st.get("hits_low_alert") != now.strftime("%Y-%m-%d"):
        st["hits_low_alert"] = now.strftime("%Y-%m-%d")
        notify(f"📚 Մնացել է {left} պատրաստի Reel (~{left / max(1, settings.LESSONS_PER_DAY):.1f} օր)։ Ժամանակն է գրել նորերը։")
    if not todo:
        return "no-script"
    lesson = todo[0]
    st["course_index"] = len(cur["lessons"]) - left          # position in the hits list (used by /status and watchdog)
    errs = qa.pre_render(lesson, cur, done)
    if errs:
        notify("⚠️ Reel-ը չանցավ ստուգումը.\n" + "\n".join(errs)); return "qa-fail"
    title_line = f"📈 {lesson['series']} · {lesson['title']}"
    dup = already_posted(title_line) if publish else None
    if dup:
        summary(f"[dedupe] {lesson['id']} is already on Instagram ({dup['id']}), only the state is updated")
        st.setdefault("published", {})[lesson["id"]] = {"media": dup["id"], "permalink": dup.get("permalink"),
                                                       "date": now.strftime("%Y-%m-%d"), "hour": now.hour}
        st["course_index"] += 1
        return "dedupe"
    if lesson.get("style"):
        pal = palettes.for_lesson(lesson)
    else:
        pal = palettes.MODULE[SERIES_PALETTE.get(lesson["module"], 5)]
    track = music.pick("lesson", lesson["module"], st, now.strftime("%Y-%m-%d"))
    mp4, cover = os.path.join(OUT, rid + ".mp4"), os.path.join(OUT, rid + ".jpg")
    arm = captions.choose_cta(st, lesson)
    lesson = dict(lesson, _cta=arm)                     # the Reel's last screen shows the same call to action
    res = lesson_video.render_lesson(lesson, {"module_size": 0, "next_title": None}, pal, mp4, cover, music=track,
                                     used_ids=[], clip_cache={})
    caption, arm = captions.hit_caption(lesson, title_line, st, arm)
    errs, warns = qa.post_render(lesson, res, caption)
    for w in warns:
        summary("[qa warning] " + w)
    if errs:
        fails = st.setdefault("qa_fail", {}); fails[lesson["id"]] = fails.get(lesson["id"], 0) + 1
        if fails[lesson["id"]] >= 2:
            st.setdefault("published", {})[lesson["id"]] = {"skipped": True, "date": now.strftime("%Y-%m-%d")}
            notify(f"⏭ {lesson['id']} Reel-ը 2 անգամ չանցավ ստուգումը և բաց է թողնվում.\n" + "\n".join(errs[:6]))
        else:
            notify(f"⚠️ {lesson['id']} Reel-ը չանցավ ստուգումը (կփորձվի նորից).\n" + "\n".join(errs[:6]))
        return "qa-fail"
    teaser = None
    if teaser_due(now):
        try:
            teaser = os.path.join(OUT, rid + "-teaser.mp4")
            render.make_teaser(mp4, builder.teaser_overlay(pal, "lesson"), teaser)
        except Exception as exc:  # noqa: BLE001
            summary(f"[teaser] {exc}"); teaser = None
    files = [(mp4, f"reels/{rid}.mp4"), (cover, f"reels/{rid}.jpg")] + ([(teaser, f"reels/{rid}-teaser.mp4")] if teaser else [])
    from . import site
    site_dir = os.path.join(OUT, "site"); site.build(cur, st, site_dir)
    if not publish:
        summary(f"[dry-run] {lesson['id']} rendered {res['duration']:.1f}s"); return "dry-run"
    urls = hosting.publish(files, site_dir)
    if not wait_until_reachable(urls[f"reels/{rid}.mp4"], timeout=300):
        raise RuntimeError("video is not reachable on GitHub Pages")
    from . import igapi
    media = igapi.publish_reel(urls[f"reels/{rid}.mp4"], caption, cover_url=urls.get(f"reels/{rid}.jpg"))
    try:
        link = igapi.permalink(media)
    except Exception:  # noqa: BLE001
        link = None
    st.setdefault("published", {})[lesson["id"]] = {"media": media, "permalink": link,
                                                   "date": now.strftime("%Y-%m-%d"), "hour": now.hour, "cta": arm}
    if teaser:
        try:
            publish_story_file(teaser, rid + "-teaser", True)
        except Exception as exc:  # noqa: BLE001
            summary(f"[teaser] {exc}")
    st["course_index"] += 1
    summary(f"✅ {lesson['id']} «{lesson['title']}» published ({res['duration']:.0f}s, cta={arm})")
    return "published"


# ---------------------------------------------------------------- lesson
HITS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "hits.json")
SERIES_PALETTE = {1: 5, 2: 8, 3: 6, 4: 7, 5: 3}


def quiet(now):
    a, b = settings.QUIET_HOURS
    return a <= now.hour < b


def reel_to_story(urls, rid):
    """Re-share the fresh Reel as a Story (more reach; the owner adds good ones to Highlights by hand)."""
    if not getattr(settings, "REEL_TO_STORY", False):
        return
    from . import igapi
    try:
        igapi.publish_story_video(urls[f"reels/{rid}.mp4"]); summary("✅ Story published")
    except Exception as exc:  # noqa: BLE001
        summary(f"⚠️ Story failed (the Reel is fine): {str(exc)[:160]}")


def do_short(st, now, rid, publish):
    """12:37 short lesson Reel (Remotion, brand «Գիշերային Սևան»)."""
    from . import shorts
    from delivery.media_hosting import wait_until_reachable
    s, left = shorts.next_script(st)
    if not s:
        return None
    if left <= 5 and st.get("shorts_low_alert") != now.strftime("%Y-%m-%d"):
        st["shorts_low_alert"] = now.strftime("%Y-%m-%d")
        notify(f"📚 Մնացել է {left} կարճ դասի սցենար։ Ժամանակն է գրել նորերը։")
    kw = now.weekday() in shorts.KW_DAYS
    mp4, cover = os.path.join(OUT, rid + ".mp4"), os.path.join(OUT, rid + ".jpg")
    dur = shorts.render(s, kw, mp4, cover, music.pick("lesson", None, st, now.strftime("%Y-%m-%d"), need=25))
    if not 8 <= dur <= 25:
        raise RuntimeError(f"short {s['id']} has a bad duration: {dur:.1f}s")
    cap = shorts.caption(s, kw)
    if not publish:
        summary(f"[dry-run] short {s['id']} rendered {dur:.1f}s"); return "dry-run"
    from . import site
    site_dir = os.path.join(OUT, "site"); site.build(curriculum.load(), st, site_dir)     # keeps /start/ (mini course) live
    urls = hosting.publish([(mp4, f"reels/{rid}.mp4"), (cover, f"reels/{rid}.jpg")], site_dir)
    if not wait_until_reachable(urls[f"reels/{rid}.mp4"], timeout=300):
        raise RuntimeError("video is not reachable on GitHub Pages")
    from . import igapi
    media = igapi.publish_reel(urls[f"reels/{rid}.mp4"], cap, cover_url=urls.get(f"reels/{rid}.jpg"))
    today = now.strftime("%Y-%m-%d")
    st.setdefault("shorts_done", {})[s["id"]] = {"media": media, "date": today, "kw": kw}
    st.setdefault("published", {})[s["id"]] = {"media": media, "date": today, "hour": now.hour}
    summary(f"✅ short {s['id']} published ({dur:.0f}s, kw={kw})")
    reel_to_story(urls, rid); return "published"


def do_lesson(st, now, rid, publish):
    # Schedule (executive decision, Nov 2026): 12:37 short lesson · 19:07 analysis Reel · no 21:37 Reel.
    if settings.SHORTS_ENABLED and now.hour >= 18:
        if now.hour < 21:
            return do_analysis(st, now, rid, publish)
        summary("ℹ️ the 21:37 Reel slot is retired"); return "slot-retired"
    if publish and quiet(now):
        summary(f"🌙 {now:%H:%M} is inside quiet hours — the lesson waits for the next slot"); return "skipped-quiet"
    if settings.SHORTS_ENABLED and (not publish or st.get("shorts_last") != now.strftime("%Y-%m-%d")):
        res = do_short(st, now, rid, publish)
        if res:
            if publish:
                st["shorts_last"] = now.strftime("%Y-%m-%d")
            return res
    elif settings.SHORTS_ENABLED:
        summary("ℹ️ today's short is already out"); return "slot-done"
    if publish:                                       # the exact trigger (Cloudflare) and the late GitHub cron may both fire
        from .watchdog import LESSON_SLOTS
        mins = now.hour * 60 + now.minute + 20
        allowed = sum(1 for h, m in LESSON_SLOTS if h * 60 + m <= mins)
        done_today = sum(1 for p in st.get("published", {}).values() if p.get("date") == now.strftime("%Y-%m-%d") and not p.get("skipped"))
        if done_today >= allowed:
            summary(f"ℹ️ {done_today}/{allowed} lessons already out today — nothing to do"); return "slot-done"
    if settings.CONTENT_MODE == "hits":
        return do_hit(st, now, rid, publish)
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
    if teaser_due(now):
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
    k = st.setdefault("palette", {}).get("news", 0); pal = palettes.BRAND
    bg, vid = (None, None) if settings.BG_MODE == "charts" else \
        pexels.fetch(spec.get("broll", ""), set(st.get("used_broll", [])), check=lesson_video._clip_ok(False, st.setdefault("clip_checks", {})))
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
    if settings.NEWS_AS_STORY:                      # news live in Stories only; the grid and Reels tab are for lessons
        if dur > 59:
            cut = mp4.replace(".mp4", "-59.mp4")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-t", "59", "-af", "afade=t=out:st=57:d=2",
                            "-c:v", "copy", cut], check=True)
            os.replace(cut, mp4)
        media = publish_story_file(mp4, rid, publish)
    else:
        urls = hosting.publish([(mp4, f"reels/{rid}.mp4")])
        if not wait_until_reachable(urls[f"reels/{rid}.mp4"], timeout=300):
            raise RuntimeError("video is not reachable on GitHub Pages")
        from . import igapi
        media = igapi.publish_reel(urls[f"reels/{rid}.mp4"], caption, share_to_feed=False)
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
    pal = palettes.BRAND
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
    render.render(quiz.html(lesson, palettes.for_lesson(lesson)), mp4,
                  music.pick("quiz", lesson["module"], st, now.strftime("%Y-%m-%d")))
    if not publish:
        return "dry-run"
    publish_story_file(mp4, rid, publish); st["quiz_count"] = st.get("quiz_count", 0) + 1
    summary(f"✅ Quiz Story from {lesson['id']}"); return "published"


def do_carousel(st, now, rid, publish):
    """Educational carousel (TI Rise), Mon/Wed/Fri 15:07. Falls back to nothing when the scripts run out."""
    from . import edu_carousel as ec
    from delivery.media_hosting import wait_until_reachable
    today = now.strftime("%Y-%m-%d")
    if publish and quiet(now):
        summary("🌙 quiet hours — carousel skipped"); return "skipped-quiet"
    if publish and st.get("edu_carousel_last") == today:
        summary("ℹ️ carousel already published today"); return "skipped"
    c, n = ec.next_one(st)
    if not c:
        notify("📚 Կարուսելների սցենարները վերջացան։ Ժամանակն է գրել նորերը։"); return "skipped"
    imgs = ec.render(ec.slides(c, n), os.path.join(OUT, rid + "-car"))
    cap = ec.caption(c)
    if ec.DISCLAIMER not in cap:
        raise RuntimeError("carousel caption has no disclaimer")
    if not publish:
        summary(f"[dry-run] carousel {c['id']} {len(imgs)} slides"); return "dry-run"
    urls = hosting.publish([(p, f"reels/{rid}-{i}.jpg") for i, p in enumerate(imgs)])
    ordered = [urls[f"reels/{rid}-{i}.jpg"] for i in range(len(imgs))]
    if not wait_until_reachable(ordered[-1], timeout=300):
        raise RuntimeError("carousel images not reachable")
    from . import igapi
    media = igapi.publish_carousel(ordered, cap)
    st.setdefault("edu_carousels_done", {})[c["id"]] = {"media": media, "date": today}
    st["edu_carousel_last"] = today
    summary(f"✅ Carousel {c['id']} published ({len(imgs)} slides)"); return "published"


def do_weekly_carousel_legacy(st, now, rid, publish):
    from . import carousel
    from delivery.media_hosting import wait_until_reachable
    cur = {l["id"]: l for l in curriculum.load()["lessons"]}
    since = (now - dt.timedelta(days=7)).strftime("%Y-%m-%d")
    ls = [cur[i] for i, p in sorted(st.get("published", {}).items(), key=lambda kv: kv[1].get("date", "")) if p.get("date", "") >= since and i in cur and not p.get("skipped")]
    if len(ls) < 2:
        summary("ℹ️ Carousel չկա՝ քիչ դասեր այս շաբաթ"); return "skipped"
    ls = ls[-24:]
    pages = carousel.slides(ls, None, f"{since} → {now:%Y-%m-%d}")
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


def do_analysis(st, now, rid, publish):
    """Daily analysis Reel (Remotion) on real candles; asset rotates by weekday."""
    from . import analysis
    from delivery.media_hosting import wait_until_reachable
    today = now.strftime("%Y-%m-%d")
    if publish and quiet(now):
        summary("🌙 quiet hours — analysis skipped"); return "skipped-quiet"
    if publish and settings.SHORTS_ENABLED and now.hour < 18:
        summary("ℹ️ the analysis Reel moved to 19:07"); return "moved"
    if publish and st.get("analysis_last") == today:
        summary("ℹ️ analysis already published today"); return "skipped"
    asset, info, lv, props, caption = analysis.build(now)
    RUN_LOG.append(f"[analysis] {asset} {lv['kind']} zone={lv['zone'][0]:.2f}-{lv['zone'][1]:.2f} touches={len(lv['touches'])} other={lv['other']:.2f}")
    mp4, cover = os.path.join(OUT, rid + ".mp4"), os.path.join(OUT, rid + ".jpg")
    analysis.render(props, mp4, cover, music.pick("lesson", None, st, today, need=40))
    if analysis.DISCLAIMER not in caption:
        raise RuntimeError("analysis caption has no disclaimer")
    if not publish:
        summary(f"[dry-run] analysis {asset} rendered"); return "dry-run"
    from . import site
    site_dir = os.path.join(OUT, "site"); site.build(curriculum.load(), st, site_dir)
    urls = hosting.publish([(mp4, f"reels/{rid}.mp4"), (cover, f"reels/{rid}.jpg")], site_dir)
    if not wait_until_reachable(urls[f"reels/{rid}.mp4"], timeout=300):
        raise RuntimeError("video is not reachable on GitHub Pages")
    from . import igapi
    media = igapi.publish_reel(urls[f"reels/{rid}.mp4"], caption, cover_url=urls.get(f"reels/{rid}.jpg"))
    st["analysis_last"] = today
    st.setdefault("analysis_media", []).append({"media": media, "asset": asset, "date": today})
    st["analysis_media"] = st["analysis_media"][-60:]
    summary(f"✅ Analysis Reel {asset} published")
    reel_to_story(urls, rid); return "published"


def do_stories_pack(st, now, rid, publish):
    """One-off: publish every image in reels/assets/stories_pack/ (sorted) as Stories, once."""
    import glob, time
    from . import igapi
    from delivery.media_hosting import wait_until_reachable
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "stories_pack")
    done = st.setdefault("stories_pack_done", [])
    files = [f for f in sorted(glob.glob(os.path.join(d, "*.jpg"))) if os.path.basename(f) not in done]
    if not files:
        summary("ℹ️ stories pack: nothing new"); return "skipped"
    if not publish:
        summary(f"[dry-run] stories pack: {len(files)} images"); return "dry-run"
    urls = hosting.publish([(f, f"reels/{rid}-{os.path.basename(f)}") for f in files])
    for f in files:
        u = urls[f"reels/{rid}-{os.path.basename(f)}"]
        if not wait_until_reachable(u, timeout=300):
            raise RuntimeError(f"{u} is not reachable")
        igapi.publish_story_image(u); done.append(os.path.basename(f))
        summary(f"✅ Story {os.path.basename(f)}"); time.sleep(8)
    return "published"


def do_weekly(st, now, rid, publish):
    """Sunday «Շաբաթը մեկ հայացքով» Reel (real daily closes)."""
    from . import weekly
    from delivery.media_hosting import wait_until_reachable
    today = now.strftime("%Y-%m-%d")
    if publish and st.get("weekly_last") == today:
        summary("ℹ️ weekly recap already published today"); return "skipped"
    props = weekly.build(now)
    mp4, cover = os.path.join(OUT, rid + ".mp4"), os.path.join(OUT, rid + ".jpg")
    weekly.render(props, mp4, cover, music.pick("lesson", None, st, today, need=25))
    cap = weekly.caption(props)
    if weekly.DISCLAIMER not in cap:
        raise RuntimeError("weekly caption has no disclaimer")
    if not publish:
        summary("[dry-run] weekly recap rendered"); return "dry-run"
    urls = hosting.publish([(mp4, f"reels/{rid}.mp4"), (cover, f"reels/{rid}.jpg")])
    if not wait_until_reachable(urls[f"reels/{rid}.mp4"], timeout=300):
        raise RuntimeError("video is not reachable on GitHub Pages")
    from . import igapi
    media = igapi.publish_reel(urls[f"reels/{rid}.mp4"], cap, cover_url=urls.get(f"reels/{rid}.jpg"))
    st["weekly_last"] = today
    st.setdefault("weekly_media", []).append({"media": media, "date": today})
    summary("✅ Weekly recap Reel published")
    reel_to_story(urls, rid); return "published"


def _story_image(path, rid):
    from . import igapi
    from delivery.media_hosting import wait_until_reachable
    urls = hosting.publish([(path, f"reels/{rid}.jpg")])
    u = urls[f"reels/{rid}.jpg"]
    if not wait_until_reachable(u, timeout=300):
        raise RuntimeError(f"{u} is not reachable")
    return igapi.publish_story_image(u)


def do_challenge(st, now, rid, publish):
    """«30 օր, 30 կանոն» daily Story at 10:07."""
    from . import story_cards as sc
    today = now.strftime("%Y-%m-%d")
    ch = st.setdefault("challenge30", {"day": 0, "last": ""})
    if publish and ch.get("last") == today:
        summary("ℹ️ challenge story already published today"); return "skipped"
    n = len(sc.challenge_rules())
    if ch["day"] >= n:
        summary("ℹ️ the 30-day challenge is finished"); return "skipped"
    day = ch["day"] + 1
    img = sc.render(sc.challenge_page(day), os.path.join(OUT, rid + ".jpg"))
    if not publish:
        summary(f"[dry-run] challenge day {day}"); return "dry-run"
    _story_image(img, rid)
    ch.update(day=day, last=today)
    summary(f"✅ Challenge Story day {day}/{n}")
    try:                                         # economic calendar Story: Monday = the week, other days = today's events
        from . import econ
        kind, evs = econ.plan(now)
        if kind and st.get("econ_last") != today:
            page = econ.week_page(evs) if kind == "week" else econ.today_page(evs)
            _story_image(sc.render(page, os.path.join(OUT, rid + "-econ.jpg")), rid + "-econ")
            st["econ_last"] = today
            summary(f"✅ Economic calendar Story ({kind}, {len(evs)} events)")
    except Exception as exc:  # noqa: BLE001
        summary(f"⚠️ economic calendar skipped: {str(exc)[:160]}")
    return "published"


def do_alert(st, now, rid, publish):
    """Hourly: if BTC/ETH moved ≥ 5 % in 24 h, publish one alert Story (max one per asset per 12 h)."""
    import requests
    from . import analysis, story_cards as sc
    if quiet(now):
        return "skipped-quiet"
    done = []
    for asset, sym in (("BTC", "BTCUSDT"), ("ETH", "ETHUSDT")):
        try:
            t = requests.get("https://data-api.binance.vision/api/v3/ticker/24hr", params={"symbol": sym}, timeout=20).json()
            pct, last, hi, lo = float(t["priceChangePercent"]), float(t["lastPrice"]), float(t["highPrice"]), float(t["lowPrice"])
        except Exception as exc:  # noqa: BLE001
            summary(f"[alert] {asset}: {exc}"); continue
        prev = st.setdefault("alerts", {}).get(asset, 0)
        if abs(pct) < settings.ALERT_PCT or now.timestamp() - prev < 12 * 3600:
            continue
        lv = analysis.levels(analysis.candles(asset))
        f = lambda v: (lambda x: x if x.startswith("$") else "$" + x)(analysis.fmt(asset, v))  # noqa: E731
        z = f"{f(lv['zone'][0])}–{f(lv['zone'][1])}"
        img = sc.render(sc.alert_page(analysis.NAME_HY[asset], asset, pct, f(last), f(hi), f(lo), z, f(lv["other"])),
                        os.path.join(OUT, f"{rid}-{asset}.jpg"))
        if not publish:
            summary(f"[dry-run] alert {asset} {pct:+.1f}%"); done.append(asset); continue
        _story_image(img, f"{rid}-{asset}")
        st["alerts"][asset] = now.timestamp()
        summary(f"✅ Alert Story {asset} {pct:+.1f}%"); done.append(asset)
    return "published" if done else "no-move"


def do_monthly(st, now, rid, publish):
    """1st of the month: «Bitcoin-ի <ամիս>ը մեկ նկարում» infographic for the previous month (feed image post)."""
    from . import monthly
    from delivery.media_hosting import wait_until_reachable
    from playwright.sync_api import sync_playwright
    first = now.date().replace(day=1)
    prev = first - dt.timedelta(days=1)
    key = f"{prev.year}-{prev.month:02d}"
    if publish and st.get("monthly_last") == key:
        summary("ℹ️ monthly infographic already published"); return "skipped"
    D = monthly.data(prev.year, prev.month)
    html = os.path.join(OUT, rid + ".html"); img = os.path.join(OUT, rid + ".jpg")
    open(html, "w", encoding="utf-8").write(monthly.page(prev.year, prev.month, D))
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(f"file://{html}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        pg.screenshot(path=img, type="jpeg", quality=92); b.close()
    cap = monthly.caption(prev.year, prev.month, D)
    if not publish:
        summary(f"[dry-run] monthly {key}"); return "dry-run"
    urls = hosting.publish([(img, f"reels/{rid}.jpg")])
    u = urls[f"reels/{rid}.jpg"]
    if not wait_until_reachable(u, timeout=300):
        raise RuntimeError("image not reachable")
    from . import igapi
    media = igapi.publish_image(u, cap)
    st["monthly_last"] = key
    st.setdefault("monthly_media", []).append({"media": media, "date": now.strftime("%Y-%m-%d")})
    summary(f"✅ Monthly infographic {key} published"); return "published"


def do_econ_dry(st, now, rid, publish):
    from . import econ, story_cards as sc
    evs = econ.events()
    for e in evs:
        print(f"{e['t']:%a %d %H:%M}  {e['name']}")
    sc.render(econ.week_page(evs), os.path.join(OUT, rid + "-week.jpg"))
    return "done"


def do_fact(st, now, rid, publish):
    """16:07 rotating Story: did-you-know fact → glossary term → number of the day."""
    from . import story_cards as sc
    today = now.strftime("%Y-%m-%d")
    d = st.setdefault("daily_fact", {"n": 0, "last": "", "fact": 0, "term": 0, "num": 0})
    if publish and d.get("last") == today:
        summary("ℹ️ daily fact already published"); return "skipped"
    F = sc.facts()
    kind = ("fact", "term", "num")[d["n"] % 3]
    if kind == "fact" and d["fact"] >= len(F["facts"]):
        kind = "num"
    if kind == "term" and d["term"] >= len(F["terms"]):
        kind = "num"
    if kind == "fact":
        page = sc.fact_page(F["facts"][d["fact"]])
    elif kind == "term":
        page = sc.term_page(F["terms"][d["term"]], d["term"] + 1, len(F["terms"]))
    else:
        page = sc.number_of_day(d["num"])
    img = sc.render(page, os.path.join(OUT, rid + ".jpg"))
    if not publish:
        summary(f"[dry-run] daily {kind}"); return "dry-run"
    _story_image(img, rid)
    d[kind] += 1; d["n"] += 1; d["last"] = today
    summary(f"✅ Daily {kind} Story"); return "published"


def do_report_dry(st, now, rid, publish):
    from . import report
    report.main(dry=True); return "done"


HANDLERS = {"fact": do_fact, "econ_dry": do_econ_dry, "monthly": do_monthly, "challenge": do_challenge, "alert": do_alert, "weekly": do_weekly, "report_dry": do_report_dry, "stories_pack": do_stories_pack, "music": do_music, "lesson": do_lesson, "news": do_news, "story": lambda s, n, r, p: do_story(s, n, r, p, False),
            "chart": lambda s, n, r, p: do_story(s, n, r, p, True), "quiz": do_quiz, "carousel": do_carousel, "analysis": do_analysis}


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
