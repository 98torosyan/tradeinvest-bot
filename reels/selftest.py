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
    res = lesson_video.render_lesson(lesson, {"module_size": size, "next_title": cur["lessons"][1]["title"]},
                                     palettes.MODULE[1], f"{OUT}/t.mp4", f"{OUT}/t.jpg")
    cap, _ = captions.lesson_caption(lesson, size, {})
    e, w = qa.post_render(lesson, res, cap)
    print("lesson:", round(res["duration"], 1), "s; qa errors:", e, "warnings:", w)
    if e:
        return 1
    render.render(quiz.html(lesson, palettes.MODULE[1]), f"{OUT}/q.mp4")
    site.build(cur, st, f"{OUT}/site")
    for f in ("t.mp4", "t.jpg", "q.mp4", "site/index.html"):
        if not os.path.getsize(f"{OUT}/{f}"):
            print("empty output", f); return 1
    print("selftest OK"); return 0


if __name__ == "__main__":
    sys.exit(main())
