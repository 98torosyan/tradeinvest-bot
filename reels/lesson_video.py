"""TradeInvest v1.0 lesson Reel: beat-synced hybrid of real B-roll, motion-graphic
cards and kinetic captions. No voice. Hook visible on the very first frame."""
import os
import shutil
import subprocess
import tempfile

import numpy as np

from . import pexels, settings
from .broll import (_load, _probe_dur, _segment, chunks, mix_audio, word_times, SR)
from .builder import ASSETS, esc, logo_svg
from .palettes import css_vars

FPS = int(os.environ.get("REEL_FPS", "30"))
OUTRO = 3.4
LOOP = 0.45              # seconds at the very end that fade back into the hook frame
GRAPHIC = {"hero", "card", "compare", "checklist", "chart", "math", "stat", "myth", "quiz", "steps", "bars"}


# ---------------- music beat grid (numpy only) ----------------
def beat_grid_librosa(music, seconds=120):
    """Runs the librosa beat tracker in a child process: a crash in native code (numba) can then never
    take the whole publishing run down -- we simply fall back to the numpy beat grid."""
    import json as _j
    import sys as _sys
    code = ("import json,sys;sys.path.insert(0,sys.argv[2]);from reels.lesson_video import _beat_grid_librosa as f;"
            "r=f(sys.argv[1]);print(json.dumps(None if r is None else [list(map(float,r[0])),list(map(float,r[1]))]))")
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        r = subprocess.run([_sys.executable, "-c", code, music, root], capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            print("[librosa] beat tracker failed (code", r.returncode, "), using the numpy grid")
            return None
        out = _j.loads(r.stdout.strip().splitlines()[-1])
        return (out[0], out[1]) if out else None
    except Exception as exc:  # noqa: BLE001
        print("[librosa]", exc); return None


def _beat_grid_librosa(music, seconds=120):
    """(beat_times, downbeat_times) aligned to the music start, via librosa; None if unavailable."""
    try:
        import librosa
        y, sr = librosa.load(music, sr=22050, mono=True, duration=seconds)
        env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, beats = librosa.beat.beat_track(onset_envelope=env, sr=sr, units="frames", start_bpm=100)
        if len(beats) < 8:
            return None
        times = librosa.frames_to_time(beats, sr=sr)
        strength = env[beats]
        phase = max(range(4), key=lambda p: strength[p::4].sum())           # bar phase = strongest of 4
        return list(times), list(times[phase::4])
    except Exception as exc:  # noqa: BLE001
        print("[librosa]", exc); return None


def beat_grid(music, seconds=120):
    """Returns (offset, period): first strong beat and beat period in seconds, or None."""
    try:
        a = _load(music)[: int(seconds * SR)].mean(axis=1)
    except Exception:  # noqa: BLE001
        return None
    hop = 512
    frames = len(a) // hop
    if frames < 200:
        return None
    e = np.sqrt(np.add.reduceat(a[: frames * hop] ** 2, np.arange(0, frames * hop, hop)))
    onset = np.maximum(0, np.diff(e, prepend=e[0]))
    onset = onset - onset.mean()
    fps = SR / hop
    ac = np.correlate(onset, onset, "full")[len(onset) - 1:]
    lo, hi = int(fps * 60 / 140), int(fps * 60 / 75)            # 75-140 BPM
    lag = lo + int(np.argmax(ac[lo:hi]))
    period = lag / fps
    phases = [onset[p::lag].sum() for p in range(lag)]
    offset = int(np.argmax(phases)) / fps
    return offset, period


def snap(times, grid, tol=0.28):
    """Moves each cut to a strong beat (downbeat) if one is near, else to the nearest beat."""
    if not grid:
        return times, set()
    if isinstance(grid, dict):                        # librosa: explicit beat and downbeat lists
        beats, downs = grid["beats"], grid["downs"]
    else:                                             # numpy fallback: regular grid
        off, per = grid
        beats = [k * per for k in range(0, 400)]; downs = beats[::4]
    out, strong = [], set()
    for t in times:
        d = min(downs, key=lambda x: abs(x - t)) if downs else None
        if d is not None and abs(d - t) <= tol + 0.12:
            out.append(d); strong.add(len(out) - 1); continue
        b = min(beats, key=lambda x: abs(x - t))
        out.append(b if abs(b - t) <= tol else t)
    return out, strong


# ---------------- timing ----------------
def _nwords(*parts):
    return sum(len(str(p).replace("|", " ").split()) for p in parts)


def beat_len(b):
    k, W = b["kind"], settings.WORD_SEC
    if k == "hero":
        return max(3.2, 1.4 + 0.7 * len(b["text"].split("|")) + 0.15 * _nwords(b["text"]))
    if k == "card":
        return min(7.0, max(3.5, 1.8 + 0.62 * _nwords(b["title"], b["text"])))
    if k == "compare":
        return min(8.0, max(4.5, 2.2 + 0.55 * _nwords(*b["a"], *b["b"])))
    if k == "checklist":
        return min(9.0, max(4.5, 1.6 + 1.3 * len(b["items"]) + 0.2 * _nwords(*b["items"])))
    if k == "chart":
        return min(10.0, max(6.0, 3.4 + 0.55 * _nwords(b.get("title", ""), b.get("text", ""))))
    if k == "stat":
        return min(7.0, max(4.6, 2.6 + 0.55 * _nwords(b.get("label", ""), b.get("sub", ""))))
    if k == "myth":
        return min(11.0, max(6.0, 2.2 + 0.32 * _nwords(b["myth"]) + 0.62 * _nwords(b["truth"])))
    if k == "quiz":
        t_opts = 0.7 + 0.3 * _nwords(b["q"])
        return min(14.0, t_opts + 0.55 * len(b["options"]) + 0.3 + 3 + 1.8 + 0.12 * _nwords(*b["options"]))
    if k == "steps":
        return min(10.0, max(4.8, 1.6 + 1.1 * len(b["items"]) + 0.22 * _nwords(*b["items"])))
    if k == "bars":
        return min(9.0, max(4.8, 2.4 + 0.8 * len(b["items"]) + 0.15 * _nwords(*[x[0] for x in b["items"]])))
    if k == "math":
        return min(10.0, max(5.5, 3.2 + 0.55 * _nwords(b.get("text", ""))))
    words = b["text"].split()
    need = sum(max(settings.CHUNK_MIN, len(c) * W) for c in chunks(words)) + 0.6     # every chunk readable
    return min(12.0, max(2.6, need))


def plan(lesson, grid):
    beats = [{"kind": "hero", "text": lesson["hook"], "first": True}] + [dict(b) for b in lesson["beats"]] + \
            [{"kind": "hero", "text": lesson["recap"], "query": lesson.get("recap_query", "abstract light bokeh")}]
    cuts, t = [], 0.0
    for b in beats:
        t += beat_len(b); cuts.append(t)
    cuts, strong = snap(cuts, grid)
    start = 0.0
    for i, (b, c) in enumerate(zip(beats, cuts)):
        b["_t"], b["_d"] = start, max(1.6, c - start); start = b["_t"] + b["_d"]
        # a soft transition INTO the next beat when the cut sits on a downbeat (not after the hook)
        b["_xfade_out"] = i in strong and 0 < i < len(beats) - 1
    return beats, start + OUTRO


# ---------------- footage ----------------
CHECK_LIMIT = 4           # Gemini second-opinion checks per video (local checks are unlimited)


def _clip_ok(negative, cache=None):
    from . import gemini
    cache = {} if cache is None else cache
    budget = [CHECK_LIMIT]

    def check(path):
        key = os.path.basename(path)
        if key in cache:
            return cache[key] and not (negative and cache.get(key + ":face"))
        budget[0] -= 1
        frame = path + ".jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.5", "-i", path, "-frames:v", "1", frame])
        if not os.path.exists(frame):
            return False
        from . import media_checks
        local = media_checks.local_flags(frame)
        if local is not None:
            if local["text"] or (negative and local["face"]):
                cache[key] = False; cache[key + ":face"] = local["face"]; return False
        flags = gemini.frame_flags(frame) if budget[0] > 0 else None      # second opinion: logos
        if flags is None:                  # no second opinion: trust local checks, never risk faces in negative ones
            if local is not None:
                cache[key] = True; cache[key + ":face"] = local["face"]
                return not (negative and local["face"])
            return not negative
        cache[key] = not (flags["text"] or flags["logo"]); cache[key + ":face"] = flags["face"]
        if flags["text"] or flags["logo"]:
            return False
        return not (negative and flags["face"])
    return check


XFADES = ["smoothleft", "smoothup", "zoomin", "hblur", "circleopen", "fadefast"]
XF = 0.35


def _segment_v2(src, start, dur, out, i, palette, cx=0.5):
    """One beat of footage: subject-aware 9:16 crop, slow push-in/pull-out, module colour grade (LUT)."""
    from . import media_checks
    frames = max(1, int(round(dur * FPS)))
    z = f"1+0.08*on/{frames}" if i % 2 == 0 else f"1.08-0.08*on/{frames}"
    lut = media_checks.lut_for(palette)
    tail = (f"fps={FPS},zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={FPS},"
            f"lut3d='{lut}',eq=contrast=1.04:brightness=-0.02,vignette=PI/5")
    if src:
        w, h = [int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                "stream=width,height", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip().split(",")[:2]]
        if w / max(h, 1) > 9 / 16:
            crop = f"scale=-2:1920,crop=1080:1920:x='(iw-1080)*{cx:.3f}':y=0,"
        else:
            crop = "scale=1080:-2,crop=1080:1920:x=0:y='(ih-1920)/2',"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-i", src, "-t", f"{dur:.3f}",
                        "-vf", crop + tail, "-an", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-pix_fmt", "yuv420p", out], check=True)
    else:
        tint = palette["bg"].split("#", 1)[1][:6]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"gradients=s=1080x1920:d={dur:.3f}:speed=0.015:c0=0x{tint}:c1=0x1a2a44:c2=0x0b1220:r={FPS}",
                        "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out],
                       check=True)


def build_footage(beats, total, work, used_ids, palette, negative, cache=None):
    from . import media_checks
    segs, used, last = [], [], None
    check = _clip_ok(negative, cache)
    for i, b in enumerate(beats):
        extra = (XF if b.get("_xfade_out") else 0.04) if i < len(beats) - 1 else 0.0   # overlap used by the transition
        d = b["_d"] + extra
        path, vid = pexels.fetch(b.get("query", ""), set(map(str, used_ids)) | set(map(str, used)), check=check)
        if vid:
            used.append(vid); last = path
        src = path or last
        start, cx = 0.0, 0.5
        if src:
            dur = _probe_dur(src)
            if dur and dur < d + 0.2:
                looped = os.path.join(work, f"loop{i}.mp4")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "3", "-i", src, "-t", f"{d + 1:.2f}",
                                "-an", "-c:v", "libx264", "-preset", "veryfast", looped], check=True)
                src, dur = looped, d + 1
            start = media_checks.clean_start(src, d, dur)
            frame = os.path.join(work, f"sc{i}.jpg")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start + d / 2:.2f}", "-i", src, "-frames:v", "1", frame])
            cx = media_checks.smart_x(frame) if os.path.exists(frame) else 0.5
        seg = os.path.join(work, f"seg{i:02d}.mp4")
        _segment_v2(src, start, d, seg, i, palette, cx)
        segs.append((seg, b))
    # chain: hard cuts by default, xfade on downbeats. Offsets come from the REAL segment lengths
    # (frame-rounded), so every transition starts inside its first input.
    inputs, filters, label = [], [], "[0:v]"
    for seg, _ in segs:
        inputs += ["-i", seg]
    out_len = _probe_dur(segs[0][0])
    for k in range(1, len(segs)):
        prev_b = segs[k - 1][1]
        tr, dur = (XFADES[k % len(XFADES)], XF) if prev_b.get("_xfade_out") else ("fade", 0.04)
        offset = max(0.0, out_len - dur - 1.5 / FPS)        # keep the whole transition inside input 1
        out = f"[v{k}]"
        filters.append(f"{label}[{k}:v]xfade=transition={tr}:duration={dur}:offset={offset:.3f}{out}")
        out_len = offset + _probe_dur(segs[k][0])
        label = out
    foot = os.path.join(work, "footage.mp4")
    fc = ";".join(filters) + (";" if filters else "") + f"{label}tpad=stop_mode=clone:stop_duration={OUTRO + 1}[vout]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fc, "-map", "[vout]",
                    "-t", f"{total:.2f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                    "-pix_fmt", "yuv420p", foot], check=True)
    return foot, used


# ---------------- overlay (captions + motion graphics) ----------------
def _fit(text, base, width=900, k=0.64):
    """Font size so that the longest word/line fits the safe width (Armenian glyphs are wide)."""
    longest = max(len(text), 1)
    return int(min(base, width / (longest * k)))


def _hero(b, mode="slam"):
    parts = b["text"].split("|")
    html = ""
    for i, p in enumerate(parts):
        last = i == len(parts) - 1 and len(parts) > 1
        k = 0.92
        size = _fit(max(p.split(), key=len) if len(p) > 14 else p, 150 if last else 128, width=880, k=k)
        style = f' style="font-size:{size}px"'
        if b.get("first") and i == 0:
            html += f'<div class="hl"{style}>{esc(p)}</div>'                      # visible on frame 0 (hook)
            continue
        at = (0.55 + 0.8 if b.get("first") else 0.2) + i * 0.62   # first scene starts 0.8 s "early" (hook on frame 0)
        if mode == "mask":
            html += f'<div class="hl mk" data-fx="mask" data-at="{at:.2f}" data-dur=".7"{style}><span>{esc(p)}</span></div>'
        elif mode == "type":
            html += f'<div class="hl" data-fx="type" data-at="{at - .1:.2f}" data-dur="{max(.45, .045 * len(p)):.2f}"{style}>{esc(p)}</div>'
        elif mode == "chars":
            html += f'<div class="hl" data-fx="chars" data-at="{at:.2f}" data-dur=".6"{style}>{esc(p)}</div>'
        elif mode == "glow":
            html += f'<div class="hl" data-fx="glow" data-at="{at:.2f}" data-dur=".7"{style}>{esc(p)}</div>'
        else:
            html += f'<div class="hl" data-fx="slam" data-at="{at:.2f}" data-dur=".55"{style}>{esc(p)}</div>'
    return f'<div class="dim"></div><div class="hstack">{html}</div>'


def _captions(b):
    words = b["text"].split()
    chs = chunks(words)
    span = b["_d"] - 0.45
    need = [max(settings.CHUNK_MIN, len(c) * settings.WORD_SEC) for c in chs]
    scale = span / max(sum(need), 1e-6)
    wt, t = [], 0.15
    for c, n in zip(chs, need):                  # chunk time is shared by its words
        dur = n * scale
        wt += [(t + k * dur / len(c), t + (k + 1) * dur / len(c)) for k in range(len(c))]
        t += dur
    out, wi = "", 0
    for ch in chs:
        s0, s1 = wt[wi][0], wt[wi + len(ch) - 1][1]
        ws = "".join(f'<span class="w" data-s="{wt[wi + j][0]:.2f}" data-e="{wt[wi + j][1]:.2f}">{esc(w)}</span> '
                     for j, w in enumerate(ch))
        fs = _fit(max(ch, key=len), 92, width=800, k=0.86)
        out += f'<div class="chunk" style="font-size:{fs}px" data-s="{s0:.2f}" data-e="{s1:.2f}">{ws}</div>'
        wi += len(ch)
    return f'<div class="cap">{out}</div>'


def _price(o):
    up = o.get("dir", "up") == "up"
    pct = (o["to"] / o["from"] - 1) * 100
    return (f'<div class="ptag" data-fx="pop" data-at=".15" data-dur=".45"><span data-fx="count" data-at=".35" data-dur="1.2" '
            f'data-from="{o["from"]}" data-to="{o["to"]}" data-pre="$">{o["from"]}</span>'
            f'<b class="{"up" if up else "dn"}" data-fx="pop" data-at="1.5" data-dur=".45">{"▲" if up else "▼"} {abs(pct):.0f}%</b></div>')


ICON_WORDS = [("կանոն", "shield-check"), ("տնային", "school"), ("market cap", "chart-pie"), ("xau", "coins"),
              ("s&p", "building-skyscraper"), ("smart", "file-text"), ("usdt", "currency-dollar"), ("halving", "hourglass"),
              ("բլոկ", "link"), ("քանակ", "stack-2"), ("ռիսկ", "alert-triangle"), ("գին", "chart-line"),
              ("support", "chart-candle"), ("stop", "shield-lock"), ("շուկա", "world")]
ICON_DIR = os.path.join(ASSETS, "icons")
LOTTIE_DIR = os.path.join(ASSETS, "lottie")


def icon_for(b):
    name = b.get("icon")
    if not name:
        t = (b.get("title", "") + " " + b.get("text", "")).lower()
        name = next((ic for w, ic in ICON_WORDS if w in t), {"card": "bulb", "checklist": "list-check",
                                                              "compare": "arrows-exchange"}.get(b["kind"], "bulb"))
    return name


def _icon_html(name, at=0.05):
    lot = os.path.join(LOTTIE_DIR, name + ".json")
    if os.path.exists(lot):                      # an animated Lottie with the same name wins over the static icon
        data = open(lot, encoding="utf-8").read()
        return f'<div class="gicon lottie" data-lottie=\'{esc(data)}\'></div>'
    svg = os.path.join(ICON_DIR, name + ".svg")
    if not os.path.exists(svg):
        return ""
    body = open(svg, encoding="utf-8").read()
    body = body.replace('stroke="currentColor"', 'stroke="var(--a2)"').replace('width="24"', 'width="120"').replace('height="24"', 'height="120"')
    return f'<div class="gicon" data-fx="pop" data-at="{at:.2f}" data-dur=".5">{body}</div>'


CARD_FX = {"glass": "tilt", "editorial": "rise", "terminal": "rise", "neon": "pop", "paper": "pop"}


def _graphic(b, card="neon"):
    k = b["kind"]
    if k == "card":
        return (f'<div class="dim"></div><div class="gcard" data-fx="{CARD_FX.get(card, "pop")}" data-at=".15" data-dur=".55">{_icon_html(icon_for(b), .3)}'
                f'<div class="gt">{esc(b["title"])}</div><div class="gx" data-fx="rise" data-at=".55" data-dur=".6">{esc(b["text"])}</div></div>')
    if k == "chart":
        import json as _j
        from . import charts
        bars, levels, src = None, [], "ideal"
        if b.get("source") == "real":
            try:
                bars, levels, src = charts.real()
                levels = [l for l in levels if l["kind"] == b.get("level", "support")][:1] or levels[:1]
            except Exception as exc:  # noqa: BLE001
                print("[chart] real data unavailable, using the ideal shape:", str(exc)[:120])
        if bars is None:
            bars, levels, _ = charts.ideal(b.get("pattern", "support"))
            if b.get("source") == "real":
                src = "ideal-fallback"
        b["_chart_src"] = src
        data = _j.dumps({"bars": bars, "levels": levels})
        return (f'<div class="dim"></div><div class="ctitle" data-fx="rise" data-at=".1" data-dur=".5">{esc(b.get("title", ""))}</div>'
                f'<div class="lwc" data-chart=\'{esc(data)}\'></div>' + _captions(dict(b, _d=b["_d"])))
    if k == "math":
        return (f'<div class="dim"></div><div class="ctitle" data-fx="rise" data-at=".1" data-dur=".5">{esc(b.get("title", ""))}</div>'
                + _captions(dict(b, _d=b["_d"])))
    if k == "compare":
        a, c = b["a"], b["b"]
        lw = lambda t: max(str(t).split(), key=len)
        gt = min(_fit(lw(a[0]), 44, width=330, k=0.8), _fit(lw(c[0]), 44, width=330, k=0.8))   # both sides the same size
        gx = min(_fit(lw(a[1]), 48, width=330, k=0.8), _fit(lw(c[1]), 48, width=330, k=0.8))
        st = lambda n: f' style="font-size:{n}px"'
        return (f'<div class="dim"></div><div class="cmp">'
                f'<div class="side l" data-fx="rise" data-at=".2" data-dur=".6"><div class="gt"{st(gt)}>{esc(a[0])}</div><div class="gx"{st(gx)}>{esc(a[1])}</div></div>'
                f'<div class="vs" data-fx="pop" data-at=".7" data-dur=".5">VS</div>'
                f'<div class="side r" data-fx="rise" data-at="1.0" data-dur=".6"><div class="gt"{st(gt)}>{esc(c[0])}</div><div class="gx"{st(gx)}>{esc(c[1])}</div></div></div>')
    if k == "checklist":
        items = "".join(f'<div class="it" data-fx="rise" data-at="{0.6 + i * 1.0:.2f}" data-dur=".5"><i>✓</i>{esc(x)}</div>'
                        for i, x in enumerate(b["items"]))
        return (f'<div class="dim"></div><div class="chk"><div class="gt" data-fx="rise" data-at=".15" data-dur=".5">{esc(b["title"])}</div>'
                f'{items}</div>')
    if k == "stat":
        try:
            num = float(str(b["value"]).replace(",", ""))
        except ValueError:
            num = None
        dec = len(str(b["value"]).split(".")[1]) if "." in str(b["value"]) else 0
        val = (f'<div class="sv" data-fx="count" data-at=".25" data-dur="1.4" data-from="0" data-to="{num}" data-dec="{dec}" '
               f'data-grp="1" data-pre="{esc(b.get("pre", ""))}" data-post="{esc(b.get("post", ""))}">{esc(b.get("pre", ""))}0</div>'
               if num is not None else f'<div class="sv" data-fx="pop" data-at=".25" data-dur=".6">{esc(b["value"])}</div>')
        ring = ('<svg class="ring" viewBox="0 0 560 30"><path d="M10 15 H550" stroke="var(--a)" stroke-width="10" stroke-linecap="round" '
                'fill="none" data-fx="draw" data-at=".25" data-dur="1.4"/></svg>')
        sub = f'<div class="ss" data-fx="rise" data-at="1.9" data-dur=".6">{esc(b["sub"])}</div>' if b.get("sub") else ""
        shown = f'{b.get("pre", "")}{num:,.{dec}f}{b.get("post", "")}' if num is not None else str(b["value"])
        val = val.replace('<div class="sv"', f'<div class="sv" style="font-size:{_fit(shown, 250, width=880, k=0.62)}px"', 1)
        return (f'<div class="dim"></div><div class="stat">{val}{ring}'
                f'<div class="sl" data-fx="rise" data-at="1.3" data-dur=".6">{esc(b["label"])}</div>{sub}</div>')
    if k == "myth":
        t2 = 0.6 + 0.32 * _nwords(b["myth"])
        return (f'<div class="dim"></div><div class="myth" data-fx="tilt" data-at=".05" data-dur=".6">'
                f'<span class="tag m">ՄԻՖ</span><div class="mx"><span data-fx="strike" data-at="{t2:.2f}" data-dur=".6">{esc(b["myth"])}</span></div>'
                f'<div data-fx="flip" data-at="{t2 + .6:.2f}" data-dur=".6"><span class="tag t">ԻՐԱԿԱՆՈՒԹՅՈՒՆ</span>'
                f'<div class="tx">{esc(b["truth"])}</div></div></div>')
    if k == "quiz":
        t_opts = 0.7 + 0.3 * _nwords(b["q"])
        t_think = t_opts + 0.55 * len(b["options"]) + 0.3
        rows = ""
        for i, o in enumerate(b["options"]):
            cls = "ok" if i == b["a"] else "no"
            rows += (f'<div class="op" data-fx="rise" data-at="{t_opts + i * .55:.2f}" data-dur=".5">'
                     f'<b>{"ԱԲԳ"[i]}</b><span>{esc(o)}</span><i data-fx="state" data-cls="{cls}" data-at="{t_think + 3:.2f}"></i></div>')
        return (f'<div class="dim"></div><div class="quiz"><div class="qq" data-fx="rise" data-at=".15" data-dur=".5">{esc(b["q"])}</div>'
                f'{rows}<div class="timer" data-fx="shrink" data-at="{t_think:.2f}" data-dur="3"></div>'
                f'<div class="hint" data-fx="rise" data-at="{t_think:.2f}" data-dur=".4">Մտածիր 3 վայրկյան… գրիր comment-ում</div></div>')
    if k == "steps":
        items = "".join(f'<div class="st" data-fx="rise" data-at="{0.7 + i * 1.1:.2f}" data-dur=".5"><i>{i + 1}</i><span>{esc(x)}</span></div>'
                        for i, x in enumerate(b["items"]))
        return (f'<div class="dim"></div><div class="steps"><div class="gt" data-fx="rise" data-at=".15" data-dur=".5">{esc(b["title"])}</div>'
                f'<div class="rail" data-fx="scaley" data-at=".6" data-dur="{1.1 * len(b["items"]):.2f}"></div>{items}</div>')
    if k == "bars":
        mx = max(abs(float(v)) for _, v, _d, *r in b["items"]) or 1
        rows = ""
        for i, (lab, v, disp, *rest) in enumerate(b["items"]):
            bad = " bad" if rest and rest[0] == "bad" else ""
            at = 0.6 + i * 0.8
            rows += (f'<div class="br" data-fx="rise" data-at="{at:.2f}" data-dur=".45"><div class="bl"><span>{esc(lab)}</span><em>{esc(disp)}</em></div>'
                     f'<div class="bt"><div class="bf{bad}" data-fx="fill" data-w="{abs(float(v)) / mx:.3f}" data-at="{at + .2:.2f}" data-dur="1.0"></div></div></div>')
        return (f'<div class="dim"></div><div class="bars"><div class="gt" data-fx="rise" data-at=".15" data-dur=".5">{esc(b["title"])}</div>{rows}</div>')
    return ""


CHART_JS = r"""
(function(){const Ch=window.LightweightCharts;
document.querySelectorAll('.lwc').forEach(el=>{const d=JSON.parse(el.dataset.chart);const sc=el.closest('.scene');
 const cs=getComputedStyle(document.body);
 const chart=Ch.createChart(el,{width:980,height:820,localization:{locale:'en-US'},layout:{background:{type:'solid',color:'rgba(0,0,0,0)'},textColor:'#dfe6f2',fontSize:24,fontFamily:'ArmSans'},
  grid:{vertLines:{color:'rgba(255,255,255,.05)'},horzLines:{color:'rgba(255,255,255,.07)'}},rightPriceScale:{borderVisible:false,scaleMargins:{top:.12,bottom:.1}},
  timeScale:{visible:false,borderVisible:false},crosshair:{mode:2,vertLine:{visible:false},horzLine:{visible:false}},handleScroll:false,handleScale:false});
 const s=chart.addSeries(Ch.CandlestickSeries,{upColor:'#3DDC97',downColor:'#FF6B6B',wickUpColor:'#3DDC97',wickDownColor:'#FF6B6B',borderVisible:false,priceLineVisible:false,lastValueVisible:false});
 el._c={chart,s,d,n:-1,lines:[]};
 HOOKS.push(t=>{const a=+sc.dataset.in,b=+sc.dataset.out;if(t<a||t>=b)return;const l=t-a,span=(b-a)*.55;
  const n=Math.max(1,Math.ceil(clamp01((l-.3)/span)*d.bars.length));
  if(n!==el._c.n){s.setData(d.bars.slice(0,n));chart.timeScale().setVisibleLogicalRange({from:-1,to:d.bars.length});el._c.n=n;}
  d.levels.forEach((lv,i)=>{if(l>=.3+span+.2+i*.4&&!el._c.lines[i]){el._c.lines[i]=s.createPriceLine({price:lv.price,
   color:lv.kind==='support'?'#3DDC97':'#FF6B6B',lineWidth:4,lineStyle:2,axisLabelVisible:true,title:lv.label});}});});});
document.querySelectorAll('.lottie').forEach(el=>{const sc=el.closest('.scene');const anim=lottie.loadAnimation({container:el,renderer:'svg',loop:false,autoplay:false,animationData:JSON.parse(el.dataset.lottie)});
 HOOKS.push(t=>{const a=+sc.dataset.in;if(!anim.totalFrames)return;anim.goToAndStop(Math.min(anim.totalFrames-1,Math.max(0,(t-a-.2)*anim.frameRate)),true);});});
})();"""


def overlay_html(lesson, cur_info, palette, beats, total):
    from . import styles
    sname = lesson.get("style") or "marker"
    sty = styles.get(sname)
    scenes = []
    for i, b in enumerate(beats):
        a, d = b["_t"], b["_d"]
        a_in = -0.8 if i == 0 else a                     # first scene already fully visible at frame 0
        if b["kind"] == "hero":
            inner = _hero(b, sty["hero"]); cls = "hero"
            if i == 0 and not settings.SHOW_COURSE_LABEL:      # open loop: tells the viewer the payoff comes at the end
                inner += (f'<div class="wte" data-fx="rise" data-at="{0.8 + min(1.9, d - 1.4):.2f}" data-dur=".5">'
                          f'<span>Վերջում՝ ամենակարևորը</span><i></i></div>')
        elif b["kind"] == "broll":
            inner = (_price(b["overlay"]) if b.get("overlay") else "") + _captions(b); cls = "beat"
        else:
            inner = _graphic(b, sty["card"]); cls = "graphic beat" if b["kind"] in ("chart", "math") else "graphic"
        scenes.append(f'<section class="scene {cls}" data-in="{a_in:.2f}" data-out="{a + d:.2f}">{inner}</section>')
    oa = total - OUTRO
    nxt = cur_info.get("next_title") if settings.SHOW_COURSE_LABEL else None
    if not settings.SHOW_COURSE_LABEL:
        from .captions import OUTRO_CTA
        top, big = OUTRO_CTA.get(lesson.get("_cta"), ("Ամեն օր՝ նոր թրեյդինգ դաս", "Հետևիր @armtradeinvest"))
        scenes_cta = (f'<div class="nxt" data-fx="rise" data-at=".1" data-dur=".5">{esc(top)}</div>'
                      f'<div class="nxt2" data-fx="rise" data-at=".25" data-dur=".6">{esc(big)}</div>')
    else:
        scenes_cta = ""
    nxt_html = (f'<div class="nxt" data-fx="rise" data-at=".1" data-dur=".5">Հաջորդ դասը</div>'
                f'<div class="nxt2" data-fx="rise" data-at=".25" data-dur=".6">{esc(nxt)}</div>') if nxt else ""
    loop = not settings.SHOW_COURSE_LABEL           # last frames turn back into the first frame, so the replay is seamless
    scenes.append(f'<section class="scene outro" data-in="{oa:.2f}" data-out="{(total if loop else total + 1):.2f}"><div class="obg"></div>{nxt_html or scenes_cta}'
                  f'{logo_svg()}<div class="name" data-fx="rise" data-at="1.3" data-dur=".6">TradeInvest</div></section>')
    if loop:
        first = dict(beats[0], first=True)
        scenes.append(f'<section class="scene hero loopb" data-in="{total - LOOP:.2f}" data-out="{total + 1:.2f}">{_hero(first, sty["hero"])}</section>')
    css = "".join(open(os.path.join(ASSETS, f), encoding="utf-8").read() for f in ("broll.css", "lesson.css", "themes.css"))
    css = (f"@font-face{{font-family:'ArmCond';src:url('file://{ASSETS}/ttf/NotoSansArmenian.ttf');font-weight:100 900;font-stretch:62.5% 100%}}"
           + "".join(f"@font-face{{font-family:'JBMono';font-weight:{w};src:url('file://{ASSETS}/fonts/jetbrains-mono-latin-{w}-normal.woff2')}}"
                     for w in (500, 700, 800)) + css)
    extra = '<div class="scan"></div>' if sname == "terminal" else ""
    if sname == "glass":
        extra = ('<div class="blobs"><i style="left:-200px;top:200px;width:700px;height:700px;background:var(--blob1)"></i>'
                 '<i style="right:-220px;top:900px;width:760px;height:760px;background:var(--blob2)"></i>'
                 '<i style="left:200px;bottom:-200px;width:600px;height:600px;background:var(--blob3)"></i></div>')
    if settings.SHOW_COURSE_LABEL:
        pill = f'Մոդուլ {lesson["module"]} · Դաս {lesson["n"]}/{cur_info["module_size"]}'
        head = f'<div class="pill" id="pill"><span>{esc(pill)}</span></div><div class="prog" id="prog"><i id="pi"></i></div>'
    else:
        head = '<div class="rbar"><i id="rbi"></i></div>'      # watch-progress bar: viewers see how little is left
    bg_canvas, bg_js = "", ""
    if settings.BG_MODE == "charts":
        import json as _j
        from . import bgdata
        seed = sum(map(ord, lesson["id"]))
        data = bgdata.get(seed)
        bgs = sty["bg"]
        calm = ("chart", "math", "quiz", "myth", "bars", "steps", "stat")
        bsc = [{"a": (-1 if i == 0 else b["_t"]), "b": b["_t"] + b["_d"], "style": bgs[0] if b["kind"] == "hero" else ("plain" if b["kind"] in calm else bgs[(seed + i) % len(bgs)]),
                "seed": seed + i * 13, "acc": palette["a2"]} for i, b in enumerate(beats)]
        bsc.append({"a": total - OUTRO, "b": (total - LOOP if loop else total + 2), "style": "line", "seed": seed + 99, "acc": palette["a2"]})
        if loop:
            bsc.append({"a": total - LOOP - 1, "b": total + 2, "style": bgs[0], "seed": seed, "acc": palette["a2"]})
        bg_canvas = '<canvas id="bgc" width="1080" height="1920" style="position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:0"></canvas>'
        bg_js = (f'<script>window.BGDATA={_j.dumps(data)};window.BGSCENES={_j.dumps(bsc)};</script>'
                 f'<script src="{ASSETS}/chartbg.js"></script>')
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>{css}</style></head><body class="st-{sname}" data-trans="{sty["trans"]}" data-cap="{sty["cap"]}" style="{css_vars(palette)}">'
            f'{bg_canvas}{extra}<div class="shade"></div>{head}{"".join(scenes)}'
            f'<script src="{ASSETS}/js/lwc.js"></script><script src="{ASSETS}/js/lottie.js"></script>'
            f'<script src="{ASSETS}/engine.js"></script>{bg_js}<script>window.DURATION={total:.2f};{CHART_JS}'
            f'''captionFx();
HOOKS.push(t=>{{const end={oa:.2f};const o=1-EASE.inOut(prog(t,end-.35,.35));
 const P=document.getElementById('pill');if(P){{P.style.opacity=o;document.getElementById('prog').style.opacity=o;
 document.getElementById('pi').style.transform=`scaleX(${{clamp01(t/end)}})`;}}
 const R=document.getElementById('rbi');if(R){{R.style.transform=`scaleX(${{clamp01(t/end)}})`;R.parentElement.style.opacity=o;}}
}});logoFx({oa + 0.55:.2f});setupReel();</script></body></html>''')


def cover_html(lesson, cur_info, palette):
    """Reel cover = one brand template for every lesson (the profile grid reads as one library).
    Only the series colour changes. Everything important sits inside the 3:4 crop the grid shows (y 240-1680)."""
    sname = lesson.get("style") or "marker"
    parts = [p.strip() for p in lesson["hook"].split("|") if p.strip()]
    words = lambda t: " ".join(f'<span class="w">{esc(w)}</span>' for w in t.split())
    title = "".join(f'<span class="ln{" acc" if i == len(parts) - 1 and len(parts) > 1 else ""}">{words(p)}</span>'
                    for i, p in enumerate(parts))
    label = lesson.get("series") or f'Մոդուլ {lesson["module"]} · Դաս {lesson["n"]}'
    sub = lesson["title"]
    sub_cls = "sub mono" if sub.isascii() else "sub"
    fonts = (f"@font-face{{font-family:'JBMono';font-weight:600;src:url('file://{ASSETS}/fonts/jetbrains-mono-latin-500-normal.woff2')}}"
             f"@font-face{{font-family:'JBMono';font-weight:800;src:url('file://{ASSETS}/fonts/jetbrains-mono-latin-800-normal.woff2')}}")
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>{fonts}*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1080px;height:1920px;overflow:hidden}}'
            f'body{{background:var(--bg);color:var(--txt);font-family:ArmSans,sans-serif;position:relative;-webkit-font-smoothing:antialiased}}'
            f'.glow{{position:absolute;right:-380px;top:-160px;width:1300px;height:1300px;border-radius:50%;'
            f'background:radial-gradient(circle,var(--blob1),transparent 62%)}}'
            f'.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 2px,transparent 2px),'
            f'linear-gradient(90deg,rgba(255,255,255,.035) 2px,transparent 2px);background-size:120px 120px;background-position:-2px 58px;'
            f'-webkit-mask-image:linear-gradient(180deg,transparent 8%,#000 30%,#000 70%,transparent 92%)}}'
            f'.edge{{position:absolute;left:0;top:300px;bottom:300px;width:10px;background:var(--a)}}'
            f'.box{{position:absolute;left:96px;right:84px;top:330px;bottom:470px;display:flex;flex-direction:column;justify-content:center}}'
            f'.ser{{display:flex;align-items:center;gap:18px;font-size:38px;font-weight:700;color:var(--a2);letter-spacing:.01em}}'
            f'.ser i{{width:18px;height:18px;border-radius:4px;background:var(--a);flex:none}}'
            f'.t{{margin-top:44px;font-weight:800;line-height:1.06;letter-spacing:-.025em;font-size:118px}}'
            f'.t .ln{{display:block}}.t .w{{white-space:nowrap;display:inline-block}}.t .acc{{color:var(--a2)}}'
            f'.bar{{width:132px;height:8px;border-radius:4px;background:var(--a);margin-top:56px}}'
            f'.sub{{margin-top:34px;font-size:44px;font-weight:600;color:var(--mut);line-height:1.25}}'
            f'.sub.mono{{font-family:JBMono,ArmSans,monospace;text-transform:uppercase;letter-spacing:.04em;font-size:40px}}'
            f'.foot{{position:absolute;left:96px;right:84px;top:1500px;display:flex;align-items:center;gap:20px;'
            f'padding-top:34px;border-top:2px solid rgba(255,255,255,.10)}}'
            f'.foot .logo{{width:66px;height:66px;overflow:visible}}.foot b{{font-size:38px;font-weight:800;letter-spacing:-.01em}}'
            f'.foot span{{margin-left:auto;font-size:32px;font-weight:600;color:var(--mut)}}</style></head>'
            f'<body class="st-{sname}" style="{css_vars(palette)}"><div class="glow"></div><div class="grid"></div><div class="edge"></div>'
            f'<div class="box"><div class="ser"><i></i>{esc(label)}</div><div class="t" id="t">{title}</div>'
            f'<div class="bar"></div><div class="{sub_cls}">{esc(sub)}</div></div>'
            f'<div class="foot">{logo_svg().replace("opacity:0", "opacity:1")}<b>TradeInvest</b><span>@armtradeinvest</span></div>'
            # auto-fit: biggest size at which no word overflows and the block keeps clear of the footer
            f'''<script>function fit(){{const t=document.getElementById('t'),box=document.querySelector('.box');let s=118;
 const ok=()=>[...t.querySelectorAll('.w')].every(w=>w.getBoundingClientRect().right<=1080-84+1)&&box.scrollHeight<=box.clientHeight;
 while(s>64&&!ok()){{s-=2;t.style.fontSize=s+'px';}}}}
fit();document.fonts.ready.then(fit);</script></body></html>''')


# ---------------- main ----------------
def render_lesson(lesson, cur_info, palette, out_mp4, out_cover, music=None, used_ids=(), notes=None, clip_cache=None):
    from .render import _frames
    from playwright.sync_api import sync_playwright
    grid, moff = None, 0.0
    if music:
        lb = beat_grid_librosa(music)
        if lb:
            moff = lb[1][0]
            grid = {"beats": [t - moff for t in lb[0] if t >= moff], "downs": [t - moff for t in lb[1]]}
        else:
            ng = beat_grid(music)
            if ng:
                grid, moff = ng, ng[0]
    beats, total = plan(lesson, grid)
    work = tempfile.mkdtemp(prefix="lesson_")
    if settings.BG_MODE == "charts":                # backgrounds are drawn inside the overlay page
        foot, used = os.path.join(work, "footage.mp4"), []
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=0x070b14:s=1080x1920:r={FPS}:d={total + 1:.2f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", foot], check=True)
    else:
        foot, used = build_footage(beats, total, work, used_ids, palette, lesson.get("negative", False), clip_cache)
    html = overlay_html(lesson, cur_info, palette, beats, total)
    pattern, _ = _frames(html, work, transparent=True)
    events = []
    for i, b in enumerate(beats):
        if i:
            events.append(("whoosh" if i % 2 else "whoosh2", b["_t"] - .18, .45))
        if b["kind"] == "hero" and i:
            events.append(("impact", b["_t"] + .2, .6))
        if b["kind"] in ("card", "compare", "checklist"):
            events.append(("pop", b["_t"] + .2, .35))
        if b.get("overlay"):
            events += [("tick", b["_t"] + .35 + k * .1, .12) for k in range(12)] + [("pop", b["_t"] + 1.5, .35)]
        if b["kind"] == "stat":
            events += [("riser", b["_t"] + .1, 1.4), ("pop", b["_t"] + 1.6, .35)]
        if b["kind"] == "myth":
            events += [("impact", b["_t"] + 0.6 + 0.32 * _nwords(b["myth"]), .5), ("chime", b["_t"] + 1.2 + 0.32 * _nwords(b["myth"]), .8)]
        if b["kind"] == "quiz":
            tt = b["_t"] + 0.7 + 0.3 * _nwords(b["q"]) + 0.55 * len(b["options"]) + 0.3
            events += [("tick", tt + k, .12) for k in range(3)] + [("chime", tt + 3, .9)]
        if b["kind"] in ("steps", "bars"):
            n = len(b["items"]); gap = 1.1 if b["kind"] == "steps" else 0.8
            events += [("pop", b["_t"] + .7 + k * gap, .3) for k in range(n)]
        if lesson.get("style") == "terminal" and b["kind"] == "broll":
            words = b["text"].split(); chs = chunks(words)
            need = [max(settings.CHUNK_MIN, len(c) * settings.WORD_SEC) for c in chs]
            sc_ = (b["_d"] - 0.45) / max(sum(need), 1e-6); tt = b["_t"] + 0.15
            for n_ in need:
                events += [("tick", tt + k * .07, .08) for k in range(5)]; tt += n_ * sc_
    events += [("whoosh", total - OUTRO - .18, .45), ("logo", total - OUTRO + 0.5, .8)]
    wav = os.path.join(work, "mix.wav")
    mix_audio(music, events, total, wav, music_offset=moff)
    # Manim clips for calculation beats (transparent), laid over everything else at their beat time
    extra_in, chain, last = [], "[0:v][1:v]overlay=shortest=1:format=auto[b0]", "[b0]"
    from . import manim_scenes
    for j, b in enumerate([b for b in beats if b["kind"] == "math"]):
        if not manim_scenes.available():
            break
        mov = os.path.join(work, f"math{j}.mov")
        try:
            manim_scenes.render(b.get("template", "rr"), palette, b["_d"] - 0.3, FPS, mov, b.get("mtitle"))
        except Exception as exc:  # noqa: BLE001
            print("[manim]", str(exc)[:200]); continue
        idx = 3 + len(extra_in) // 2
        extra_in += ["-i", mov]
        a0 = b["_t"] + 0.15
        chain += (f";[{idx}:v]setpts=PTS+{a0:.3f}/TB[m{j}];{last}[m{j}]overlay=x=40:y=470:eof_action=pass:"
                  f"enable='between(t,{a0:.2f},{b['_t'] + b['_d']:.2f})'[b{j + 1}]")
        last = f"[b{j + 1}]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", foot, "-framerate", str(FPS), "-i", pattern, "-i", wav, *extra_in,
                    "-filter_complex", chain + f";{last}null[v];[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]",
                    "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4], check=True)
    ch = os.path.join(work, "cover.html")
    open(ch, "w", encoding="utf-8").write(cover_html(lesson, cur_info, palette))
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1080, "height": 1920}, locale="en-US")
        pg.goto(f"file://{ch}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        pg.screenshot(path=out_cover, type="jpeg", quality=92); br.close()
    graphic_time = sum(b["_d"] for b in beats if b["kind"] in GRAPHIC)
    shutil.rmtree(work, ignore_errors=True)
    return {"duration": total, "clips": used, "html": html, "graphic_share": graphic_time / max(1e-6, total - OUTRO),
            "beats": [(b["kind"], round(float(b["_t"]), 2), round(float(b["_d"]), 2)) for b in beats],
            "chart_sources": [b.get("_chart_src") for b in beats if b["kind"] == "chart"]}
