"""Professional B-roll educational Reel.

Every sentence ("beat") gets its own real video clip from Pexels, cut hard
on the beat with a slow push-in / pull-out, colour-graded, with big
TikTok-style captions (the spoken word lights up) and a few graphic
overlays (price counters, arrows). Transitions carry whoosh sounds.
The footage is assembled with ffmpeg; captions/overlays are rendered as a
transparent HTML layer and laid on top."""
import json
import math
import os
import shutil
import subprocess
import tempfile
import wave

import numpy as np

from . import pexels
from .builder import ASSETS, esc, logo_svg
from .palettes import css_vars

FPS = int(os.environ.get("REEL_FPS", "30"))
SR = 44100
SFX = os.path.join(ASSETS, "sfx")
OUTRO = 5.0


def _run(cmd):
    subprocess.run(cmd, check=True)


def beat_len(b):
    n = len(b["text"].replace("|", " ").split())
    d = n * 0.42 + 0.9
    return max(2.8 if b.get("style") == "hero" else 2.2, min(4.4, d))


def chunks(words, maxw=3, maxc=18):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or len(" ".join(cur + [w])) > maxc):
            out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def word_times(words, span, start=0.15):
    """Spread words over the spoken span proportionally to their length."""
    w = [len(x) + 2 for x in words]; tot = sum(w) or 1
    out, t = [], start
    for x in w:
        d = span * x / tot; out.append((t, t + d)); t += d
    return out


# ---------------- footage ----------------
def _probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _segment(src, start, dur, out, i, tint):
    frames = max(1, int(round(dur * FPS)))
    zin = i % 2 == 0
    z = f"1+0.10*on/{frames}" if zin else f"1.10-0.10*on/{frames}"
    vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={FPS},"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={FPS},"
          f"eq=contrast=1.08:saturation=0.88:brightness=-0.03,vignette=PI/5")
    if src:
        _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-i", src, "-t", f"{dur:.3f}", "-vf", vf,
              "-an", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out])
    else:  # no clip available: slow-moving brand gradient
        _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
              f"gradients=s=1080x1920:d={dur:.3f}:speed=0.015:c0=0x{tint}:c1=0x1a2a44:c2=0x0b1220:r={FPS}",
              "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out])


def build_footage(beats, work, used_ids, tint):
    segs, clips = [], []
    for i, b in enumerate(beats):
        d = b["_d"]
        path, vid = pexels.fetch(b.get("query", ""), used_ids | {c[1] for c in clips if c[1]})
        if vid:
            clips.append((path, vid))
        src = path or (clips[-1][0] if clips else None)
        start = 0.0
        if src:
            total = _probe_dur(src)
            start = min(1.0, max(0.0, total - d - 0.1)) if not path else min(0.8, max(0.0, total - d - 0.1))
            if total and total < d:  # too short: loop it
                looped = os.path.join(work, f"loop{i}.mp4")
                _run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "3", "-i", src, "-t", f"{d + 1:.2f}",
                      "-c:v", "libx264", "-preset", "veryfast", "-an", looped])
                src, start = looped, 0.0
        seg = os.path.join(work, f"seg{i:02d}.mp4")
        _segment(src, start, d, seg, i, tint)
        segs.append(seg)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        f.write("".join(f"file '{s}'\n" for s in segs))
    foot = os.path.join(work, "footage.mp4")
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
          "-vf", f"tpad=stop_mode=clone:stop_duration={OUTRO}", "-c:v", "libx264", "-preset", "veryfast",
          "-crf", "18", "-pix_fmt", "yuv420p", foot])
    return foot, [c[1] for c in clips]


# ---------------- overlay layer ----------------
def overlay_html(spec, palette, beats, total):
    scenes, t = [], 0.0
    for b in beats:
        a, d = b["_t"], b["_d"]
        words = b["text"].replace("|", " ").split()
        if b.get("style") == "hero":
            inner, k = "", 0
            parts = [p.split() for p in b["text"].split("|")] if "|" in b["text"] else chunks(words, 2, 16)
            wt = word_times(words, b.get("_span", d - 0.6)); k0 = 0
            for ci, ch in enumerate(parts):
                at = wt[k0][0] if b.get("_voice") else 0.15 + ci * 0.45
                k0 += len(ch)
                inner += f'<div class="hl" data-fx="slam" data-at="{at:.2f}" data-dur=".45">{esc(" ".join(ch))}</div>'
            scenes.append(f'<section class="scene hero" data-in="{a:.2f}" data-out="{a + d:.2f}"><div class="dim"></div>'
                          f'<div class="hstack">{inner}</div></section>')
            continue
        wt = word_times(words, b.get("_span", d - 0.35))
        cap, wi = "", 0
        for ch in chunks(words):
            s0 = wt[wi][0]; s1 = wt[wi + len(ch) - 1][1]
            ws = "".join(f'<span class="w" data-s="{wt[wi + j][0]:.2f}" data-e="{wt[wi + j][1]:.2f}">{esc(w)}</span> '
                         for j, w in enumerate(ch))
            cap += f'<div class="chunk" data-s="{s0:.2f}" data-e="{s1:.2f}">{ws}</div>'
            wi += len(ch)
        ov = ""
        o = b.get("overlay")
        if o and o.get("type") == "price":
            up = o.get("dir", "up") == "up"
            pct = (o["to"] / o["from"] - 1) * 100
            ov = (f'<div class="ptag" data-fx="pop" data-at=".2" data-dur=".5"><span data-fx="count" data-at=".45" data-dur="1.3" '
                  f'data-from="{o["from"]}" data-to="{o["to"]}" data-pre="$">{o["from"]}</span>'
                  f'<b class="{"up" if up else "dn"}" data-fx="pop" data-at="1.7" data-dur=".5">{"▲" if up else "▼"} {abs(pct):.0f}%</b></div>')
        scenes.append(f'<section class="scene beat" data-in="{a:.2f}" data-out="{a + d:.2f}">{ov}<div class="cap">{cap}</div></section>')
    oa = total - OUTRO
    scenes.append(f'''<section class="scene outro" data-in="{oa:.2f}" data-out="{total:.2f}"><div class="obg"></div>
<div class="nxt" data-fx="rise" data-at=".2" data-dur=".6">Հաջորդ դասը</div>
<div class="nxt2" data-fx="rise" data-at=".4" data-dur=".7">{esc(spec.get("next", ""))}</div>
{logo_svg()}
<div class="name" data-fx="rise" data-at="2.0" data-dur=".7">TradeInvest</div>
<div class="cta" data-fx="pop" data-at="2.4" data-dur=".7">{esc(spec.get("cta", "Պահիր այս դասը"))}</div></section>''')
    css = open(os.path.join(ASSETS, "broll.css"), encoding="utf-8").read()
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>{css}</style></head><body style="{css_vars(palette)}">'
            f'<div class="shade"></div><div class="pill" id="pill"><span>{esc(spec.get("pill", ""))}</span></div>'
            f'<div class="prog" id="prog"><i id="pi"></i></div>{"".join(scenes)}'
            f'<script src="{ASSETS}/engine.js"></script><script>window.DURATION={total:.2f};'
            f'''(function(){{const o=applyFx;applyFx=function(it,l){{if(it.dataset.fx!=='slam')return o(it,l);
 const r=prog(l,+it.dataset.at,+it.dataset.dur);const e=r<=0?0:EASE.back(r);it.style.opacity=clamp01(r*3);
 it.style.transform=`scale(${{1.4-.4*e}})`;it.style.filter=`blur(${{(1-clamp01(r*1.6))*12}}px)`;}};}})();
HOOKS.push(t=>{{const end={oa:.2f};const o=1-EASE.inOut(prog(t,end-.4,.4));
 document.getElementById('pill').style.opacity=Math.min(o,EASE.out(prog(t,.2,.5)));
 document.getElementById('prog').style.opacity=o;document.getElementById('pi').style.transform=`scaleX(${{clamp01(t/end)}})`;
 for(const sc of SCENES){{if(!sc.el.classList.contains('beat'))continue;const l=t-sc.a;
  sc.el.querySelectorAll('.chunk').forEach(c=>{{const on=l>=+c.dataset.s&&l<+c.dataset.e+(c.nextElementSibling?0:9);
   c.style.display=on?'block':'none';const k=EASE.back(clamp01((l-+c.dataset.s)/.22));c.style.transform=`scale(${{.85+.15*k}})`;}});
  sc.el.querySelectorAll('.w').forEach(w=>w.classList.toggle('on',l>=+w.dataset.s&&l<+w.dataset.e));}}
}});logoFx({oa + 0.9:.2f});setupReel();</script></body></html>''')


# ---------------- audio ----------------
def _load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768


def mix_audio(music, events, total, out_wav, voices=(), music_gain=0.36, music_offset=0.0):
    n = int(total * SR)
    mix = np.zeros((n, 2), np.float32)
    if music:
        m = _load(music)
        m = m[int(max(0.0, music_offset) * SR):] if len(m) > int(music_offset * SR) + SR else m
        m = np.tile(m, (int(math.ceil(n / len(m))), 1))[:n]
        env = np.ones(n); fi, fo = int(.6 * SR), int(2.2 * SR)
        env[:fi] = np.linspace(0, 1, fi); env[-fo:] = np.linspace(1, 0, fo)
        mix += m * music_gain * env[:, None]
    for path, t in voices:
        v = _load(path); i = int(t * SR); j = min(n, i + len(v))
        if j > i:
            mix[i:j] += v[:j - i] * 1.0
    cache = {}
    for name, t, g in events:
        p = os.path.join(SFX, name + ".mp3")
        if not os.path.exists(p):
            continue
        s = cache.setdefault(name, _load(p))
        i = max(0, int(t * SR)); j = min(n, i + len(s))
        if j > i:
            mix[i:j] += s[:j - i] * g
    mix /= max(1.0, float(np.max(np.abs(mix))) / 0.95)
    with wave.open(out_wav, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


# ---------------- main ----------------
def render_broll(spec, palette, out_mp4, music=None, used_ids=(), voice=None, notes=None):
    from .render import _frames
    beats = [dict(b) for b in spec["beats"]]
    work = tempfile.mkdtemp(prefix="broll_")
    if voice:
        from . import gemini
        try:
            for i, b in enumerate(beats):
                path = gemini.tts(b["text"].replace("|", " "), voice, os.path.join(work, f"v{i:02d}.wav"))
                with wave.open(path) as w:
                    span = w.getnframes() / w.getframerate()
                b["_voice"], b["_span"] = path, span
        except Exception as exc:  # noqa: BLE001
            if notes is not None:
                notes.append(f"[voice] disabled: {str(exc)[:200]}")
            for b in beats:
                b.pop("_voice", None); b.pop("_span", None)
    t = 0.0
    for b in beats:
        d = beat_len(b)
        if b.get("_voice"):
            d = max(1.6, b["_span"] + 0.5)
        b["_t"], b["_d"] = t, d; t += d
    total = t + OUTRO
    tint = palette["bg"].split("#", 1)[1][:6] if "#" in palette["bg"] else "0b1220"
    foot, used = build_footage(beats, work, set(used_ids), tint)
    pattern, _ = _frames(overlay_html(spec, palette, beats, total), work, transparent=True)
    events = [("riser", 0.0, .45)]
    for i, b in enumerate(beats):
        if i:
            events.append(("whoosh" if i % 2 else "whoosh2", b["_t"] - .18, .5))
        if b.get("style") == "hero":
            events.append(("impact", b["_t"] + .2, .75))
        if b.get("overlay"):
            events.append(("pop", b["_t"] + .2, .4))
            events += [("tick", b["_t"] + .45 + k * .1, .14) for k in range(13)]
            events.append(("pop", b["_t"] + 1.7, .4))
    events += [("whoosh", total - OUTRO - .18, .5)] + [("pop", total - OUTRO + .9 + k * .16, .22) for k in range(5)]
    events.append(("chime", total - OUTRO + 2.2, .4))
    wav = os.path.join(work, "mix.wav")
    voices = [(b["_voice"], b["_t"] + 0.15) for b in beats if b.get("_voice")]
    mix_audio(music, events, total, wav, voices, music_gain=0.15 if voices else 0.36)
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", foot, "-framerate", str(FPS), "-i", pattern, "-i", wav,
          "-filter_complex", "[0:v][1:v]overlay=shortest=1:format=auto[v];[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]",
          "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4])
    shutil.rmtree(work, ignore_errors=True)
    return total, used
