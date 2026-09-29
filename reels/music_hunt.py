"""Semi-automatic music: every week the bot finds royalty-free tracks in current trending styles
(Openverse: CC0 / CC BY, commercial use allowed), checks tempo, energy and intro, and sends short
previews to Telegram with ✅ / ❌ buttons. Approved tracks are added automatically to the right library.
Profiles: lesson (soft, modern), news (energetic), story (bright, fast hook)."""
import json
import os
import re
import subprocess
import sys
import tempfile

import requests

from . import control

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC = os.path.join(ROOT, "reels", "assets", "music")
CREDITS = os.path.join(MUSIC, "credits.json")
API = "https://api.openverse.org/v1/audio/"
PROFILES = {
    "lesson": {"queries": ["lofi house", "chill deep house", "chillhop", "lofi beat", "ambient house", "soft afro house"],
               "bpm": (70, 118), "min_len": 75, "folder": "lesson", "per_week": 2},
    "news": {"queries": ["afro house", "tech house", "upbeat electronic", "energetic beat", "deep house groove"],
             "bpm": (110, 132), "min_len": 60, "folder": "news", "per_week": 2},
    "story": {"queries": ["upbeat funky", "electronic intro", "happy upbeat", "future bass"],
              "bpm": (98, 135), "min_len": 25, "folder": "story", "per_week": 1},
}
BAD_TAGS = ("vocal", "voice", "sing", "song", "rap", "lyric", "speech", "spoken", "choir", "podcast", "christmas",
            "church", "religious", "sad", "horror", "scary", "national anthem")


MIXKIT_GENRES = {
    "lesson": ["lo-fi-beats", "chillout", "deep-house", "tropical-house", "downtempo"],
    "news": ["house", "tech-house", "future-bass", "dance-pop", "hip-hop"],
    "story": ["future-bass", "electropop", "dance-pop", "trap"],
}
MIX_RE = re.compile(r"https://assets\.mixkit\.co/music/(?:preview/mixkit-[a-z0-9-]*?-)?(\d+)(?:/\1)?\.mp3")


def mixkit(profile, limit=12):
    """Tracks from Mixkit genre pages (Mixkit Free License: commercial use, no attribution)."""
    out, seen = [], set()
    for g in MIXKIT_GENRES[profile]:
        try:
            html = requests.get(f"https://mixkit.co/free-stock-music/{g}/", timeout=30,
                                headers={"User-Agent": "Mozilla/5.0 (TradeInvest bot)"}).text
        except Exception as exc:  # noqa: BLE001
            print("[mixkit]", g, exc); continue
        for m in MIX_RE.finditer(html):
            tid = m.group(1)
            if tid in seen:
                continue
            seen.add(tid)
            out.append({"id": f"mixkit-{tid}", "title": f"Mixkit {g} #{tid}", "creator": "Mixkit",
                        "license": "mixkit", "license_version": "", "license_url": "https://mixkit.co/license/",
                        "url": f"https://assets.mixkit.co/music/{tid}/{tid}.mp3", "tags": [{"name": g}]})
            if len(out) >= limit:
                return out
    print(f"[mixkit] {profile}: {len(out)} tracks found")
    return out


def search(query, page_size=20):
    r = requests.get(API, timeout=30, headers={"User-Agent": "TradeInvest-bot"},
                     params={"q": query, "license": "cc0,by", "license_type": "commercial", "page_size": page_size,
                             "length": "medium,long", "mature": "false"})
    r.raise_for_status()
    return r.json().get("results", [])


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "track").lower()).strip("-")[:40] or "track"


def analyse(path):
    """Tempo (BPM), loudness and whether the first 2 seconds already carry energy."""
    import numpy as np
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True, duration=150)
    dur = len(y) / sr
    tempo = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=sr)[0])[0])
    rms = librosa.feature.rms(y=y)[0]
    med = float(np.median(rms)) + 1e-9
    intro = float(np.mean(rms[: int(2 * sr / 512)])) / med
    return {"duration": dur, "bpm": tempo, "loud_db": 20 * float(np.log10(med)), "intro": intro}


def fits(profile, a):
    lo, hi = PROFILES[profile]["bpm"]
    bpm = a["bpm"]
    for b in (bpm, bpm * 2, bpm / 2):                  # librosa can report half/double time
        if lo <= b <= hi:
            a["bpm"] = b; break
    else:
        return False
    return a["duration"] >= PROFILES[profile]["min_len"] and a["intro"] >= 0.45


def _known():
    known = set()
    for p in (control.get("music_pending", {}) or {}).values():
        known.add(p["ov_id"])
    try:
        known |= set(json.load(open(CREDITS, encoding="utf-8")).get("_rejected", []))
        known |= {v.get("ov_id") for v in json.load(open(CREDITS, encoding="utf-8")).values() if isinstance(v, dict)}
    except (OSError, ValueError):
        pass
    return known


def tg(method, **kw):
    sys.path.insert(0, ROOT)
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    kw.setdefault("chat_id", TELEGRAM_CHAT_ID)
    files = kw.pop("files", None)
    return requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}", data=kw, files=files, timeout=60).json()


def hunt():
    """Weekly: finds candidates and sends previews. Returns number of previews sent."""
    pending = control.get("music_pending", {}) or {}
    known = _known()
    sent = 0
    for prof, cfg in PROFILES.items():
        got = 0
        own = len([f for f in os.listdir(os.path.join(MUSIC, cfg["folder"]))]) if os.path.isdir(os.path.join(MUSIC, cfg["folder"])) else 0
        want = cfg["per_week"] + (3 if own < 6 else 0)          # first weeks: build the library faster
        batches = [("mixkit", lambda: mixkit(prof))] + [(q, (lambda q=q: search(q))) for q in cfg["queries"]]
        for q, fetch in batches:
            if got >= want:
                break
            try:
                results = fetch()
            except Exception as exc:  # noqa: BLE001
                print("[music] search failed:", exc); continue
            for r in results:
                if got >= want:
                    break
                tags = " ".join([t.get("name", "") for t in r.get("tags") or []] + [r.get("title") or ""]).lower()
                if r["id"] in known or any(b in tags for b in BAD_TAGS) or not r.get("url"):
                    continue
                work = tempfile.mkdtemp(prefix="mh_")
                src = os.path.join(work, "full")
                try:
                    with requests.get(r["url"], timeout=90, stream=True) as resp:
                        resp.raise_for_status()
                        with open(src, "wb") as f:
                            for chunk in resp.iter_content(1 << 20):
                                f.write(chunk)
                    wav = os.path.join(work, "a.wav")
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-t", "150", "-ac", "1", wav], check=True)
                    a = analyse(wav)
                except Exception as exc:  # noqa: BLE001
                    print("[music] skip", r.get("title"), exc); known.add(r["id"]); continue
                known.add(r["id"])
                if not fits(prof, a):
                    continue
                prev = os.path.join(work, "preview.mp3")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0", "-i", src, "-t", "15", "-af",
                                "afade=t=out:st=13:d=2", "-b:a", "128k", prev], check=True)
                key = f"{prof}-{len(pending) + 1}-{r['id'][:6]}"
                credit = f"{r.get('title') or 'Untitled'} — {r.get('creator') or 'unknown'} ({(r.get('license') or '').upper()} {r.get('license_version') or ''})".strip()
                kb = {"inline_keyboard": [[{"text": "✅ Հաստատել", "callback_data": f"m:ok:{key}"},
                                           {"text": "❌ Մերժել", "callback_data": f"m:no:{key}"}]]}
                label = {"lesson": "🎓 Դասերի համար", "news": "📰 Լուրերի համար", "story": "📱 Story-ների համար"}[prof]
                cap = (f"{label}\n🎵 {credit}\nՏեմպ՝ {a['bpm']:.0f} BPM · տևողություն՝ {a['duration']:.0f} վրկ\n"
                       f"Նմուշը՝ առաջին 15 վայրկյանը")
                res = tg("sendAudio", caption=cap, reply_markup=json.dumps(kb), title=(r.get("title") or "track")[:60],
                         files={"audio": open(prev, "rb")})
                if res.get("ok"):
                    pending[key] = {"ov_id": r["id"], "profile": prof, "url": r["url"], "title": r.get("title"),
                                    "creator": r.get("creator"), "license": r.get("license"),
                                    "license_version": r.get("license_version"), "license_url": r.get("license_url"),
                                    "credit": credit, "status": "pending"}
                    got += 1; sent += 1
    control.put("music_pending", pending)
    rejected = sorted(known - {p["ov_id"] for p in pending.values()})
    try:
        cr = json.load(open(CREDITS, encoding="utf-8"))
    except (OSError, ValueError):
        cr = {}
    cr["_rejected"] = sorted(set(cr.get("_rejected", [])) | set(rejected))[-2000:]
    json.dump(cr, open(CREDITS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not sent:
        tg("sendMessage", text="🎵 Այս շաբաթ համապատասխան նոր trek չգտնվեց։ Կփորձեմ հաջորդ շաբաթ։")
    return sent


def on_callback(cq):
    """Called by the community job for a ✅/❌ button press. Only marks the choice (no ffmpeg there)."""
    data = cq.get("data", "")
    if not data.startswith("m:"):
        return False
    _, act, key = data.split(":", 2)
    pending = control.get("music_pending", {}) or {}
    item = pending.get(key)
    if not item or item["status"] != "pending":
        tg("answerCallbackQuery", callback_query_id=cq["id"], text="Արդեն մշակված է")
        return True
    item["status"] = "approved" if act == "ok" else "rejected"
    control.put("music_pending", pending)
    tg("answerCallbackQuery", callback_query_id=cq["id"], text="✅ Կավելացվի գրադարան" if act == "ok" else "❌ Մերժված է")
    return True


def install_approved():
    """Called at the start of a reels run (ffmpeg available): downloads approved tracks, normalises them
    (loudness, 150 s max, fades) and adds them to the right folder with their credit."""
    pending = control.get("music_pending", {}) or {}
    done = []
    try:
        cr = json.load(open(CREDITS, encoding="utf-8"))
    except (OSError, ValueError):
        cr = {}
    for key, item in list(pending.items()):
        if item["status"] == "rejected":
            cr.setdefault("_rejected", []).append(item["ov_id"]); pending.pop(key); continue
        if item["status"] != "approved":
            continue
        folder = os.path.join(MUSIC, PROFILES[item["profile"]]["folder"])
        os.makedirs(folder, exist_ok=True)
        name = f"{item['profile']}_{_slug(item['title'])}.mp3"
        out = os.path.join(folder, name)
        try:
            tmp = tempfile.mktemp(suffix=".src")
            with requests.get(item["url"], timeout=120, stream=True) as resp:
                resp.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in resp.iter_content(1 << 20):
                        f.write(chunk)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-t", "150", "-af",
                            "afade=t=in:st=0:d=0.3,loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st=146:d=4",
                            "-ac", "2", "-ar", "44100", "-b:a", "192k", out], check=True)
            cr[name] = {k: item.get(k) for k in ("ov_id", "profile", "title", "creator", "license", "license_version",
                                                 "license_url", "credit")}
            done.append(name); pending.pop(key)
        except Exception as exc:  # noqa: BLE001
            print("[music] install failed:", exc)
    json.dump(cr, open(CREDITS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    control.put("music_pending", pending)
    return done


def credit_for(track_path):
    """Caption line for tracks that need attribution (CC BY). CC0 and our own tracks need none."""
    try:
        c = json.load(open(CREDITS, encoding="utf-8")).get(os.path.basename(track_path or ""))
    except (OSError, ValueError):
        return ""
    if c and (c.get("license") or "").lower() not in ("cc0", "mixkit"):
        return f"🎵 {c['credit']}"
    return ""
