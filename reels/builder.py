"""Turns a content spec (dict) into a self-contained HTML composition.
Every frame of the page is a pure function of time (window.seek(t)),
so reels/render.py can screenshot it frame by frame."""
import html as _html
import os
import random

from .palettes import css_vars

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
RATE = 0.30  # seconds on screen per word (reading pace)

ICONS = {
 "building": '<path d="M14 46 L60 18 L106 46 Z"/><path d="M22 52 H98"/><path d="M32 58 V92"/><path d="M52 58 V92"/><path d="M68 58 V92"/><path d="M88 58 V92"/><path d="M14 100 H106"/>',
 "shift": '<path d="M14 88 C44 88 44 36 76 36 H104"/><path d="M90 22 L104 36 L90 50"/><circle cx="14" cy="88" r="6"/>',
 "wallet": '<path d="M20 40 H96 a8 8 0 0 1 8 8 V94 a8 8 0 0 1 -8 8 H28 a8 8 0 0 1 -8 -8 Z"/><path d="M20 48 V34 a8 8 0 0 1 8 -8 H86"/><path d="M104 60 H84 a10 10 0 0 0 0 20 H104"/>',
 "card": '<rect x="12" y="28" width="96" height="64" rx="10"/><path d="M12 46 H108"/><path d="M26 76 H56"/>',
 "pie": '<circle cx="60" cy="60" r="44"/><path d="M60 16 V60 H104"/>',
 "bridge": '<path d="M8 74 Q60 14 112 74"/><path d="M8 74 H112"/><path d="M34 52 V74"/><path d="M60 44 V74"/><path d="M86 52 V74"/><path d="M8 96 H112"/>',
 "bulb": '<path d="M42 84 C28 74 24 60 26 50 C30 30 46 20 60 20 C74 20 90 30 94 50 C96 60 92 74 78 84 Z"/><path d="M46 96 H74"/><path d="M50 106 H70"/>',
 "shield": '<path d="M60 12 L100 26 V58 C100 84 82 100 60 108 C38 100 20 84 20 58 V26 Z"/><path d="M60 40 V66"/><path d="M60 80 V82"/>',
 "clock": '<circle cx="60" cy="60" r="44"/><path d="M60 32 V60 L80 72"/>',
 "key": '<circle cx="38" cy="60" r="20"/><path d="M58 60 H108"/><path d="M92 60 V76"/><path d="M104 60 V72"/>',
 "lock": '<rect x="24" y="52" width="72" height="54" rx="10"/><path d="M38 52 V38 a22 22 0 0 1 44 0 V52"/><path d="M60 72 V86"/>',
 "chain": '<rect x="10" y="44" width="40" height="32" rx="8"/><rect x="70" y="44" width="40" height="32" rx="8"/><path d="M50 60 H70"/>',
 "globe": '<circle cx="60" cy="60" r="44"/><path d="M16 60 H104"/><path d="M60 16 C40 40 40 80 60 104"/><path d="M60 16 C80 40 80 80 60 104"/>',
 "users": '<circle cx="44" cy="44" r="16"/><path d="M14 100 C14 78 28 68 44 68 C60 68 74 78 74 100"/><circle cx="84" cy="48" r="12"/><path d="M80 70 C96 70 106 80 106 98"/>',
 "doc": '<path d="M28 12 H74 L94 32 V108 H28 Z"/><path d="M74 12 V32 H94"/><path d="M42 58 H80"/><path d="M42 74 H80"/><path d="M42 90 H66"/>',
 "scale": '<path d="M60 16 V100"/><path d="M36 100 H84"/><path d="M22 34 H98"/><path d="M22 34 L10 64 H34 Z"/><path d="M98 34 L86 64 H110 Z"/>',
 "eye": '<path d="M8 60 C28 30 92 30 112 60 C92 90 28 90 8 60 Z"/><circle cx="60" cy="60" r="16"/>',
 "percent": '<circle cx="34" cy="34" r="14"/><circle cx="86" cy="86" r="14"/><path d="M94 22 L26 98"/>',
 "stack": '<path d="M60 16 L106 38 L60 60 L14 38 Z"/><path d="M14 60 L60 82 L106 60"/><path d="M14 82 L60 104 L106 82"/>',
 "phone": '<rect x="34" y="10" width="52" height="100" rx="10"/><path d="M52 94 H68"/>',
 "alert": '<path d="M60 14 L110 102 H10 Z"/><path d="M60 46 V72"/><path d="M60 86 V88"/>',
 "chart": '<path d="M14 100 H106"/><path d="M14 100 V16"/><path d="M26 84 L50 60 L68 72 L100 34"/>',
}
DEFAULT_ICON = "bulb"
MONTHS = ["հունվարի", "փետրվարի", "մարտի", "ապրիլի", "մայիսի", "հունիսի", "հուլիսի",
          "օգոստոսի", "սեպտեմբերի", "հոկտեմբերի", "նոյեմբերի", "դեկտեմբերի"]


def arm_date(d):
    return f"{d.day} {MONTHS[d.month - 1]}"


def esc(s):
    return _html.escape(str(s), quote=False)


def split_lines(text, maxc):
    """Greedy word wrap by character count (used for the line-reveal effect)."""
    lines, cur = [], ""
    for w in str(text).split():
        if cur and len(cur) + 1 + len(w) > maxc:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def icon(name, at=.3):
    body = ICONS.get(name, ICONS[DEFAULT_ICON]).replace("/>", f' data-fx="draw" data-at="{at}" data-dur="1.2"/>')
    return f'<svg class="icon" viewBox="0 0 120 120">{body}</svg>'


def lines(ls, at=0, cls="h1", dur=1.0):
    inner = "".join(f'<span class="clip"><span class="ln">{esc(l)}</span></span>' for l in ls)
    return f'<div class="{cls}" data-fx="lines" data-at="{at:.2f}" data-dur="{dur}">{inner}</div>'


def words(text, at, cls="p"):
    ws = str(text).split()
    inner = " ".join(f'<span class="w">{esc(w)}</span>' for w in ws)
    return f'<p class="{cls}" data-fx="words" data-at="{at:.2f}" data-rate="{RATE}">{inner}</p>', at + len(ws) * RATE


def fx(tag, cls, text, f="rise", at=0.0, dur=.7, extra=""):
    return f'<{tag} class="{cls}" data-fx="{f}" data-at="{at:.2f}" data-dur="{dur}" {extra}>{text}</{tag}>'


def paras(ps, start):
    out, t = "", start
    for p in ps:
        h, t = words(p["text"], t, "p em" if p.get("em") else "p")
        out += h; t += .45
    return out, t


class Timeline:
    def __init__(self):
        self.t = 0.0; self.scenes = []

    def add(self, html, length, cls=""):
        a = self.t; b = a + length
        self.scenes.append(f'<section class="scene {cls}" data-in="{a:.2f}" data-out="{b:.2f}">{html}</section>')
        self.t = b
        return a


LOGO_U, LOGO_G, LOGO_R = 100, 18, 22


def logo_svg():
    S = LOGO_U + LOGO_G; W = 3 * LOGO_U + 2 * LOGO_G
    blocks = [(0, 0, False), (S, 0, False), (S, S, False), (S, 2 * S, False), (2 * S, 0, True)]
    rects = ""
    for i, (x, y, acc) in enumerate(blocks):
        fill = "url(#lg)" if acc else "var(--txt)"
        lift = ' data-lift="1"' if acc else ""
        rects += f'<rect data-i="{i}"{lift} x="{x}" y="{y}" width="{LOGO_U}" height="{LOGO_U}" rx="{LOGO_R}" style="fill:{fill};opacity:0"/>'
    return (f'<svg class="logo" viewBox="-10 -44 {W + 20} {W + 54}"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" style="stop-color:var(--a2)"/><stop offset="1" style="stop-color:var(--a)"/></linearGradient></defs>{rects}</svg>')


def outro(tl, tag, cta=""):
    o = .7 if cta else 0.0
    h = (fx("div", "cta", esc(cta), "rise", 0, .9) if cta else "") + logo_svg()
    h += fx("div", "name", "TradeInvest", "rise", 1.5 + o, .8) + fx("div", "tag", esc(tag), "rise", 1.8 + o, .8)
    h += fx("div", "handle", "@armtradeinvest", "pop", 2.2 + o, .8)
    start = tl.add(h, 5.0 + o, "outro")
    return start + o + .15


AMBIENT_HOOK = '''HOOKS.push(t=>{
 const B=[['b1',-200,200,160,120,.11],['b2',500,900,180,140,.09],['b3',100,1300,140,160,.13]];
 for(const [id,x,y,ax,ay,f] of B){const e=document.getElementById(id);e.style.transform=`translate(${x+ax*Math.sin(t*f*2)}px,${y+ay*Math.cos(t*f*1.6)}px)`;}
 document.querySelectorAll('.pt').forEach((p,i)=>{const s=+p.dataset.s,r=+p.dataset.r;const y=((+p.dataset.y-t*40*s)%2000+2000)%2000-40;
  const x=+p.dataset.x+Math.sin(t*.6*s+i)*30;p.style.width=p.style.height=r+'px';p.style.transform=`translate(${x}px,${y}px)`;
  p.style.opacity=(+p.dataset.o)*(.6+.4*Math.sin(t*1.3+i));});
 const g=document.getElementById('grid');if(g)g.style.transform=`translateY(${(t*18)%120}px)`;});'''


def ambient(kind, seed):
    rnd = random.Random(seed)
    pts = "".join(f'<div class="pt" data-x="{rnd.uniform(0,1080):.0f}" data-y="{rnd.uniform(0,1920):.0f}" data-s="{rnd.uniform(.4,1.2):.2f}" '
                  f'data-r="{rnd.uniform(3,7):.1f}" data-o="{rnd.uniform(.15,.5):.2f}"></div>' for _ in range(28))
    grid = '<div class="gridlines" id="grid"></div>' if kind == "news" else ""
    return f'<div class="blob b1" id="b1"></div><div class="blob b2" id="b2"></div><div class="blob b3" id="b3"></div>{grid}<div>{pts}</div>'


def page(kind, palette, tl, persistent, hooks, seed=1, transparent=False):
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8">'
            f'<link rel="stylesheet" href="{ASSETS}/fonts.css"><link rel="stylesheet" href="{ASSETS}/styles.css"></head>'
            f'<body class="{kind}{" footage" if transparent else ""}" style="{css_vars(palette)}">{ambient(kind, seed)}{persistent}{"".join(tl.scenes)}'
            f'<script src="{ASSETS}/engine.js"></script><script>window.DURATION={tl.t:.2f};{AMBIENT_HOOK}{hooks}setupReel();</script></body></html>')


def build_news(spec, palette, date_label, footage=False):
    tl = Timeline()
    hl = split_lines(spec["headline"], 15)
    h = lines(hl, .3); t = .3 + len(hl) * .14 + 1.0
    if spec.get("sub"):
        s, t = words(spec["sub"], t, "who"); h += s
    big = spec.get("big")
    if big and isinstance(big.get("value"), (int, float)):
        big = dict(big)
        if not str(big.get("suffix", "")).strip():
            if abs(big["value"]) >= 1e9:
                big["value"], big["suffix"] = round(big["value"] / 1e9, 1), " մլրդ"
            elif abs(big["value"]) >= 1e6:
                big["value"], big["suffix"] = round(big["value"] / 1e6, 1), " մլն"
        dec = 0 if float(big["value"]).is_integer() else 1
        shown = f'{big.get("prefix", "")}{big["value"]:,.{dec}f}{big.get("suffix", "")}'
        size = 220 if len(shown) <= 7 else 170 if len(shown) <= 10 else 130
        h += fx("div", "big grad", "0", "count", t, 1.6,
                f'style="font-size:{size}px" data-grp="1" data-from="0" data-to="{big["value"]}" data-dec="{dec}" data-pre="{esc(big.get("prefix",""))}" data-post="{esc(big.get("suffix",""))}"')
        t += 1.6
    tl.add(h, t + 1.8)
    for n, st in enumerate(spec["steps"], 1):
        h = f'<div class="top">{fx("div", "num grad", str(n), "rise", 0, .8)}{icon(st.get("icon"), .3)}</div>'
        tls = split_lines(st["title"], 19)
        h += lines(tls, .25, "h2", .9)
        ph, t = paras(st["paragraphs"], 1.3)
        h += f'<div class="card" data-fx="card" data-at=".9" data-dur=".8">{ph}</div>'
        tl.add(h, t + 1.9)
    end = tl.t
    logo_t = outro(tl, "Crypto լուրերը՝ հայերեն և պարզ")
    persistent = (f'<div class="rail"><i id="railfill"></i></div><div class="mast" id="mast"><span class="dot" id="live"></span>'
                  f'<span>Լուր</span><span class="date">{esc(date_label)}</span></div>')
    hooks = (f"logoFx({logo_t:.2f});HOOKS.push(t=>{{document.getElementById('railfill').style.transform=`scaleY(${{Math.min(1,t/{end:.2f})}})`;"
             f"document.getElementById('live').style.opacity=.4+.6*Math.abs(Math.cos(t*2.4));"
             f"const o=1-EASE.inOut(prog(t,{end:.2f}-.5,.5));document.getElementById('mast').style.opacity=Math.min(o,EASE.out(prog(t,0,.7)));"
             f"document.querySelector('.rail').style.opacity=o;}});")
    return page("news", palette, tl, persistent, hooks, seed=len(spec["headline"]), transparent=footage)


def build_lesson(spec, palette):
    tl = Timeline()
    tl.add(lines(split_lines(spec["title"], 13), .3, "t1", 1.1), 4.4)
    numbered = spec.get("numbered", False)
    for n, st in enumerate(spec["steps"], 1):
        head = (fx("div", "ord", str(n), "pop", 0, .9) if numbered else "") + icon(st.get("icon"), .4)
        h = f'<div class="head">{head}</div>' + lines(split_lines(st["title"], 18), .4, "t2", .9)
        start = 1.3
        if st.get("quote"):
            h += (f'<div class="quote" data-fx="rise" data-at="1.3" data-dur=".8">«{esc(st["quote"])}»'
                  f'<div class="strike" data-fx="scalex" data-at="2.5" data-dur=".7"></div></div>')
            start = 3.2
        ph, t = paras(st["paragraphs"], start + .4)
        h += f'<div class="card" data-fx="card" data-at="{start:.2f}" data-dur=".8">{ph}</div>'
        tl.add(h, t + 2.0)
    end = tl.t
    logo_t = outro(tl, "Crypto-ն հայերեն և պարզ", spec.get("cta", "Պահիր այս դասը"))
    if "level" in spec:
        pill = f'Մակարդակ {spec["level"]}՝ {spec["level_name"]}'
        prog_line = f'<div class="progress">Դաս {spec["n"]} / {spec["total"]}</div>'
    else:
        pill, prog_line = spec.get("series", ""), ""
    persistent = f'<div class="series" id="series"><span>{esc(pill)}</span>{prog_line}</div>'
    hooks = (f"logoFx({logo_t:.2f});HOOKS.push(t=>{{const o=1-EASE.inOut(prog(t,{end:.2f}-.5,.5));"
             f"document.getElementById('series').style.opacity=Math.min(o,EASE.out(prog(t,0,.7)));}});")
    return page("lesson", palette, tl, persistent, hooks, seed=len(spec["title"]))


# ---------------- Market Story ----------------
ASSET_LABEL = {"BTC": ("BTC", "Bitcoin"), "ETH": ("ETH", "Ethereum"), "GOLD": ("XAU", "Ոսկի"), "SPX": ("S&P", "S&P 500")}
MOOD = {"bull": ("Bullish", "Crypto շուկայում գերակշռում է աճի տրամադրությունը", "#3DDC97"),
        "bear": ("Bearish", "Crypto շուկայում գերակշռում է անկման տրամադրությունը", "#FF6B6B"),
        "neutral": ("Neutral", "Crypto շուկան հիմա չեզոք է, հստակ ուղղություն չկա", "#F4C95D")}


def fmt_price(asset, v):
    if asset == "SPX":
        return f"{v:,.0f}"
    return f"${v:,.0f}" if v >= 100 else f"${v:,.2f}"


def sparkline(closes, w=240, h=90):
    if not closes or len(closes) < 2:
        return ""
    lo, hi = min(closes), max(closes)
    rng = (hi - lo) or 1
    pts = [(i * w / (len(closes) - 1), h - (c - lo) / rng * (h - 10) - 5) for i, c in enumerate(closes)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    up = closes[-1] >= closes[0]
    return (f'<svg class="spark" viewBox="0 0 {w} {h}"><path d="{d}" class="{"up" if up else "down"}" '
            f'data-fx="draw" data-at="{{at}}" data-dur="1.4"/></svg>')


def build_story(spec, palette, date_label):
    tl = Timeline()
    rows_html = ""
    order = [a for a in ("BTC", "ETH", "GOLD", "SPX") if a in spec["rows"]]
    for i, a in enumerate(order):
        r = spec["rows"][a]; at = 1.0 + i * 0.45
        sym, name = ASSET_LABEL[a]
        chg = r["chg24"]; cls = "up" if chg >= 0 else "down"; arrow = "▲" if chg >= 0 else "▼"
        note = '<span class="note">վերջին փակում</span>' if a == "SPX" else ""
        rows_html += (f'<div class="row" data-fx="rise" data-at="{at:.2f}" data-dur=".7">'
                      f'<div class="sym">{sym}</div><div class="nm">{esc(name)}{note}</div>'
                      f'{sparkline(r.get("closes")).replace("{at}", f"{at + .3:.2f}")}'
                      f'<div class="val"><div class="pr">{fmt_price(a, r["price"])}</div>'
                      f'<div class="ch {cls}">{arrow} {abs(chg):.1f}%</div></div></div>')
    head = (fx("div", "mh1", "Շուկան այսօր", "rise", .1, .8) + fx("div", "mdate", esc(date_label), "rise", .3, .8))
    fng = spec.get("fng")
    fng_html = ""
    if fng is not None:
        fng_html = (f'<div class="fng" data-fx="rise" data-at="3.2" data-dur=".7"><div class="fl">Fear &amp; Greed</div>'
                    f'<div class="fbar"><i data-fx="scalex" data-at="3.5" data-dur="1.4" style="width:{fng}%"></i></div>'
                    f'<div class="fv" data-fx="count" data-at="3.5" data-dur="1.4" data-from="0" data-to="{fng}">0</div></div>')
    label, expl, color = MOOD[spec["mood"]]
    mood_html = (f'<div class="mood" data-fx="pop" data-at="5.4" data-dur=".9" style="--mc:{color}">'
                 f'<div class="ml">{label}</div><div class="me">{esc(expl)}</div></div>'
                 f'<div class="disc" data-fx="fade" data-at="6.4" data-dur=".8">Հիմնված է BTC-ի և ETH-ի 24 ժամվա և 7 օրվա շարժման, '
                 f'ինչպես նաև Fear &amp; Greed ինդեքսի վրա։ Կանխատեսում կամ ֆինանսական խորհուրդ չէ։</div>')
    tl.add(f'<div class="mstack">{head}<div class="rows">{rows_html}</div>{fng_html}{mood_html}</div>', 15.0, "mscene")
    logo = f'<div class="mlogo">{logo_svg()}<span>TradeInvest</span></div>'
    hooks = "logoFx(0.2);"
    return page("market", palette, tl, logo, hooks, seed=7)


# ---------------- "Bitcoin 24 ժամում" candle Story ----------------
def _hhmm(ts):
    import datetime as _dt
    from zoneinfo import ZoneInfo
    return _dt.datetime.fromtimestamp(ts, ZoneInfo("Asia/Yerevan")).strftime("%H:%M")


def build_chart_story(spec, palette, date_label):
    cs = spec["candles"]; n = len(cs)
    W, H, PAD = 940, 760, 30
    lo = min(c["l"] for c in cs); hi = max(c["h"] for c in cs); rng = (hi - lo) or 1
    y = lambda v: PAD + (hi - v) / rng * (H - 2 * PAD)
    step = W / n; bw = step * .62
    candles = ""
    for i, c in enumerate(cs):
        x = i * step + step / 2; up = c["c"] >= c["o"]; col = "#3DDC97" if up else "#FF6B6B"
        top, bot = y(max(c["o"], c["c"])), y(min(c["o"], c["c"]))
        candles += (f'<g class="cd" data-i="{i}" style="opacity:0">'
                    f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(c["h"]):.1f}" y2="{y(c["l"]):.1f}" stroke="{col}" stroke-width="4"/>'
                    f'<rect x="{x - bw / 2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(4, bot - top):.1f}" rx="3" fill="{col}"/></g>')
    bi = next(i for i, c in enumerate(cs) if c["t"] == spec["big_t"])
    bx = bi * step + step / 2
    marks = (f'<line class="mk" x1="0" x2="{W}" y1="{y(spec["high"]):.1f}" y2="{y(spec["high"]):.1f}" stroke="var(--txt)" stroke-dasharray="8 10" stroke-width="2" data-fx="fade" data-at="6.0" data-dur=".6"/>'
             f'<line class="mk" x1="0" x2="{W}" y1="{y(spec["low"]):.1f}" y2="{y(spec["low"]):.1f}" stroke="var(--txt)" stroke-dasharray="8 10" stroke-width="2" data-fx="fade" data-at="7.0" data-dur=".6"/>'
             f'<rect x="{bx - step * .75:.1f}" y="4" width="{step * 1.5:.1f}" height="{H - 8}" rx="12" fill="none" stroke="var(--a2)" stroke-width="4" data-fx="fade" data-at="8.2" data-dur=".6"/>')
    chg = spec["chg"]; cls = "up" if chg >= 0 else "down"; arrow = "▲" if chg >= 0 else "▼"
    bp = spec["big_pct"]
    head = (fx("div", "mh1", "Bitcoin 24 ժամում", "rise", .1, .8) + fx("div", "mdate", esc(date_label), "rise", .3, .8)
            + f'<div class="cprice"><span data-fx="count" data-at=".6" data-dur="1.4" data-from="{spec["price"] * .98:.0f}" '
              f'data-to="{spec["price"]:.0f}" data-grp="1" data-pre="$">0</span>'
              f'<span class="ch {cls}" data-fx="pop" data-at="1.4" data-dur=".7">{arrow} {abs(chg):.1f}%</span></div>')
    chart = f'<svg class="cchart" viewBox="0 0 {W} {H}">{candles}{marks}</svg>'
    info = (f'<div class="cinfo">'
            f'<div data-fx="rise" data-at="6.1" data-dur=".6"><b>Առավելագույն</b><span>${spec["high"]:,.0f} · {_hhmm(spec["high_t"])}</span></div>'
            f'<div data-fx="rise" data-at="7.1" data-dur=".6"><b>Նվազագույն</b><span>${spec["low"]:,.0f} · {_hhmm(spec["low_t"])}</span></div>'
            f'<div data-fx="rise" data-at="8.3" data-dur=".6"><b>Ամենամեծ ժամային շարժումը</b>'
            f'<span>{_hhmm(spec["big_t"])}-ին՝ {"+" if bp >= 0 else "−"}{abs(bp):.1f}%</span></div></div>')
    tl = Timeline()
    brand = f'<div class="cbrand" data-fx="fade" data-at="9.0" data-dur=".8">{logo_svg()}<span>@armtradeinvest</span></div>'
    tl.add(f'<div class="mstack">{head}{chart}{info}{brand}</div>', 16.0, "mscene")
    logo = ""
    hooks = ("logoFx(9.0);HOOKS.push(t=>{document.querySelectorAll('.cd').forEach(g=>{"
             "const k=EASE.out(prog(t,1.6+(+g.dataset.i)*.17,.45));g.style.opacity=k;"
             "g.style.transform=`translateY(${(1-k)*30}px)`;});});")
    return page("market", palette, tl, logo, hooks, seed=11)


def teaser_overlay(palette, kind):
    """Transparent badge laid over the first seconds of a Reel for the Story teaser."""
    text = "Ամբողջ դասը՝ էջում" if kind == "lesson" else "Ամբողջ լուրը՝ էջում"
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>html,body{{margin:0;width:1080px;height:1920px;background:transparent;font-family:ArmSans,sans-serif}}'
            f'.b{{position:absolute;left:50%;top:1395px;transform:translateX(-50%);display:flex;align-items:center;gap:22px;'
            f'padding:26px 44px;border-radius:60px;background:linear-gradient(135deg,{palette["a2"]},{palette["a"]});'
            f'color:#0B1220;font-size:46px;font-weight:800;box-shadow:0 20px 60px rgba(0,0,0,.45);white-space:nowrap}}'
            f'.h{{position:absolute;left:0;right:0;top:1515px;text-align:center;color:#fff;font-size:34px;font-weight:700;'
            f'text-shadow:0 2px 12px rgba(0,0,0,.6)}}</style></head><body>'
            f'<div class="b"><svg width="44" height="44" viewBox="0 0 24 24"><path d="M12 20V5M5 11l7-7 7 7" fill="none" '
            f'stroke="#0B1220" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>{text}</div>'
            f'<div class="h">@armtradeinvest</div></body></html>')
