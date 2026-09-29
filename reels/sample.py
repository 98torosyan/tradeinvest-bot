"""Renders the M5-11 'Support' lesson (all v1.1 features) at full quality to the media branch
as samples/M5-11.mp4 -- NOT published to Instagram. Used once by the installer as a preview."""
import os
import sys

from . import curriculum, hosting, lesson_video, music, palettes, state


def main():
    cur = curriculum.load()
    i = next(k for k, l in enumerate(cur["lessons"]) if l["id"] == "M5-11")
    l, nxt = cur["lessons"][i], cur["lessons"][i + 1]
    out = "/tmp/sample_v11"; os.makedirs(out, exist_ok=True)
    st = state.load()
    track = music.pick("lesson", 5, {}, "sample")
    res = lesson_video.render_lesson(l, {"module_size": curriculum.module_size(cur, 5), "next_title": nxt["title"]},
                                     palettes.MODULE[5], f"{out}/M5-11.mp4", f"{out}/M5-11.jpg", music=track,
                                     used_ids=st.get("used_broll", []), clip_cache={})
    urls = hosting.publish([(f"{out}/M5-11.mp4", "samples/M5-11.mp4"), (f"{out}/M5-11.jpg", "samples/M5-11.jpg")])
    print("sample:", urls, "duration", round(res["duration"], 1), "charts:", res.get("chart_sources"))


if __name__ == "__main__":
    sys.exit(main())
