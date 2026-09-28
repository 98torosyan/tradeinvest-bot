"""Music choice: module mood group first (file name prefix basics_/risk_/charts_/quiz_),
never the same track twice in a row, each track at most once a day when possible."""
import glob
import os

from . import settings

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "music")


def pick(kind, module, state, today):
    folder = "news" if kind in ("news", "story", "chart") else "lesson"
    files = sorted(glob.glob(os.path.join(DIR, folder, "*.mp3")) + glob.glob(os.path.join(DIR, folder, "*.wav")))
    if not files:
        return None
    group = "quiz" if kind == "quiz" else settings.MUSIC_GROUPS.get(module or 1, "basics")
    grouped = [f for f in files if os.path.basename(f).startswith(group + "_")]
    pool = grouped or files
    used = state.setdefault("music_used", {})
    used_today = used.get(today, [])
    last = state.get("last_track")
    cands = [f for f in pool if os.path.basename(f) not in used_today and os.path.basename(f) != last] or \
            [f for f in pool if os.path.basename(f) != last] or pool
    choice = cands[(len(used_today) + (module or 0)) % len(cands)]
    name = os.path.basename(choice)
    state["music_used"] = {today: used_today + [name]}
    state["last_track"] = name
    return choice
