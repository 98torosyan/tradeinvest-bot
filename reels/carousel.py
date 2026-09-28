"""Weekly 'The week on one page' carousel (JPEG slides, 1080x1350)."""
import os

from .builder import ASSETS, esc
from .palettes import css_vars

W, H = 1080, 1350


def _page(body, palette):
    return f'''<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css"><style>
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{background:var(--bg);color:var(--txt);font-family:ArmSans,sans-serif;padding:90px 80px;display:flex;flex-direction:column;justify-content:center;gap:34px}}
.tag{{align-self:flex-start;font-size:32px;font-weight:700;color:var(--onacc);background:linear-gradient(135deg,var(--a2),var(--a));padding:12px 26px;border-radius:40px}}
h1{{font-family:ArmSerif,serif;font-size:96px;line-height:1.08}}p.s{{font-size:40px;color:var(--mut)}}
.it{{padding:30px 34px;border-radius:28px;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.12)}}
.it b{{display:block;font-size:44px;margin-bottom:10px;color:var(--a2)}}.it span{{font-size:34px;line-height:1.35}}
.cta{{font-size:52px;font-weight:800;line-height:1.3}}</style></head><body style="{css_vars(palette)}">{body}</body></html>'''


def slides(lessons, palette, date_range):
    out = [_page(f'<div class="tag">Շաբաթվա ամփոփում</div><h1>Շաբաթը<br>մեկ էջով</h1><p class="s">{esc(date_range)} · '
                 f'{len(lessons)} դաս</p>', palette)]
    for i in range(0, len(lessons), 3):
        items = "".join(f'<div class="it"><b>{esc(l["title"])}</b><span>{esc(l["summary"])}</span></div>' for l in lessons[i:i + 3])
        out.append(_page(items, palette))
    out.append(_page('<h1>Պահիր.<br>Կրկնիր.<br>Կիսվիր.</h1><p class="cta">📚 Ամբողջ դասընթացը՝ հղումը bio-ում</p>', palette))
    return out[:10]


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
