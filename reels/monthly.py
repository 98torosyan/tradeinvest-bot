"""Monthly infographic «Ամիսը մեկ նկարում» (1080x1350 feed post), published on the 1st for the previous month.
Real Binance daily candles: month change, high/low, green days, best/worst day and a daily-return heatmap calendar."""
import calendar
import datetime as dt

import requests

from . import brand
from .builder import ASSETS, esc
from .story_cards import MARK

MONTHS_HY = ["Հունվար", "Փետրվար", "Մարտ", "Ապրիլ", "Մայիս", "Հունիս", "Հուլիս", "Օգոստոս", "Սեպտեմբեր", "Հոկտեմբեր", "Նոյեմբեր", "Դեկտեմբեր"]
DISCLAIMER = "Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ"


def data(year, month, sym="BTCUSDT"):
    start = dt.datetime(year, month, 1, tzinfo=dt.timezone.utc)
    end = dt.datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=dt.timezone.utc)
    rows = requests.get("https://data-api.binance.vision/api/v3/klines", timeout=25, params={
        "symbol": sym, "interval": "1d", "startTime": int(start.timestamp() * 1000), "endTime": int(end.timestamp() * 1000) - 1, "limit": 40}).json()
    days = [{"d": dt.datetime.utcfromtimestamp(r[0] / 1000).day, "o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4])} for r in rows]
    for x in days:
        x["ret"] = (x["c"] / x["o"] - 1) * 100
    o, c = days[0]["o"], days[-1]["c"]
    return {"days": days, "open": o, "close": c, "pct": (c / o - 1) * 100, "high": max(x["h"] for x in days),
            "low": min(x["l"] for x in days), "green": sum(x["ret"] > 0 for x in days),
            "best": max(days, key=lambda x: x["ret"]), "worst": min(days, key=lambda x: x["ret"])}


def _money(v):
    return f"${v:,.0f}".replace(",", " ")


def page(year, month, D, name="Bitcoin"):
    first_wd = calendar.monthrange(year, month)[0]           # Monday = 0
    cells = ['<div class="cell e"></div>'] * first_wd
    m = max(abs(x["ret"]) for x in D["days"]) or 1
    for x in D["days"]:
        a = 0.18 + 0.82 * min(1, abs(x["ret"]) / m)
        col = f"rgba(52,201,138,{a:.2f})" if x["ret"] >= 0 else f"rgba(242,80,94,{a:.2f})"
        cells.append(f'<div class="cell" style="background:{col}"><b>{x["d"]}</b><span>{"+" if x["ret"] >= 0.05 else ("−" if x["ret"] <= -0.05 else "")}{abs(x["ret"]):.1f}</span></div>')
    up = D["pct"] >= 0
    css = """*{margin:0;box-sizing:border-box}html,body{width:1080px;height:1350px;overflow:hidden}
body{background:#0B0B0C;color:#F2EFE8;font-family:ArmV,ArmSans,sans-serif;position:relative;padding:70px 80px}
.top{display:flex;align-items:center;gap:16px;font-weight:800;font-size:32px}.top span{color:#FF8A00;font-weight:500}.top em{margin-left:auto;font-style:normal;font-size:24px;letter-spacing:.08em;color:#A3A09A}
h1{margin-top:44px;font-size:76px;line-height:1.02;font-weight:800;font-stretch:80%;letter-spacing:-.02em}h1 b{color:#FF8A00}
.kp{margin-top:34px;display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.k{background:#141416;border:1.5px solid rgba(242,239,232,.1);border-radius:18px;padding:20px 20px}
.k small{display:block;font-family:ArmV,sans-serif;font-size:21px;color:#A3A09A;font-weight:700;letter-spacing:.02em}.k b{display:block;margin-top:8px;font-family:Mono;font-size:34px;font-weight:800}
.wd{margin-top:34px;display:grid;grid-template-columns:repeat(7,1fr);gap:10px;font-size:20px;color:#A3A09A;font-weight:700;text-align:center}
.cal{margin-top:10px;display:grid;grid-template-columns:repeat(7,1fr);gap:10px}
.cell{height:92px;border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;justify-content:space-between}.cell.e{background:transparent}
.cell b{font-size:20px;font-weight:800;color:rgba(255,255,255,.85)}.cell span{font-family:Mono;font-size:22px;font-weight:800;text-align:right}
.ft{position:absolute;left:80px;right:80px;bottom:46px;display:flex;font-size:20px;color:#8E8A83}.ft span{margin-left:auto}"""
    wd = "".join(f"<div>{d}</div>" for d in ["Երկ", "Երք", "Չրք", "Հնգ", "Ուր", "Շբթ", "Կիր"])
    kp = (f'<div class="k"><small>ԱՄՍՎԱ ԱՐԴՅՈՒՆՔ</small><b style="color:{"#34C98A" if up else "#F2505E"}">{"+" if up else "−"}{abs(D["pct"]):.1f}%</b></div>'
          f'<div class="k"><small>ԲԱՐՁՐ / ՑԱԾՐ</small><b style="font-size:24px">{_money(D["high"])}<br>{_money(D["low"])}</b></div>'
          f'<div class="k"><small>ԿԱՆԱՉ ՕՐԵՐ</small><b>{D["green"]}/{len(D["days"])}</b></div>'
          f'<div class="k"><small>ԼԱՎ / ՎԱՏ ՕՐ</small><b style="font-size:24px"><span style="color:#34C98A">{D["best"]["d"]}՝ +{D["best"]["ret"]:.1f}%</span><br>'
          f'<span style="color:#F2505E">{D["worst"]["d"]}՝ −{abs(D["worst"]["ret"]):.1f}%</span></b></div>')
    small = MARK.replace('width="64" height="74"', 'width="40" height="46"')
    return (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css">'
            f'<style>{brand.font_css()}{css}</style></head><body>'
            f'<div class="top">{small}<div>Trade<span>Invest</span></div><em>{MONTHS_HY[month - 1].upper()} {year}</em></div>'
            f'<h1>{esc(name)}-ի {esc(MONTHS_HY[month - 1].lower())}ը<br><b>մեկ նկարում</b></h1><div class="kp">{kp}</div>'
            f'<div class="wd">{wd}</div><div class="cal">{"".join(cells)}</div>'
            f'<div class="ft">Օրական փոփոխություն, % (UTC)։ {DISCLAIMER}։<span>@armtradeinvest</span></div></body></html>')


def caption(year, month, D, name="Bitcoin"):
    up = D["pct"] >= 0
    return "\n".join([
        f"📅 {name}-ի {MONTHS_HY[month - 1].lower()}ը մեկ նկարում", "",
        f"{'🟢' if up else '🔴'} Ամսվա արդյունք՝ {'+' if up else '−'}{abs(D['pct']):.1f}%",
        f"📈 Բարձր՝ {_money(D['high'])} · 📉 Ցածր՝ {_money(D['low'])}",
        f"🟩 Կանաչ օրեր՝ {D['green']}/{len(D['days'])}",
        f"🏆 Լավագույն օր՝ {D['best']['d']} (+{D['best']['ret']:.1f}%) · Վատագույն՝ {D['worst']['d']} (−{abs(D['worst']['ret']):.1f}%)", "",
        "Նույնիսկ լավ ամսում կան կարմիր օրեր։ Ահա թե ինչու է կարևոր ռիսկի կառավարումը։", "",
        "💬 Ինչպե՞ս անցավ քո ամիսը։ Գրիր comment-ում",
        "🎓 Անվճար մինի դասընթաց և PDF՝ հղումը bio-ում", "",
        f"⚠️ {DISCLAIMER}։", "",
        "Bitcoin ամսական վիճակագրություն · crypto հայերեն · թրեյդինգ հայերեն",
        "#bitcoin #btc #crypto #monthlyrecap #հայերեն #թրեյդինգհայերեն"])
