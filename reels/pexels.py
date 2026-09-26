"""Free cinematic background clips from Pexels (free for commercial use,
no attribution required). Needs PEXELS_API_KEY; without it nothing happens."""
import os
import subprocess
import tempfile

import requests

API = "https://api.pexels.com/videos/search"
FALLBACK_QUERIES = ["city skyline night", "abstract blue technology", "stock market screen", "server room lights"]
NOTES = []


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
        if files:
            best = min(files, key=lambda f: abs((f.get("width") or 0) - 1080))
            out.append((v["id"], best["link"]))
    return out


def fetch(query, used_ids):
    """Returns (path, video_id) or (None, None). Never raises."""
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        return None, None
    for q in [query] + FALLBACK_QUERIES:
        if not q:
            continue
        try:
            cands = [c for c in _candidates(q, key) if c[0] not in used_ids]
        except Exception as exc:  # noqa: BLE001
            note(f"[pexels] search '{q}' failed: {str(exc)[:120]}"); continue
        for vid, link in cands[:3]:
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
                    note(f"[pexels] using video {vid} for '{q}'")
                    return path, vid
            except Exception as exc:  # noqa: BLE001
                note(f"[pexels] download {vid} failed: {str(exc)[:120]}")
    note("[pexels] no usable clip, rendering without background video")
    return None, None
