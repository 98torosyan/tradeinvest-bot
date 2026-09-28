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
GRAPHIC = {"hero", "card", "compare", "checklist"}


# ---------------- music beat grid (numpy only) ----------------
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
    if not grid:
        return times
    off, per = grid
    out = []
    for t in times:
        k = round((t - 0) / per)
        cand = k * per
        out.append(cand if abs(cand - t) <= tol else t)
    return out


# ---------------- timing ----------------
def _nwords(*parts):
    return sum(len(str(p).replace("|", " ").split()) for p in parts)


def beat_len(b):
    k, W = b["kind"], settings.WORD_SEC
    if k == "hero":
        return max(2.4, 0.9 + 0.5 * len(b["text"].split("|")) + 0.12 * _nwords(b["text"]))
    if k == "card":
        return min(5.5, max(3.0, 1.6 + 0.5 * _nwords(b["title"], b["text"])))
    if k == "compare":
        return min(6.5, max(4.0, 2.0 + 0.42 * _nwords(*b["a"], *b["b"])))
    if k == "checklist":
        return min(7.5, max(4.0, 1.4 + 1.1 * len(b["items"]) + 0.15 * _nwords(*b["items"])))
    return min(4.6, max(2.0, 0.9 + W * _nwords(b["text"])))


def plan(lesson, grid):
    beats = [{"kind": "hero", "text": lesson["hook"], "first": True}] + [dict(b) for b in lesson["beats"]] + \
            [{"kind": "hero", "text": lesson["recap"], "query": lesson["beats"][0].get("query", "")}]
    cuts, t = [], 0.0
    for b in beats:
        t += beat_len(b); cuts.append(t)
    cuts = snap(cuts, grid)
    start = 0.0
    for b, c in zip(beats, cuts):
        b["_t"], b["_d"] = start, max(1.6, c - start); start = b["_t"] + b["_d"]
    return beats, start + OUTRO


# ---------------- footage ----------------
def _clip_ok(negative):
    from . import gemini

    def check(path):
        frame = path + ".jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.5", "-i", path, "-frames:v", "1", frame])
        if not os.path.exists(frame):
            return False
        flags = gemini.frame_flags(frame)
        if flags is None:                  # check unavailable: accept neutral lessons, never risk faces in negative ones
            return not negative
        if flags["text"] or flags["logo"]:
            return False
        return not (negative and flags["face"])
    return check


def build_footage(beats, total, work, used_ids, tint, negative):
    segs, used = [], []
    last = None
    check = _clip_ok(negative)
    for i, b in enumerate(beats):
        d = b["_d"]
        path, vid = pexels.fetch(b.get("query", ""), set(used_ids) | set(used), check=check)
        if vid:
            used.append(vid); last = path
        src = path or last
        start = 0.0
        if src:
            dur = _probe_dur(src)
            start = min(0.8, max(0.0, dur - d - 0.1))
            if dur and dur < d:
                looped = os.path.join(work, f"loop{i}.mp4")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "3", "-i", src, "-t", f"{d + 1:.2f}",
                                "-an", "-c:v", "libx264", "-preset", "veryfast", looped], check=True)
                src, start = looped, 0.0
        seg = os.path.join(work, f"seg{i:02d}.mp4")
        _segment(src, start, d, seg, i, tint)
        segs.append(seg)
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    foot = os.path.join(work, "footage.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf",
                    f"tpad=stop_mode=clone:stop_duration={OUTRO + 1}", "-t", f"{total:.2f}", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", foot], check=True)
    return foot, used


# ---------------- overlay (captions + motion graphics) ----------------
def _fit(text, base, width=900, k=0.64):
    """Font size so that the longest word/line fits the safe width (Armenian glyphs are wide)."""
    longest = max(len(text), 1)
    return int(min(base, width / (longest * k)))


def _hero(b):
    parts = b["text"].split("|")
    html = ""
    for i, p in enumerate(parts):
        last = i == len(parts) - 1 and len(parts) > 1
        size = _fit(max(p.split(), key=len) if len(p) > 14 else p, 150 if last else 128, width=880, k=0.92)
        style = f' style="font-size:{size}px"'
        if b.get("first") and i == 0:
            html += f'<div class="hl"{style}>{esc(p)}</div>'                      # visible on frame 0 (hook)
        else:
            at = (0.35 if b.get("first") else 0.15) + i * 0.42
            html += f'<div class="hl" data-fx="slam" data-at="{at:.2f}" data-dur=".42"{style}>{esc(p)}</div>'
    return f'<div class="dim"></div><div class="hstack">{html}</div>'


def _captions(b):
    words = b["text"].split()
    wt = word_times(words, b["_d"] - 0.35)
    out, wi = "", 0
    for ch in chunks(words):
        s0, s1 = wt[wi][0], wt[wi + len(ch) - 1][1]
        ws = "".join(f'<span class="w" data-s="{wt[wi + j][0]:.2f}" data-e="{wt[wi + j][1]:.2f}">{esc(w)}</span> '
                     for j, w in enumerate(ch))
        fs = _fit(max(ch, key=len), 92, width=860, k=0.86)
        out += f'<div class="chunk" style="font-size:{fs}px" data-s="{s0:.2f}" data-e="{s1:.2f}">{ws}</div>'
        wi += len(ch)
    return f'<div class="cap">{out}</div>'


def _price(o):
    up = o.get("dir", "up") == "up"
    pct = (o["to"] / o["from"] - 1) * 100
    return (f'<div class="ptag" data-fx="pop" data-at=".15" data-dur=".45"><span data-fx="count" data-at=".35" data-dur="1.2" '
            f'data-from="{o["from"]}" data-to="{o["to"]}" data-pre="$">{o["from"]}</span>'
            f'<b class="{"up" if up else "dn"}" data-fx="pop" data-at="1.5" data-dur=".45">{"▲" if up else "▼"} {abs(pct):.0f}%</b></div>')


def _graphic(b):
    k = b["kind"]
    if k == "card":
        return (f'<div class="dim"></div><div class="gcard" data-fx="pop" data-at=".15" data-dur=".55">'
                f'<div class="gt">{esc(b["title"])}</div><div class="gx" data-fx="rise" data-at=".55" data-dur=".6">{esc(b["text"])}</div></div>')
    if k == "compare":
        a, c = b["a"], b["b"]
        return (f'<div class="dim"></div><div class="cmp">'
                f'<div class="side l" data-fx="rise" data-at=".2" data-dur=".6"><div class="gt">{esc(a[0])}</div><div class="gx">{esc(a[1])}</div></div>'
                f'<div class="vs" data-fx="pop" data-at=".7" data-dur=".5">VS</div>'
                f'<div class="side r" data-fx="rise" data-at="1.0" data-dur=".6"><div class="gt">{esc(c[0])}</div><div class="gx">{esc(c[1])}</div></div></div>')
    if k == "checklist":
        items = "".join(f'<div class="it" data-fx="rise" data-at="{0.6 + i * 1.0:.2f}" data-dur=".5"><i>✓</i>{esc(x)}</div>'
                        for i, x in enumerate(b["items"]))
        return (f'<div class="dim"></div><div class="chk"><div class="gt" data-fx="rise" data-at=".15" data-dur=".5">{esc(b["title"])}</div>'
                f'{items}</div>')
    return ""


def overlay_html(lesson, cur_info, palette, beats, total):
    scenes = []
    for i, b in enumerate(beats):
        a, d = b["_t"], b["_d"]
        a_in = -0.8 if i == 0 else a                     # first scene already fully visible at frame 0
        if b["kind"] == "hero":
            inner = _hero(b); cls = "hero"
        elif b["kind"] == "broll":
            inner = (_price(b["overlay"]) if b.get("overlay") else "") + _captions(b); cls = "beat"
        else:
            inner = _graphic(b); cls = "graphic"
        scenes.append(f'<section class="scene {cls}" data-in="{a_in:.2f}" data-out="{a + d:.2f}">{inner}</section>')
    oa = total - OUTRO
    nxt = cur_info.get("next_title")
    nxt_html = (f'<div class="nxt" data-fx="rise" data-at=".1" data-dur=".5">Հաջորդ դասը</div>'
                f'<div class="nxt2" data-fx="rise" data-at=".25" data-dur=".6">{esc(nxt)}</div>') if nxt else ""
    scenes.append(f'<section class="scene outro" data-in="{oa:.2f}" data-out="{total + 1:.2f}"><div class="obg"></div>{nxt_html}'
                  f'{logo_svg()}<div class="name" data-fx="rise" data-at="1.3" data-dur=".6">TradeInvest</div></section>')
    css = open(os.path.join(ASSETS, "broll.css"), encoding="utf-8").read() + open(os.path.join(ASSETS, "lesson.css"), encoding="utf-8").read()
    pill = f'Մոդուլ {lesson["module"]} · Դաս {lesson["n"]}/{cur_info["module_size"]}'
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>{css}</style></head><body style="{css_vars(palette)}">'
            f'<div class="shade"></div><div class="pill" id="pill"><span>{esc(pill)}</span></div>'
            f'<div class="prog" id="prog"><i id="pi"></i></div>{"".join(scenes)}'
            f'<script src="{ASSETS}/engine.js"></script><script>window.DURATION={total:.2f};'
            f'''(function(){{const o=applyFx;applyFx=function(it,l){{if(it.dataset.fx!=='slam')return o(it,l);
 const r=prog(l,+it.dataset.at,+it.dataset.dur);const e=r<=0?0:EASE.back(r);it.style.opacity=clamp01(r*3);
 it.style.transform=`scale(${{1.4-.4*e}})`;it.style.filter=`blur(${{(1-clamp01(r*1.6))*12}}px)`;}};}})();
HOOKS.push(t=>{{const end={oa:.2f};const o=1-EASE.inOut(prog(t,end-.35,.35));
 document.getElementById('pill').style.opacity=o;document.getElementById('prog').style.opacity=o;
 document.getElementById('pi').style.transform=`scaleX(${{clamp01(t/end)}})`;
 for(const sc of SCENES){{if(!sc.el.classList.contains('beat'))continue;const l=t-sc.a;
  sc.el.querySelectorAll('.chunk').forEach(c=>{{const on=l>=+c.dataset.s&&l<+c.dataset.e+(c.nextElementSibling?0:9);
   c.style.display=on?'block':'none';const k=EASE.back(clamp01((l-+c.dataset.s)/.22));c.style.transform=`scale(${{.85+.15*k}})`;}});
  sc.el.querySelectorAll('.w').forEach(w=>w.classList.toggle('on',l>=+w.dataset.s&&l<+w.dataset.e));}}
}});logoFx({oa + 0.55:.2f});setupReel();</script></body></html>''')


def cover_html(lesson, cur_info, palette):
    title = "<br>".join(esc(p) for p in lesson["hook"].split("|"))
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1080px;height:1920px;overflow:hidden}}'
            f'body{{background:var(--bg);color:var(--txt);font-family:ArmSans,sans-serif;display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;gap:56px;text-align:center}}'
            f'.m{{font-size:44px;font-weight:700;color:var(--onacc);background:linear-gradient(135deg,var(--a2),var(--a));padding:16px 34px;border-radius:50px}}'
            f'.t{{font-family:ArmSerif,serif;font-weight:800;font-size:112px;line-height:1.1;padding:0 70px}}'
            f'.s{{font-size:46px;color:var(--mut);font-weight:600;padding:0 90px}}.logo{{width:120px;height:120px}}</style></head>'
            f'<body style="{css_vars(palette)}"><div class="m">Մոդուլ {lesson["module"]} · Դաս {lesson["n"]}</div>'
            f'<div class="t">{title}</div><div class="s">{esc(lesson["title"])}</div>'
            f'{logo_svg().replace("opacity:0", "opacity:1")}</body></html>')


# ---------------- main ----------------
def render_lesson(lesson, cur_info, palette, out_mp4, out_cover, music=None, used_ids=(), notes=None):
    from .render import _frames
    from playwright.sync_api import sync_playwright
    grid = beat_grid(music) if music else None
    beats, total = plan(lesson, grid)
    work = tempfile.mkdtemp(prefix="lesson_")
    tint = palette["bg"].split("#", 1)[1][:6]
    foot, used = build_footage(beats, total, work, used_ids, tint, lesson.get("negative", False))
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
    events += [("whoosh", total - OUTRO - .18, .45), ("logo", total - OUTRO + 0.5, .8)]
    wav = os.path.join(work, "mix.wav")
    mix_audio(music, events, total, wav, music_offset=(grid[0] if grid else 0.0))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", foot, "-framerate", str(FPS), "-i", pattern, "-i", wav,
                    "-filter_complex", "[0:v][1:v]overlay=shortest=1:format=auto[v];[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]",
                    "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4], check=True)
    ch = os.path.join(work, "cover.html")
    open(ch, "w", encoding="utf-8").write(cover_html(lesson, cur_info, palette))
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(f"file://{ch}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        pg.screenshot(path=out_cover, type="jpeg", quality=92); br.close()
    graphic_time = sum(b["_d"] for b in beats if b["kind"] in GRAPHIC)
    shutil.rmtree(work, ignore_errors=True)
    return {"duration": total, "clips": used, "html": html, "graphic_share": graphic_time / max(1e-6, total - OUTRO),
            "beats": [(b["kind"], round(b["_t"], 2), round(b["_d"], 2)) for b in beats]}
