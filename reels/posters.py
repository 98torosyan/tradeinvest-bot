"""Typographic posters (1080x1350 feed images), brand TI Rise. Tue/Thu/Sat/Sun 15:07 — the days without a carousel.
Three grounds rotate (ink, paper, amber) so the profile grid stays varied."""
import json
import os
import re

from . import brand
from .builder import ASSETS, esc
from .story_cards import MARK

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "posters.json")
DISCLAIMER = "Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ"
GROUNDS = [("#0B0B0C", "#F2EFE8", "#FF8A00", "#A3A09A"), ("#F2EFE8", "#0B0B0C", "#C25E00", "#5C5850"), ("#FF8A00", "#0B0B0C", "#0B0B0C", "#3A2A10")]


def load():
    return json.load(open(SRC, encoding="utf-8"))["posters"]


def _acc(s, a):
    return re.sub(r"\*([^*]+)\*", rf'<span style="color:{a}">\1</span>', esc(s))


def page(p, n):
    bg, fg, ac, mu = GROUNDS[n % 3]
    mark = MARK.replace('width="64" height="74"', 'width="44" height="51"')
    if bg == "#FF8A00":
        mark = mark.replace('fill="#FF8A00"', 'fill="#0B0B0C"').replace('fill="#F2EFE8"', 'fill="#0B0B0C"')
    elif bg == "#F2EFE8":
        mark = mark.replace('fill="#F2EFE8"', 'fill="#0B0B0C"')
    if p["type"] == "big":
        size = 250 if len(p["big"]) <= 4 else 150
        mid = (f'<div class="big" style="color:{ac if bg != "#FF8A00" else fg};font-size:{size}px">{esc(p["big"])}</div>'
               f'<div class="t">{esc(p["title"])}</div>')
    else:
        txt = p["text"]
        longest = max(len(w) for w in re.sub(r"[*«»]", "", txt).split())
        size = 118 if len(txt) <= 34 and longest <= 11 else (100 if longest <= 13 else 86)
        mid = (f'<div class="q" style="color:{ac}">“</div><div class="t" style="font-size:{size}px">{_acc(txt, ac if bg != "#FF8A00" else "#FFFFFF")}</div>')
    css = f"""*{{margin:0;box-sizing:border-box}}html,body{{width:1080px;height:1350px;overflow:hidden}}
body{{background:{bg};color:{fg};font-family:ArmV,ArmSans,sans-serif;position:relative}}
.top{{position:absolute;left:90px;right:90px;top:80px;display:flex;align-items:center;gap:16px;font-weight:800;font-size:34px}}
.top span{{color:{ac if bg != "#FF8A00" else fg};font-weight:500}}.top em{{margin-left:auto;font-style:normal;font-size:24px;letter-spacing:.2em;color:{mu}}}
.mid{{position:absolute;left:90px;right:90px;top:250px;bottom:250px;display:flex;flex-direction:column;justify-content:center}}
.q{{font-size:240px;line-height:.55;height:110px;font-weight:800}}
.t{{font-size:84px;line-height:1.1;font-weight:800;letter-spacing:-.02em;font-stretch:80%}}
.big{{font-family:Mono,monospace;font-weight:800;line-height:1;margin-bottom:34px}}
.w{{margin-top:40px;font-size:38px;line-height:1.4;color:{mu};font-weight:600}}
.ft{{position:absolute;left:90px;right:90px;bottom:80px;display:flex;font-size:26px;color:{mu};font-weight:600}}.ft span{{margin-left:auto}}
.ln{{position:absolute;left:90px;width:120px;height:8px;bottom:150px;background:{ac if bg != "#FF8A00" else fg}}}"""
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>{brand.font_css()}{css}</style></head><body>'
            f'<div class="top">{mark}<div>Trade<span>Invest</span></div><em>TRADING ACADEMY</em></div>'
            f'<div class="mid">{mid}<div class="w">{esc(p["why"])}</div></div><div class="ln"></div>'
            f'<div class="ft">@armtradeinvest<span>🔖 Պահիր</span></div></body></html>')


def caption(p):
    head = re.sub(r"\*", "", p.get("text") or f'{p["big"]} — {p["title"]}')
    return "\n".join([head, "", p["why"], "", "🔖 Պահիր՝ որպես հիշեցում (կամ դիր wallpaper)", "",
                      f"⚠️ {DISCLAIMER}։", "", "Թրեյդինգ հայերեն · թրեյդերի մտքեր · կարգապահություն",
                      "#tradingquotes #tradingmindset #discipline #թրեյդինգ #հայերեն #թրեյդինգհայերեն"])


def render(html, path):
    from playwright.sync_api import sync_playwright
    f = path + ".html"
    open(f, "w", encoding="utf-8").write(html)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(f"file://{f}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        pg.screenshot(path=path, type="jpeg", quality=93); b.close()
    return path
