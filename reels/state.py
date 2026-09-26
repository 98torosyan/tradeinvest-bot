import json
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
DEFAULT = {"course_index": 0, "lesson_index": 0, "palette": {"news": 0, "lesson": 0}, "music": {"news": 0, "lesson": 0, "story": 0}, "posted_links": []}


def load():
    try:
        with open(PATH, encoding="utf-8") as f:
            s = json.load(f)
    except (OSError, ValueError):
        s = {}
    out = json.loads(json.dumps(DEFAULT)); out.update(s)
    return out


def save(s):
    s["posted_links"] = s.get("posted_links", [])[-300:]
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
