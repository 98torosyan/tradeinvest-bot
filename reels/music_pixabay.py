"""Fill the mood music library from Pixabay Music (Pixabay Content License; tracks with YouTube Content ID are skipped).
Run in GitHub Actions (python -m reels.music_pixabay). Files: reels/assets/music/moods/<mood>/user_px-<slug>-<id>.mp3"""
import json
import os
import re
import sys
import urllib.parse

import requests

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "music", "moods")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
MOODS = {
    "tense":   ["dark trap", "suspense trailer", "tension cinematic"],
    "inspire": ["inspiring cinematic", "motivational epic", "emotional piano inspiring"],
    "tech":    ["tech house", "corporate technology", "minimal techno"],
    "energy":  ["phonk", "energetic sport", "future bass"],
    "calm":    ["lofi hip hop", "chill beat", "ambient piano"],
}
PER_MOOD = 7


def _items(q):
    s = requests.Session(); s.headers.update(UA)
    html = s.get(f"https://pixabay.com/music/search/{urllib.parse.quote(q)}/", timeout=30).text
    m = re.search(r"__BOOTSTRAP_URL__\s*=\s*['\"]([^'\"]+)", html)
    if not m:
        print("[px] no bootstrap for", q, len(html)); return []
    b = s.get(urllib.parse.urljoin("https://pixabay.com", m.group(1)), timeout=30).json()
    found = []

    def walk(o):
        if isinstance(o, list) and o and isinstance(o[0], dict) and o[0].get("mediaType") == "audio":
            found.extend(o); return
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(b)
    return found


def main():
    seen = set()
    for mood, qs in MOODS.items():
        d = os.path.join(ROOT, mood); os.makedirs(d, exist_ok=True)
        have = [f for f in os.listdir(d) if f.endswith(".mp3")]
        seen.update(re.findall(r"-(\d+)\.mp3$", " ".join(have)))
        need = PER_MOOD - len(have)
        if need <= 0:
            continue
        pool = []
        for q in qs:
            try:
                pool += _items(q)
            except Exception as exc:  # noqa: BLE001
                print("[px]", q, exc)
        pool = [o for o in pool if not o.get("hasYoutubeContentId") and (o.get("duration") or 0) >= 45 and str(o.get("id")) not in seen]
        pool.sort(key=lambda o: -(o.get("likeCount") or 0))
        for o in pool:
            if need <= 0:
                break
            if str(o["id"]) in seen:
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", (o.get("name") or "track").lower()).strip("-")[:40]
            out = os.path.join(d, f"user_px-{slug}-{o['id']}.mp3")
            try:
                r = requests.get(o["sources"]["src"], headers={**UA, "Referer": "https://pixabay.com/"}, timeout=60)
                r.raise_for_status()
                open(out, "wb").write(r.content)
                seen.add(str(o["id"])); need -= 1
                print(f"[px] {mood}: {o.get('name')} ({o.get('likeCount')} likes)")
            except Exception as exc:  # noqa: BLE001
                print("[px] download", o.get("name"), exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
