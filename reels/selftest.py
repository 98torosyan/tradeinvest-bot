"""Canary run used by the installer BEFORE new code goes live: if anything here fails,
the installer stops and the previous version keeps running."""
import os
import sys

os.environ.setdefault("REEL_FPS", "4")
os.environ.pop("PEXELS_API_KEY", None)          # offline: gradient footage, no API calls
os.environ.pop("GEMINI_API_KEY", None)

from . import captions, curriculum, lesson_video, palettes, qa, quiz, render, site, state  # noqa: E402

OUT = "/tmp/selftest"


def main():
    os.makedirs(OUT, exist_ok=True)
    cur = curriculum.load()
    errs = curriculum.validate(cur)
    if errs:
        print("curriculum errors:", errs); return 1
    st = state.load()
    lesson = cur["lessons"][0]
    size = curriculum.module_size(cur, 1)
    res = lesson_video.render_lesson(lesson, {"module_size": size, "next_title": None},
                                     palettes.MODULE[5], f"{OUT}/t.mp4", f"{OUT}/t.jpg")
    if cur.get("series"):
        cap, _ = captions.hit_caption(lesson, f"📈 {lesson['series']} · {lesson['title']}", {})
    else:
        cap, _ = captions.lesson_caption(lesson, size, {})
    e, w = qa.post_render(lesson, res, cap)
    print("lesson:", round(res["duration"], 1), "s; qa errors:", e, "warnings:", w)
    if e:
        return 1
    # every scripted lesson: prerequisites, schema, banned phrases and SPELLING
    bad = [e for l in cur["lessons"] if l.get("status") == "script" for e in qa.pre_render(l, cur, set())]
    if bad:
        print("script problems:", bad[:10]); return 1
    # chart lesson overlay (Lightweight Charts) must lay out inside the safe area
    ch = next((l for l in cur["lessons"] if l.get("status") == "script" and any(b["kind"] == "chart" for b in l["beats"])), None)
    if ch:
        beats, total = lesson_video.plan(ch, None)
        html = lesson_video.overlay_html(ch, {"module_size": 30, "next_title": "x"}, palettes.MODULE[ch["module"]], beats, total)
        errs = qa.layout(html, [b["_t"] + b["_d"] * f for b in beats for f in (0.3, 0.8)])
        print("chart lesson layout:", errs or "ok")
        if errs:
            return 1
    render.render(quiz.html(lesson, palettes.MODULE[1]), f"{OUT}/q.mp4")
    # new tools: spelling, chart + math beats (layout), Manim, local image checks, LUT
    from . import spell, manim_scenes, media_checks, charts
    if not spell.available() or spell.unknown("Սա կարևոր դաս է") or not spell.unknown("շուկաիում"):
        print("spell-check is not working"); return 1
    chart_lesson = next(l for l in cur["lessons"] if any(b["kind"] == "chart" for b in l["beats"]) and any(b["kind"] == "math" for b in l["beats"]))
    beats, total = lesson_video.plan(chart_lesson, None)
    h = lesson_video.overlay_html(chart_lesson, {"module_size": 30, "next_title": "Resistance"}, palettes.MODULE[5], beats, total)
    lay = qa.layout(h, [b["_t"] + b["_d"] * 0.8 for b in beats])
    if lay:
        print("chart lesson layout:", lay[:3]); return 1
    if manim_scenes.available():
        manim_scenes.render("rr", palettes.MODULE[5], 3.0, 10, f"{OUT}/m.mov")
    else:
        print("manim missing"); return 1
    charts.ideal("support"); media_checks.lut_for(palettes.MODULE[5])
    site.build(cur, st, f"{OUT}/site")
    for f in ("t.mp4", "t.jpg", "q.mp4", "site/index.html"):
        if not os.path.getsize(f"{OUT}/{f}"):
            print("empty output", f); return 1
    print("selftest OK"); return 0


if __name__ == "__main__":
    sys.exit(main())
