"""Weekly 'The week on one page' carousel (JPEG slides, 1080x1350), brand system v2.
Cover slide -> lesson slides (3 lessons each, colour-coded by series) -> closing slide.
Everything important stays inside the 3:4 crop the profile grid shows (x 34-1046)."""
import datetime as dt
import os
import re

from .builder import ASSETS, MONTHS, esc, logo_svg
from .palettes import BRAND, css_vars, for_lesson

W, H = 1080, 1350
MAX_SLIDES = 10                  # Instagram limit


def _icon(name, size=46):
    p = os.path.join(ASSETS, "icons", f"{name}.svg")
    if not os.path.exists(p):
        return ""
    s = open(p, encoding="utf-8").read()
    return re.sub(r'width="24"\s*height="24"', f'width="{size}" height="{size}"', s).replace('stroke="currentColor"', 'stroke="var(--a2)"')


CSS = '''*{margin:0;padding:0;box-sizing:border-box}html,body{width:1080px;height:1350px;overflow:hidden}
body{background:var(--bg);color:var(--txt);font-family:ArmSans,sans-serif;position:relative;-webkit-font-smoothing:antialiased}
.glow{position:absolute;right:-420px;top:-300px;width:1200px;height:1200px;border-radius:50%;background:radial-gradient(circle,var(--blob1),transparent 62%)}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.03) 2px,transparent 2px),linear-gradient(90deg,rgba(255,255,255,.03) 2px,transparent 2px);
 background-size:120px 120px;-webkit-mask-image:linear-gradient(180deg,transparent 5%,#000 35%,#000 65%,transparent 95%)}
.top{position:absolute;left:86px;right:86px;top:70px;display:flex;align-items:center;gap:14px}
.top .logo{width:46px;height:46px;overflow:visible}.top b{font-size:28px;font-weight:800}
.top .pg{margin-left:auto;font-family:JBMono,ArmSans,monospace;font-size:26px;font-weight:700;color:var(--mut);letter-spacing:.06em}
.foot{position:absolute;left:86px;right:86px;bottom:64px;display:flex;align-items:center;font-size:28px;font-weight:600;color:var(--mut)}
.foot .sw{margin-left:auto;display:flex;align-items:center;gap:14px;color:var(--a2);font-weight:700}
.foot .sw i{width:16px;height:16px;border-right:4px solid currentColor;border-top:4px solid currentColor;transform:rotate(45deg)}
.edge{position:absolute;left:0;top:220px;bottom:220px;width:10px;background:var(--a)}
.cv,.end{position:absolute;left:96px;right:86px;top:170px;bottom:170px;display:flex;flex-direction:column;justify-content:center}
.ser{display:flex;align-items:center;gap:16px;font-size:34px;font-weight:700;color:var(--a2)}.ser i{width:16px;height:16px;border-radius:4px;background:var(--a)}
h1{margin-top:36px;font-size:124px;font-weight:800;line-height:1.04;letter-spacing:-.03em}h1 .acc{color:var(--a2)}
.end h1{margin-top:0;font-size:112px}
.meta{margin-top:44px;display:flex;align-items:center;gap:22px;font-size:34px;font-weight:600;color:var(--mut)}
.meta em{font-style:normal;color:var(--txt);font-weight:700}
.dots{margin-top:40px;display:flex;gap:12px}.dots span{width:46px;height:10px;border-radius:5px}
.list{position:absolute;left:86px;right:86px;top:160px;bottom:140px;display:flex;flex-direction:column;justify-content:center;gap:24px}
.it{position:relative;padding:32px 38px 32px 48px;border-radius:26px;background:rgba(255,255,255,.055);border:1.5px solid rgba(255,255,255,.10);overflow:hidden}
.it::before{content:"";position:absolute;left:0;top:0;bottom:0;width:8px;background:var(--c)}
.it .s{font-size:24px;font-weight:700;color:var(--c2)}
.it b{display:block;margin-top:8px;font-size:44px;font-weight:800;line-height:1.15;letter-spacing:-.01em}
.it p{margin-top:12px;font-size:30px;line-height:1.38;color:var(--p)}
.acts{margin-top:64px;display:flex;flex-direction:column;gap:22px}
.act{display:flex;align-items:center;gap:26px;font-size:38px;font-weight:700}
.act span{width:84px;height:84px;border-radius:22px;flex:none;display:flex;align-items:center;justify-content:center;
 background:rgba(var(--ar),.14);border:1.5px solid rgba(var(--ar),.4)}
'''


def _page(body, n, total, last=False):
    fonts = f"@font-face{{font-family:'JBMono';font-weight:700;src:url('file://{ASSETS}/fonts/jetbrains-mono-latin-700-normal.woff2')}}"
    top = (f'<div class="top">{logo_svg().replace("opacity:0", "opacity:1")}<b>TradeInvest</b>'
           f'<span class="pg">{n:02d} / {total:02d}</span></div>')
    foot = '<div class="foot">@armtradeinvest' + ('' if last else '<span class="sw">Սահեցրու<i></i></span>') + '</div>'
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>{fonts}{CSS}</style></head><body style="{css_vars(BRAND)}"><div class="glow"></div><div class="grid"></div>'
            f'{top}{body}{foot}</body></html>')


def _range(date_range):
    """'2026-10-11 → 2026-10-18' -> '11–18 հոկտեմբերի'; any other format is shown as it is."""
    m = re.findall(r"(\d{4})-(\d{2})-(\d{2})", date_range or "")
    if len(m) != 2:
        return date_range or ""
    a, b = (dt.date(*map(int, x)) for x in m)
    if a.month == b.month:
        return f"{a.day}–{b.day} {MONTHS[b.month - 1]}"
    return f"{a.day} {MONTHS[a.month - 1]} – {b.day} {MONTHS[b.month - 1]}"


def _item(l):
    p = for_lesson(l)
    return (f'<div class="it" style="--c:{p["a"]};--c2:{p["a2"]}"><div class="s">{esc(l.get("series") or "")}</div>'
            f'<b>{esc(l["title"])}</b><p>{esc(l["summary"])}</p></div>')


def slides(lessons, palette=None, date_range=""):
    per = 3
    lessons = lessons[-(MAX_SLIDES - 2) * per:]                 # newest lessons win if the week was very full
    groups = [lessons[i:i + per] for i in range(0, len(lessons), per)]
    total = len(groups) + 2
    series = []
    for l in lessons:
        if l.get("module") not in series:
            series.append(l.get("module"))
    dots = "".join(f'<span style="background:{for_lesson({"module": m})["a"]}"></span>' for m in series)
    cover = (f'<div class="edge"></div><div class="cv"><div class="ser"><i></i>Շաբաթվա ամփոփում</div>'
             f'<h1>Շաբաթը<br><span class="acc">մեկ էջով</span></h1>'
             f'<div class="meta"><em>{esc(_range(date_range))}</em><span>·</span><span>{len(lessons)} դաս</span></div>'
             f'<div class="dots">{dots}</div></div>')
    out = [_page(cover, 1, total)]
    for k, g in enumerate(groups, 2):
        out.append(_page(f'<div class="list">{"".join(_item(l) for l in g)}</div>', k, total))
    end = ('<div class="edge"></div><div class="end"><h1>Պահիր։<br>Կրկնիր։<br><span class="acc">Կիսվիր։</span></h1><div class="acts">'
           f'<div class="act"><span>{_icon("book")}</span>Պահիր այս ամփոփումը</div>'
           f'<div class="act"><span>{_icon("users")}</span>Ուղարկիր ընկերոջդ</div>'
           f'<div class="act"><span>{_icon("school")}</span>Ամբողջ դասընթացը՝ bio-ի հղումով</div></div></div>')
    out.append(_page(end, total, total, last=True))
    return out


def render(pages, out_dir):
    from playwright.sync_api import sync_playwright
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        for i, h in enumerate(pages):
            f = os.path.join(out_dir, f"page{i}.html"); open(f, "w", encoding="utf-8").write(h)
            pg.goto(f"file://{f}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(200)
            img = os.path.join(out_dir, f"slide{i}.jpg"); pg.screenshot(path=img, type="jpeg", quality=92); paths.append(img)
        b.close()
    return paths
