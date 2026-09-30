"""Music choice.
- Only the owner's tracks (sent to the Telegram bot, file names start with user_) are used once they exist;
  older library tracks are a fallback so nothing ever breaks.
- Shuffle bag: every track is used once before any track repeats, never twice in a row.
- Every use starts at a DIFFERENT energetic section of the track, so the same song sounds different each time."""
import glob
import os
import random
import subprocess
import tempfile

from . import settings

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "music")
FOLDER = {"news": "news", "story": "story", "chart": "story", "quiz": "story"}


def _files(folder):
    return sorted(glob.glob(os.path.join(DIR, folder, "*.mp3")) + glob.glob(os.path.join(DIR, folder, "*.wav")))


def library(kind):
    folder = FOLDER.get(kind, "lesson")
    files = _files(folder)
    if not files and folder == "story":
        files = _files("news")
    own = [f for f in files if os.path.basename(f).startswith(settings.USER_TRACK_PREFIX)]
    return own or files


def sections(path, need=70):
    """Start times (s) of energetic parts of a track, at least 12 s apart, leaving `need` seconds to play."""
    try:
        import numpy as np
        import librosa
        y, sr = librosa.load(path, sr=11025, mono=True)
        dur = len(y) / sr
        if dur <= need + 5:
            return [0.0]
        rms = librosa.feature.rms(y=y, frame_length=11025, hop_length=11025)[0]      # 1 value per second
        thr = float(np.percentile(rms, 45))
        starts = [float(t) for t in range(0, int(dur - need)) if rms[t:t + 4].mean() >= thr]
        out = []
        for t in starts:
            if not out or t - out[-1] >= 12:
                out.append(t)
        return out or [0.0]
    except Exception as exc:  # noqa: BLE001
        print("[music] sections:", exc)
        return [0.0]


def pick(kind, module, state, today, need=70):
    """Returns a path to a (trimmed) audio file ready to be mixed, or None."""
    files = library(kind)
    if not files:
        return None
    key = FOLDER.get(kind, "lesson")
    bags = state.setdefault("music_bag", {})
    bag = [b for b in bags.get(key, []) if b in map(os.path.basename, files)]
    last = state.setdefault("music_last", {}).get(key)
    if not bag:                                     # new round: shuffle all tracks, never start with the last one
        bag = [os.path.basename(f) for f in files]
        random.shuffle(bag)
        if len(bag) > 1 and bag[0] == last:
            bag.append(bag.pop(0))
    name = bag.pop(0)
    bags[key] = bag
    state["music_last"][key] = name
    path = os.path.join(os.path.dirname(files[0]), name)
    # a different section each time this track is used
    secs = state.setdefault("music_sections", {})
    if name not in secs:
        secs[name] = sections(path, need)
    uses = state.setdefault("music_uses", {})
    k = uses.get(name, 0); uses[name] = k + 1
    start = secs[name][(k * 3 + (module or 0)) % len(secs[name])]
    if start <= 0.5:
        return path
    out = os.path.join(tempfile.mkdtemp(prefix="mus_"), name.rsplit(".", 1)[0] + ".mp3")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.1f}", "-i", path, "-t", str(need + 30),
                        "-af", "afade=t=in:st=0:d=0.8", "-b:a", "192k", out])
    return out if r.returncode == 0 else path
