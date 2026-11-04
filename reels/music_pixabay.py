"""Fill the mood music library from Pixabay Music (no YouTube Content ID) and Mixkit (Mixkit Stock Music Free License).
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


MIXKIT = {
    "tense":   ["mood/tension", "mood/suspenseful", "mood/dark"],
    "inspire": ["mood/inspiring", "mood/uplifting", "mood/hopeful"],
    "tech":    ["techno", "house", "mood/serious"],
    "energy":  ["mood/energetic", "hip-hop", "mood/powerful"],
    "calm":    ["mood/chill", "mood/calm", "mood/relaxing"],
}


def _mixkit(path):
    html = requests.get(f"https://mixkit.co/free-stock-music/{path}/", headers=UA, timeout=30).text
    urls = []
    for u in re.findall(r"https://assets\.mixkit\.co/music/[^\"'\s]+?\.mp3", html):
        if u not in urls:
            urls.append(u)
    print(f"[mk] {path}: {len(urls)} tracks, html {len(html)}")
    return urls


def mixkit_fill():
    for mood, paths in MIXKIT.items():
        d = os.path.join(ROOT, mood); os.makedirs(d, exist_ok=True)
        have = {f for f in os.listdir(d) if f.endswith(".mp3")}
        need = PER_MOOD - len(have)
        for p in paths:
            if need <= 0:
                break
            try:
                urls = _mixkit(p)
            except Exception as exc:  # noqa: BLE001
                print("[mk]", p, exc); continue
            for u in urls:
                if need <= 0:
                    break
                tid = re.findall(r"(\d+)", u.rsplit("/", 1)[-1]) or ["x"]
                out = os.path.join(d, f"user_mk-{p.replace('/', '-')}-{tid[0]}.mp3")
                if os.path.basename(out) in have or any(f.endswith(f"-{tid[0]}.mp3") for f in have):
                    continue
                try:
                    r = requests.get(u, headers=UA, timeout=60); r.raise_for_status()
                    if len(r.content) < 300_000:          # skip short stingers
                        continue
                    open(out, "wb").write(r.content); have.add(os.path.basename(out)); need -= 1
                    print(f"[mk] {mood}: {u} ({len(r.content) // 1024} KB)")
                except Exception as exc:  # noqa: BLE001
                    print("[mk] download", u, exc)


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
    mixkit_fill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
