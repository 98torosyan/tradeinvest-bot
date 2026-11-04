"""Image Stories (1080x1920, brand TI Rise): «30 օր, 30 կանոն» challenge and big-move alerts.
Rendered with Playwright from HTML, published as STORIES images."""
import json
import os

from . import brand
from .builder import ASSETS, esc

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "challenge30.json")
DISCLAIMER = "Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ։"

MARK = ('<svg width="64" height="74" viewBox="-30 -136 426 496"><rect width="252" height="78" rx="16" fill="#F2EFE8"/>'
        '<rect x="84" width="84" height="340" rx="16" fill="#F2EFE8"/>'
        '<path d="M282 -22 L366 -96 L366 324 Q366 340 350 340 L298 340 Q282 340 282 324 Z" fill="#FF8A00"/></svg>')

CSS = """*{margin:0;box-sizing:border-box}html,body{width:1080px;height:1920px;overflow:hidden}
body{background:#0B0B0C;color:#F2EFE8;font-family:ArmV,ArmSans,sans-serif;position:relative}
.glow{position:absolute;right:-260px;top:120px;width:900px;height:900px;border-radius:50%;background:radial-gradient(circle,rgba(255,138,0,.17),transparent 65%)}
.top{position:absolute;left:90px;top:250px;display:flex;align-items:center;gap:22px;font-weight:800;font-size:44px}.top span{color:#FF8A00;font-weight:500}
.k{position:absolute;left:90px;top:420px;font-size:30px;font-weight:700;letter-spacing:.2em;color:#FF8A00}
.k i{display:inline-block;width:46px;height:4px;background:#FF8A00;vertical-align:middle;margin-right:18px}
.day{position:absolute;left:90px;top:480px;font-family:Mono,monospace;font-weight:800;font-size:230px;line-height:1;color:#FF8A00}
.day small{font-size:90px;color:#5C5850}
.bar{position:absolute;left:90px;right:90px;top:740px;height:12px;border-radius:6px;background:#1C1C1F}.bar i{display:block;height:100%;border-radius:6px;background:#FF8A00}
h1{position:absolute;left:90px;right:90px;top:820px;font-size:96px;line-height:1.06;font-weight:800;letter-spacing:-.02em;font-stretch:80%}h1 b{color:#FF8A00}
.p{position:absolute;left:90px;right:90px;top:1090px;font-size:46px;line-height:1.38;color:#D9D5CC}
.big{position:absolute;left:90px;top:480px;font-family:Mono,monospace;font-weight:800;font-size:200px;line-height:1}
.rows{position:absolute;left:90px;right:90px;top:990px}
.r{display:flex;justify-content:space-between;padding:24px 0;border-top:2px solid rgba(242,239,232,.12);font-size:40px;font-weight:600}
.r span{font-family:Mono,monospace;font-weight:800;color:#FFA640}
.cta{position:absolute;left:90px;right:90px;bottom:300px;background:#FF8A00;color:#0B0B0C;border-radius:30px;padding:40px 46px;font-size:46px;font-weight:800}
.foot{position:absolute;left:90px;right:90px;bottom:200px;font-size:26px;color:#A3A09A}"""


def _page(body):
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>{brand.font_css()}{CSS}</style></head><body><div class="glow"></div>'
            f'<div class="top">{MARK}<div>Trade<span>Invest</span></div></div>{body}</body></html>')


def _acc(s):
    import re
    return re.sub(r"\*([^*]+)\*", r"<b>\1</b>", esc(s))


def render(html, path):
    from playwright.sync_api import sync_playwright
    f = path + ".html"
    open(f, "w", encoding="utf-8").write(html)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(f"file://{f}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        pg.screenshot(path=path, type="jpeg", quality=92); b.close()
    return path


# ---------------------------------------------------------------- 30 days, 30 rules
def challenge_rules():
    return json.load(open(SRC, encoding="utf-8"))["rules"]


def challenge_page(day):
    rules = challenge_rules()
    r = rules[day - 1]
    body = (f'<div class="k"><i></i>ՉԵԼԵՆՋ · 30 ՕՐ, 30 ԿԱՆՈՆ</div>'
            f'<div class="day">{day:02d}<small>/{len(rules)}</small></div><div class="bar"><i style="width:{100 * day / len(rules):.1f}%"></i></div>'
            f'<h1>{_acc(r["title"])}</h1><div class="p">{esc(r["text"])}</div>'
            f'<div class="cta">Վաղը՝ կանոն {day + 1:02d} →</div>' if day < len(rules) else
            f'<div class="k"><i></i>ՉԵԼԵՆՋ · 30 ՕՐ, 30 ԿԱՆՈՆ</div>'
            f'<div class="day">{day:02d}<small>/{len(rules)}</small></div><div class="bar"><i style="width:100%"></i></div>'
            f'<h1>{_acc(r["title"])}</h1><div class="p">{esc(r["text"])}</div>'
            f'<div class="cta">Ավարտեցիր չելենջը 🎉 Գրիր DM «ԴԱՍ»</div>')
    return _page(body + f'<div class="foot">{DISCLAIMER}</div>')


# ---------------------------------------------------------------- big move alert
def alert_page(name, sym, pct, price, hi, lo, zone_txt, other_txt):
    up = pct >= 0
    color = "#34C98A" if up else "#F2505E"
    sign = "+" if up else "−"
    body = (f'<div class="k"><i></i>ԿԱՐԵՎՈՐ ՇԱՐԺՈՒՄ · 24 ԺԱՄ</div>'
            f'<div class="big" style="color:{color}">{sign}{abs(pct):.1f}%</div>'
            f'<h1 style="top:730px;font-size:84px">{esc(name)}՝ <b>{"կտրուկ աճ" if up else "կտրուկ անկում"}</b></h1>'
            f'<div class="rows"><div class="r">Գինը հիմա<span>{esc(price)}</span></div>'
            f'<div class="r">24ժ բարձր / ցածր<span>{esc(hi)} / {esc(lo)}</span></div>'
            f'<div class="r">Կարևոր գոտի<span>{esc(zone_txt)}</span></div>'
            f'<div class="r">Հաջորդ մակարդակ<span>{esc(other_txt)}</span></div></div>'
            f'<div class="cta">Մանրամասները՝ 19:07-ի վերլուծության մեջ</div>'
            f'<div class="foot">{DISCLAIMER} Սա կանխատեսում չէ։</div>')
    return _page(body)


# ---------------------------------------------------------------- daily 16:07 rotating Story: fact / term / number
FACTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "daily_facts.json")


def facts():
    return json.load(open(FACTS, encoding="utf-8"))


def fact_page(f):
    body = (f'<div class="k"><i></i>ԳԻՏԵ՞Ր</div><div class="day" style="font-size:{220 if len(f["big"]) <= 4 else 170}px">{esc(f["big"])}</div>'
            f'<h1 style="top:800px;font-size:64px;color:#A3A09A">{esc(f["when"])}</h1>'
            f'<div class="p" style="top:920px;font-size:58px;line-height:1.3;color:#F2EFE8;font-weight:700">{esc(f["text"])}</div>'
            f'<div class="cta">Ուղարկիր ընկերոջդ, ով սա չգիտեր 📤</div>')
    return _page(body)


def term_page(t, n, total):
    body = (f'<div class="k"><i></i>ԲԱՌԱՐԱՆ · {n:02d}/{total}</div>'
            f'<div class="day" style="font-size:{150 if len(t["en"]) <= 10 else 112}px;color:#F2EFE8">{esc(t["en"])}</div>'
            f'<h1 style="top:720px;color:#FF8A00">{esc(t["hy"])}</h1>'
            f'<div class="p" style="top:900px;font-size:56px;line-height:1.3;color:#F2EFE8;font-weight:600">{esc(t["text"])}</div>'
            f'<div class="cta">Պահիր բառարանը՝ ամեն օր նոր տերմին 🔖</div>')
    return _page(body)


def number_page(big, title, text, src):
    body = (f'<div class="k"><i></i>ՕՐՎԱ ԹԻՎԸ</div><div class="day" style="font-size:{230 if len(big) <= 4 else 170}px">{esc(big)}</div>'
            f'<h1 style="top:770px;font-size:76px">{_acc(title)}</h1>'
            f'<div class="p" style="top:1110px;font-size:42px">{esc(text)}</div>'
            f'<div class="cta">Ինչ ես կարծում՝ սա շատ է, թե քիչ։ Պատասխանիր 💬</div>'
            f'<div class="foot">Աղբյուր՝ {esc(src)}։ {DISCLAIMER}</div>')
    return _page(body)


def number_of_day(k):
    """Three live statistics from Binance BTC daily candles, rotated by k."""
    import requests
    rows = requests.get("https://data-api.binance.vision/api/v3/klines", params={"symbol": "BTCUSDT", "interval": "1d", "limit": 366}, timeout=25).json()[:-1]
    c = [float(r[4]) for r in rows]; o = [float(r[1]) for r in rows]; h = [float(r[2]) for r in rows]; lo = [float(r[3]) for r in rows]
    src = "Binance, BTC/USDT օրական գներ"
    if k % 3 == 0:
        g = sum(c[i] > o[i] for i in range(len(c) - 30, len(c)))
        return number_page(f"{g}/30", "Վերջին 30 օրից այսքանն է BTC-ն փակվել *կանաչ*",
                           "Նույնիսկ աճող շուկայում կարմիր օրերը շատ են։ Ահա թե ինչու է ամեն գործարքի համար պետք stop-loss։", src)
    if k % 3 == 1:
        top = max(h)
        d = (c[-1] / top - 1) * 100
        return number_page(f"{d:.0f}%", "Այսքան է BTC-ն հիմա հեռու *տարեկան գագաթից*",
                           f"Տարվա ամենաբարձր գինը՝ ${top:,.0f}, հիմա՝ ${c[-1]:,.0f}։ Գագաթից գնելը ամենաթանկ սխալներից է։".replace(",", " "), src)
    rng = sum((h[i] - lo[i]) / c[i - 1] * 100 for i in range(len(c) - 30, len(c))) / 30
    return number_page(f"{rng:.1f}%", "BTC-ի միջին *օրական* տատանումը վերջին 30 օրում",
                       "Եթե stop-ը դնում ես ավելի մոտ, քան օրական սովորական տատանումը, այն կարող է կպչել պատահաբար։", src)
