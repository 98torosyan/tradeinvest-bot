import re
"""Free cinematic background clips from Pexels (free for commercial use,
no attribution required). Needs PEXELS_API_KEY; without it nothing happens."""
import os
import subprocess
import tempfile

import requests

API = "https://api.pexels.com/videos/search"
FALLBACK_QUERIES = ["city skyline night", "abstract blue light", "server room lights", "night highway timelapse"]
NOTES = []
BAD_WORDS = ("beer", "drink", "alcohol", "wine", "whisky", "cocktail", "bar-", "-bar", "pub", "party", "smok", "cigar",
             "vape", "kiss", "bikini", "lingerie", "gun", "weapon", "blood", "casino", "gambl", "poker", "church",
             "mosque", "flag", "protest", "police")


def note(msg):
    print(msg); NOTES.append(msg)


def _candidates(query, key):
    r = requests.get(API, headers={"Authorization": key}, timeout=20,
                     params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 15})
    r.raise_for_status()
    out = []
    for v in r.json().get("videos", []):
        if v.get("duration", 0) < 8:
            continue
        files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"
                 and (f.get("height") or 0) >= 1280 and (f.get("width") or 0) <= 1440 and (f.get("height") or 0) > (f.get("width") or 0)]
        slug = (v.get("url") or "").lower()
        if any(b in slug for b in BAD_WORDS):
            continue
        if files:
            best = min(files, key=lambda f: abs((f.get("width") or 0) - 1080))
            out.append((v["id"], best["link"], slug.replace("-", " ")))
    return out


def _pixabay_candidates(query, key):
    r = requests.get("https://pixabay.com/api/videos/", timeout=20,
                     params={"key": key, "q": query, "per_page": 20, "safesearch": "true", "video_type": "film"})
    r.raise_for_status()
    out = []
    for v in r.json().get("hits", []):
        tags = (v.get("tags") or "").lower()
        if v.get("duration", 0) < 8 or any(b.strip("-") in tags for b in BAD_WORDS):
            continue
        vids = v.get("videos") or {}
        for size in ("large", "medium"):
            f = vids.get(size) or {}
            if f.get("url") and (f.get("height") or 0) >= 720:
                out.append((f"pb{v['id']}", f["url"], tags)); break
    return out


SOURCE_TURN = [0]


def _sources():
    s = []
    if os.environ.get("PEXELS_API_KEY"):
        s.append(("pexels", lambda q: _candidates(q, os.environ["PEXELS_API_KEY"])))
    if os.environ.get("PIXABAY_API_KEY"):
        s.append(("pixabay", lambda q: _pixabay_candidates(q, os.environ["PIXABAY_API_KEY"])))
    return s                                        # Pexels first (more precise search), Pixabay second


STOP = {"close", "light", "lights", "night", "view", "background", "abstract", "with", "from", "into", "the", "and"}


def relevant(query, text):
    words = [w for w in re.findall(r"[a-z]+", (query or "").lower()) if len(w) > 3 and w not in STOP]
    if not words or not text:
        return True                     # nothing to compare (generic query or no description)
    t = text.lower()
    return any(w[:5] in t for w in words)       # prefix match: server/servers, market/markets


def fetch(query, used_ids, check=None):
    """Returns (path, clip_id) or (None, None). Never raises. Tries Pexels and Pixabay."""
    used_ids = {str(u) for u in used_ids}
    sources = _sources()
    if not sources:
        return None, None
    for q in [query] + FALLBACK_QUERIES:
        if not q:
            continue
        for name, search in sources:
            try:
                cands = [c for c in search(q) if str(c[0]) not in used_ids and (q != query or relevant(q, c[2]))]
            except Exception as exc:  # noqa: BLE001
                note(f"[{name}] search '{q}' failed: {str(exc)[:120]}"); continue
            for vid, link, _text in cands[:3]:
                path = os.path.join(tempfile.mkdtemp(prefix="bg_"), f"{vid}.mp4")
                try:
                    with requests.get(link, stream=True, timeout=60) as r:
                        r.raise_for_status()
                        size = 0
                        with open(path, "wb") as f:
                            for chunk in r.iter_content(1 << 20):
                                size += len(chunk)
                                if size > 80 << 20:
                                    raise RuntimeError("file too large")
                                f.write(chunk)
                    ok = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                         "stream=width,height", "-of", "csv=p=0", path], capture_output=True, text=True)
                    if ok.returncode == 0 and ok.stdout.strip():
                        if check is not None and not check(path):
                            note(f"[{name}] clip {vid} rejected by the content check"); continue
                        note(f"[{name}] using clip {vid} for '{q}'")
                        return path, vid
                except Exception as exc:  # noqa: BLE001
                    note(f"[{name}] download {vid} failed: {str(exc)[:120]}")
    note("[pexels] no usable clip, rendering without background video")
    return None, None
