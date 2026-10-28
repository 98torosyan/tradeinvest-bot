"""Reel covers, brand system v3. Two templates, chosen per lesson:
  NUMBER - lessons whose content has a real number (stat beat, or a %/$ figure in the hook): a huge number + its proof.
  TAG    - every other lesson: an illustrative chart with an amber last-price tag pinned to the key level;
           the hook's key word sits inside the tag, a hand-drawn ring marks the moment.
Grounds alternate Ink / Paper by lesson number, so the 3-column grid reads as a checkerboard.
Everything important stays inside the 3:4 grid crop (y 240-1680)."""
import html
import math
import random
import re

from . import brand

W, H = 1080, 1920
M = 72                                   # outer margin
PATTERNS = ["support", "resistance", "uptrend", "downtrend", "range", "breakout", "fakeout",
            "double_top", "double_bottom", "head_shoulders", "triangle", "flag", "retest"]
NUM_RE = re.compile(r"[−-]?\$?\d+(?:[.,]\d+)?\s?%|\$\d[\d,.]*")


def esc(s):
    return html.escape(str(s), quote=False)


def _number(lesson):
    """(big, rows) for the NUMBER template, or None."""
    for b in lesson.get("beats", []):
        if b.get("kind") == "stat":
            v = f'{b.get("pre", "")}{b["value"]}{b.get("post", "")}'.replace("-", "−")
            rows = [r for r in (b.get("label"), b.get("sub")) if r]
            return v, rows
    m = NUM_RE.search(lesson["hook"].replace("|", " "))
    if m:
        return m.group(0).replace(" ", "").replace("-", "−"), [lesson["title"]]
    return None


def _pattern(lesson):
    for b in lesson.get("beats", []):
        if b.get("kind") == "chart" and b.get("pattern") in PATTERNS:
            return b["pattern"]
    return PATTERNS[sum(map(ord, lesson["id"])) % len(PATTERNS)]


LEVEL_HY = {"support": "Support", "resistance": "Resistance", "neckline": "Neckline", "breakout": "Breakout",
            "retest": "Retest", "stop": "Stop", "target": "Target"}


def _tag_text(lesson, levels=None):
    """Short label for the price tag: the lesson's own term (title or a keyword) if it fits, otherwise the
    name of the level drawn on the chart. Never the series name -- the tag must say something about THIS lesson."""
    for t in [lesson["title"]] + list(lesson.get("keywords", [])):
        t = t.strip()
        if 2 <= len(t) <= 16 and "հայերեն" not in t:
            return t[0].upper() + t[1:] if t[0].islower() and t.isascii() else t
    return LEVEL_HY.get(_pattern(lesson), "Level")


def _split_hook(hook):
    """Headline lines + the short key phrase that goes into the price tag (max 2 words / 16 letters)."""
    lines = [p.strip() for p in hook.split("|") if p.strip()]
    last = lines[-1]
    clean = last.strip("«».,։:՝ ")
    if len(lines) > 1 and len(clean) <= 16 and len(clean.split()) <= 2:
        return lines[:-1], clean
    words = last.split()
    key = words[-1].strip("«».,։:՝ ")
    rest = " ".join(words[:-1])
    head = lines[:-1] + ([rest] if rest else [])
    return (head or [last]), key


def _chart_svg(lesson, dark, w=W, h=620):
    """Candles + key level as SVG; returns (svg, level_y, last_x)."""
    from .charts import ideal
    bars, levels, _ = ideal(_pattern(lesson), n=44, seed=sum(map(ord, lesson["id"])) % 97)
    lo = min(b["low"] for b in bars); hi = max(b["high"] for b in bars)
    level = levels[0]["price"] if levels else bars[-1]["close"]
    lo, hi = min(lo, level), max(hi, level)
    pad = (hi - lo) * .08 or 1
    lo, hi = lo - pad, hi + pad
    y = lambda v: (hi - v) / (hi - lo) * h
    right = w - 300                                  # room for the tag on the right
    step = (right - M) / len(bars); bw = step * .58
    up = "#D9D6CF" if dark else "#2B2A28"            # monochrome candles; colour is reserved for the accent
    dn = "#5E5B55" if dark else "#9C978C"
    out = []
    for i, b in enumerate(bars):
        x = M + i * step + step / 2
        col = up if b["close"] >= b["open"] else dn
        t, bo = y(max(b["open"], b["close"])), y(min(b["open"], b["close"]))
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(b["high"]):.1f}" y2="{y(b["low"]):.1f}" stroke="{col}" stroke-width="3"/>'
                   f'<rect x="{x - bw / 2:.1f}" y="{t:.1f}" width="{bw:.1f}" height="{max(3, bo - t):.1f}" rx="2" fill="{col}"/>')
    ly = y(level)
    out.append(f'<line x1="{M}" x2="{w}" y1="{ly:.1f}" y2="{ly:.1f}" stroke="{brand.AMBER}" stroke-width="3" stroke-dasharray="10 10"/>')
    # hand-drawn ring around the last candles near the level (slightly irregular, open stroke)
    cx, cy = M + (len(bars) - 3) * step, ly
    rnd = random.Random(len(lesson["id"]))
    pts = []
    for k in range(0, 360 + 30, 12):
        a = math.radians(k - 20)
        r = 1 + rnd.uniform(-.04, .04)
        pts.append((cx + math.cos(a) * 110 * r, cy + math.sin(a) * 70 * r))
    d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    out.append(f'<path d="{d}" fill="none" stroke="{brand.AMBER}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="overflow:visible">{"".join(out)}</svg>', ly, levels


CSS = """*{margin:0;padding:0;box-sizing:border-box}html,body{width:1080px;height:1920px;overflow:hidden}
body{background:var(--bg);color:var(--txt);font-family:ArmV,sans-serif;position:relative;-webkit-font-smoothing:antialiased}
.chip{position:absolute;left:72px;top:290px;display:flex;align-items:center;gap:16px;font-size:30px;font-weight:700;letter-spacing:.04em;color:var(--mut)}
.chip b{font-family:Mono;font-weight:800;color:var(--acc);letter-spacing:0}
.hd{position:absolute;left:72px;right:72px;top:350px;height:540px;display:flex;flex-direction:column;justify-content:center}
.hd div{font-weight:800;font-stretch:75%;line-height:1.08;letter-spacing:-.01em;white-space:nowrap}
.vis{position:absolute;left:0;right:0;top:930px;height:600px}
.tag{position:absolute;right:72px;display:flex;align-items:center;height:118px;padding:0 34px 0 30px;border-radius:14px;
 background:var(--acc);color:var(--onacc);font-weight:800;font-stretch:75%;font-size:92px;line-height:1;white-space:nowrap}
.tag::before{content:"";position:absolute;left:-26px;top:50%;margin-top:-26px;border:26px solid transparent;border-right-color:var(--acc);border-left:0}
.big{position:absolute;left:72px;right:72px;top:930px;font-weight:900;font-stretch:62.5%;line-height:.92;letter-spacing:-.02em;color:var(--acc);white-space:nowrap}
.paper .big{color:var(--txt)}
.myth{position:absolute;right:72px;top:900px;padding:10px 22px 8px;border:5px solid var(--acc);color:var(--acc);font-size:44px;font-weight:800;letter-spacing:.06em;transform:rotate(-6deg);z-index:2}
.paper .big::after{content:"";display:block;width:240px;height:16px;border-radius:8px;background:var(--acc);margin-top:22px}
.proof{position:absolute;left:72px;right:72px;bottom:400px;border-top:3px solid var(--txt)}
.proof div{padding:20px 0;border-bottom:2px solid var(--rule);font-size:40px;font-weight:600;line-height:1.3}
.proof div:last-child{color:var(--mut)}
.ft{position:absolute;left:72px;right:72px;top:1586px;display:flex;align-items:center;gap:18px}
.ft .ti{width:46px;height:56px;color:var(--txt)}.ft b{font-size:34px;font-weight:800;letter-spacing:-.01em}
.ft span{margin-left:auto;font-size:30px;font-weight:600;color:var(--mut)}"""

FIT = """<script>function fit(){
 const hd=document.querySelector('.hd');if(hd){let s=156;const ls=[...hd.children];
  const ok=()=>ls.every(l=>l.scrollWidth<=936)&&hd.scrollHeight<=540;
  const set=v=>ls.forEach(l=>l.style.fontSize=v+'px');set(s);while(s>96&&!ok()){s-=2;set(s);}
  if(!ok()){ls.forEach(l=>l.style.whiteSpace='normal');while(s>72&&!ok()){s-=2;set(s);}}}
 const bg=document.querySelector('.big');if(bg){let s=440;bg.style.fontSize=s+'px';while(s>200&&bg.scrollWidth>936){s-=8;bg.style.fontSize=s+'px';}}
 const t=document.querySelector('.tag');if(t){let s=92;while(s>48&&t.getBoundingClientRect().left<560){s-=4;t.style.fontSize=s+'px';t.style.height=(s*1.28)+'px';}}
}fit();document.fonts.ready.then(fit);</script>"""


def cover_html(lesson, dark=None):
    if dark is None:
        dark = lesson.get("n", 0) % 2 == 1
    num = _number(lesson)
    chip = f'<div class="chip"><b>{lesson["module"]:02d}</b>{brand.SERIES.get(lesson["module"], "")}</div>'
    if num:
        big, rows = num
        lines = [p.strip() for p in lesson["hook"].split("|") if p.strip()]
        head = "".join(f"<div>{esc(brand.nbsp(l))}</div>" for l in lines)
        myth = "<div class=\"myth\">ՄԻՖ</div>" if any(w in lesson["title"].lower() for w in ("միֆ", "երազանք")) else ""
        vis = (f'{myth}<div class="big">{esc(big)}</div>'
               f'<div class="proof">{"".join(f"<div>{esc(brand.nbsp(r))}</div>" for r in rows[:2])}</div>')
        hd_style = ' style="top:330px;height:540px"'
    else:
        lines = [p.strip() for p in lesson["hook"].split("|") if p.strip()]
        head = "".join(f"<div>{esc(brand.nbsp(l))}</div>" for l in lines)
        svg, ly, levels = _chart_svg(lesson, dark, h=600)
        vis = f'<div class="vis">{svg}<div class="tag" style="top:{ly - 59:.0f}px">{esc(_tag_text(lesson, levels))}</div></div>'
        hd_style = ""
    foot = (f'<div class="ft">{brand.logo("currentColor")}<b>TradeInvest</b><span>@armtradeinvest</span></div>')
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><style>{brand.font_css()}{CSS}</style></head>'
            f'<body class="{"ink" if dark else "paper"}" style="{brand.ground(dark)}">{chip}<div class="hd"{hd_style}>{head}</div>{vis}{foot}{FIT}</body></html>')
