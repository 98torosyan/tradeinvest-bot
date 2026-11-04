"""Economic calendar Stories: Monday «Շաբաթվա կարևոր իրադարձությունները» and «Այսօր» on event days.
Source: the public weekly calendar feed (high-impact USD events only), times converted to Yerevan."""
import datetime as dt
from zoneinfo import ZoneInfo

import requests

from .builder import esc
from .story_cards import _page, DISCLAIMER

FEED = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
YVN = ZoneInfo("Asia/Yerevan")
DAYS_HY = ["Երկ", "Երք", "Չրք", "Հնգ", "Ուրբ", "Շբթ", "Կիր"]
NAMES = [("FOMC Press", "Ֆեդի մամուլի ասուլիս"), ("Federal Funds Rate", "ԱՄՆ տոկոսադրույք (FOMC)"), ("FOMC Statement", "ԱՄՆ տոկոսադրույք (FOMC)"),
         ("Non-Farm", "Աշխատատեղեր (NFP)"), ("Unemployment Rate", "Գործազրկություն"), ("Unemployment Claims", "Գործազրկության հայտեր"),
         ("Core PCE", "PCE գնաճ"), ("CPI", "Գնաճ (CPI)"), ("PPI", "Արտադրողի գներ (PPI)"), ("GDP", "ՀՆԱ (GDP)"),
         ("Retail Sales", "Մանրածախ վաճառք"), ("ISM", "ISM PMI"), ("JOLTS", "JOLTS աշխատատեղեր"), ("Fed Chair", "Ֆեդի նախագահի ելույթ"),
         ("FOMC Meeting Minutes", "FOMC արձանագրություն")]


def _name(title):
    for k, v in NAMES:
        if k.lower() in title.lower():
            return v
    return title


def events():
    """High-impact USD events this week, merged by (time, name), as Yerevan datetimes."""
    rows = requests.get(FEED, timeout=25, headers={"User-Agent": "Mozilla/5.0"}).json()
    out = {}
    for r in rows:
        if r.get("country") != "USD" or r.get("impact") != "High":
            continue
        try:
            t = dt.datetime.fromisoformat(r["date"]).astimezone(YVN)
        except (KeyError, ValueError):
            continue
        n = _name(r.get("title", ""))
        out[(t, n)] = {"t": t, "name": n}
    return sorted(out.values(), key=lambda e: e["t"])


def _rows(evs, with_day=True):
    return "".join(f'<div class="r">{esc(e["name"])}<span>{(DAYS_HY[e["t"].weekday()] + " ") if with_day else ""}{e["t"]:%H:%M}</span></div>' for e in evs)


def week_page(evs):
    body = ('<div class="k"><i></i>ՏՆՏԵՍԱԿԱՆ ՕՐԱՑՈՒՅՑ · ԵՐԵՎԱՆԻ ԺԱՄՈՎ</div>'
            '<h1 style="top:480px">Շաբաթվա <b>կարևոր</b> իրադարձությունները</h1>'
            f'<div class="rows" style="top:{760 if len(evs) <= 8 else 720}px">{_rows(evs[:10])}</div>'
            '<div class="cta">Այս ժամերին շարժումը կարող է կտրուկ լինել։ Պլանավորիր ռիսկը։</div>'
            f'<div class="foot">{DISCLAIMER}</div>')
    return _page(body)


def today_page(evs):
    body = ('<div class="k"><i></i>ԱՅՍՕՐ · ԵՐԵՎԱՆԻ ԺԱՄՈՎ</div>'
            '<h1 style="top:480px">Այսօր շուկան կարող է <b>կտրուկ</b> շարժվել</h1>'
            f'<div class="rows" style="top:820px">{_rows(evs, with_day=False)}</div>'
            '<div class="cta">Լուրից առաջ՝ փոքր ռիսկ կամ դադար։ Stop-ը՝ պարտադիր։</div>'
            f'<div class="foot">{DISCLAIMER}</div>')
    return _page(body)


def plan(now):
    """('week', events) on Monday, ('today', events) on other event days, or (None, [])."""
    evs = events()
    if now.weekday() == 0:
        return ("week", evs) if evs else (None, [])
    today = [e for e in evs if e["t"].date() == now.date() and e["t"] > now]
    return ("today", today) if today else (None, [])
