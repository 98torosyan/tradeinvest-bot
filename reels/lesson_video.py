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
GRAPHIC = {"hero", "card", "compare", "checklist", "chart", "math"}


# ---------------- music beat grid (numpy only) ----------------
def beat_grid_librosa(music, seconds=120):
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
            at = (0.55 + 0.8 if b.get("first") else 0.2) + i * 0.62   # first scene starts 0.8 s "early" (hook on frame 0)
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


def _graphic(b):
    k = b["kind"]
    if k == "card":
        return (f'<div class="dim"></div><div class="gcard" data-fx="pop" data-at=".15" data-dur=".55">{_icon_html(icon_for(b), .3)}'
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
    scenes = []
    for i, b in enumerate(beats):
        a, d = b["_t"], b["_d"]
        a_in = -0.8 if i == 0 else a                     # first scene already fully visible at frame 0
        if b["kind"] == "hero":
            inner = _hero(b); cls = "hero"
        elif b["kind"] == "broll":
            inner = (_price(b["overlay"]) if b.get("overlay") else "") + _captions(b); cls = "beat"
        else:
            inner = _graphic(b); cls = "graphic beat" if b["kind"] in ("chart", "math") else "graphic"
        scenes.append(f'<section class="scene {cls}" data-in="{a_in:.2f}" data-out="{a + d:.2f}">{inner}</section>')
    oa = total - OUTRO
    nxt = cur_info.get("next_title") if settings.SHOW_COURSE_LABEL else None
    if not settings.SHOW_COURSE_LABEL:
        scenes_cta = ('<div class="nxt" data-fx="rise" data-at=".1" data-dur=".5">Ամեն օր՝ նոր թրեյդինգ դաս</div>'
                      '<div class="nxt2" data-fx="rise" data-at=".25" data-dur=".6">Հետևիր @armtradeinvest</div>')
    else:
        scenes_cta = ""
    nxt_html = (f'<div class="nxt" data-fx="rise" data-at=".1" data-dur=".5">Հաջորդ դասը</div>'
                f'<div class="nxt2" data-fx="rise" data-at=".25" data-dur=".6">{esc(nxt)}</div>') if nxt else ""
    scenes.append(f'<section class="scene outro" data-in="{oa:.2f}" data-out="{total + 1:.2f}"><div class="obg"></div>{nxt_html or scenes_cta}'
                  f'{logo_svg()}<div class="name" data-fx="rise" data-at="1.3" data-dur=".6">TradeInvest</div></section>')
    css = open(os.path.join(ASSETS, "broll.css"), encoding="utf-8").read() + open(os.path.join(ASSETS, "lesson.css"), encoding="utf-8").read()
    if settings.SHOW_COURSE_LABEL:
        pill = f'Մոդուլ {lesson["module"]} · Դաս {lesson["n"]}/{cur_info["module_size"]}'
        head = f'<div class="pill" id="pill"><span>{esc(pill)}</span></div><div class="prog" id="prog"><i id="pi"></i></div>'
    else:
        head = ""
    bg_canvas, bg_js = "", ""
    if settings.BG_MODE == "charts":
        import json as _j
        from . import bgdata
        seed = sum(map(ord, lesson["id"]))
        data = bgdata.get(seed)
        styles = settings.BG_STYLES
        bsc = [{"a": (-1 if i == 0 else b["_t"]), "b": b["_t"] + b["_d"], "style": "candles" if b["kind"] == "hero" else ("plain" if b["kind"] in ("chart", "math") else styles[(seed + i) % len(styles)]),
                "seed": seed + i * 13, "acc": palette["a2"]} for i, b in enumerate(beats)]
        bsc.append({"a": total - OUTRO, "b": total + 2, "style": "line", "seed": seed + 99, "acc": palette["a2"]})
        bg_canvas = '<canvas id="bgc" width="1080" height="1920" style="position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:0"></canvas>'
        bg_js = (f'<script>window.BGDATA={_j.dumps(data)};window.BGSCENES={_j.dumps(bsc)};</script>'
                 f'<script src="{ASSETS}/chartbg.js"></script>')
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>{css}</style></head><body style="{css_vars(palette)}">'
            f'{bg_canvas}<div class="shade"></div>{head}{"".join(scenes)}'
            f'<script src="{ASSETS}/js/lwc.js"></script><script src="{ASSETS}/js/lottie.js"></script>'
            f'<script src="{ASSETS}/engine.js"></script>{bg_js}<script>window.DURATION={total:.2f};{CHART_JS}'
            f'''(function(){{const o=applyFx;applyFx=function(it,l){{if(it.dataset.fx!=='slam')return o(it,l);
 const r=prog(l,+it.dataset.at,+it.dataset.dur);const e=r<=0?0:EASE.back(r);it.style.opacity=clamp01(r*3);
 it.style.transform=`scale(${{1.18-.18*e}})`;it.style.filter=`blur(${{(1-clamp01(r*2.2))*6}}px)`;}};}})();
HOOKS.push(t=>{{const end={oa:.2f};const o=1-EASE.inOut(prog(t,end-.35,.35));
 const P=document.getElementById('pill');if(P){{P.style.opacity=o;document.getElementById('prog').style.opacity=o;
 document.getElementById('pi').style.transform=`scaleX(${{clamp01(t/end)}})`;}}
 for(const sc of SCENES){{if(!sc.el.classList.contains('beat'))continue;const l=t-sc.a;
  sc.el.querySelectorAll('.chunk').forEach(c=>{{const on=l>=+c.dataset.s&&l<+c.dataset.e+(c.nextElementSibling?0:9);
   c.style.display=on?'block':'none';const k=Math.min(1,EASE.back(clamp01((l-+c.dataset.s)/.22)));c.style.transform=`scale(${{.88+.12*k}})`;}});
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
