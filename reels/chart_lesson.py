"""«Իրական chart դաս» — 35 s lesson Reel on a REAL chart (Remotion composition "ChartLesson").

One trading concept per day (rotation in TOPICS). The code scans real candles (BTC/ETH 4H, gold and indices 1D),
finds the most recent clear example of the pattern, and shows honestly what happened in the next K candles —
also when it did not work (that is a lesson too: stop loss). Nothing is invented: every level, date and % is computed here.
Scene plan: hook → concept (the real chart draws in) → the pattern marked on the chart → «ի՞նչ եղավ հետո» → rule + CTA."""
import datetime as dt
import json
import os
import shutil
import subprocess

import requests

from .analysis import ASSETS_INFO, DISCLAIMER, MOTION, UA, T, fmt

K = 10                     # candles shown after the signal («ի՞նչ եղավ հետո»)
BEFORE = 34                # candles shown before the signal
FPS = 30
SCAN_ASSETS = ["BTC", "ETH", "GOLD", "NDX", "SPX"]
TOPICS = ["sweep", "pinbar", "retest", "divergence", "engulfing", "double", "fvg", "ema"]


# ------------------------------------------------------------------ data (long history, with timestamps)
def _binance(sym, n=500):
    for base in ("https://data-api.binance.vision/api/v3", "https://api.binance.com/api/v3"):
        try:
            rows = requests.get(f"{base}/klines", params={"symbol": sym, "interval": "4h", "limit": n + 1}, headers=UA, timeout=T).json()
            cs = [{"t": int(r[0]) // 1000, "o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4])} for r in rows]
            return cs[:-1]                                   # drop the candle that is still forming
        except Exception as exc:  # noqa: BLE001
            print("[chart_lesson] binance", base, exc)
    raise RuntimeError("no crypto candles")


def _yahoo(sym):
    d = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}", params={"range": "2y", "interval": "1d"},
                     headers=UA, timeout=T).json()["chart"]["result"][0]
    q = d["indicators"]["quote"][0]
    return [{"t": int(t), "o": o, "h": h, "l": l, "c": c} for t, o, h, l, c in
            zip(d["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)][:-1]


def _stooq(sym):
    r = requests.get("https://stooq.com/q/d/l/", params={"s": sym, "i": "d"}, headers=UA, timeout=T)
    out = []
    for x in [l.split(",") for l in r.text.strip().splitlines()[1:] if l.count(",") >= 4][-500:]:
        t = int(dt.datetime.strptime(x[0], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
        out.append({"t": t, "o": float(x[1]), "h": float(x[2]), "l": float(x[3]), "c": float(x[4])})
    return out[:-1]


def candles(asset):
    src = ASSETS_INFO[asset]["src"]
    if src[0] == "binance":
        return _binance(src[1])
    try:
        cs = _yahoo(src[1])
        if len(cs) >= 120:
            return cs
    except Exception as exc:  # noqa: BLE001
        print("[chart_lesson] yahoo", asset, exc)
    return _stooq(src[2])


# ------------------------------------------------------------------ indicators
def ema(vals, n):
    k, out, e = 2 / (n + 1), [], None
    for v in vals:
        e = v if e is None else v * k + e * (1 - k)
        out.append(e)
    return out


def rsi(closes, n=14):
    out, ag, al = [50.0] * len(closes), None, None
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        g, l = max(ch, 0), max(-ch, 0)
        if i <= n:
            ag = (ag or 0) + g / n; al = (al or 0) + l / n
            continue
        ag = (ag * (n - 1) + g) / n; al = (al * (n - 1) + l) / n
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def atr(cs, n=14):
    trs = [cs[0]["h"] - cs[0]["l"]] + [max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"])) for p, c in zip(cs, cs[1:])]
    return ema(trs, n)


def _body(c):
    return abs(c["c"] - c["o"])


def _lowest(cs, a, b):
    return min(cs[j]["l"] for j in range(max(0, a), b))


def _highest(cs, a, b):
    return max(cs[j]["h"] for j in range(max(0, a), b))


# ------------------------------------------------------------------ detectors: yield (i, dir, marks)
# dir: +1 = bullish idea, −1 = bearish. Marks are drawn by the composition (indices are absolute here).
def d_pinbar(cs, A):
    for i in range(20, len(cs)):
        c = cs[i]; rng = c["h"] - c["l"]
        if rng < A[i] * 1.1:
            continue
        lw, uw = min(c["o"], c["c"]) - c["l"], c["h"] - max(c["o"], c["c"])
        if lw >= 0.6 * rng and lw >= 2.2 * _body(c) and c["l"] <= _lowest(cs, i - 12, i):
            yield i, 1, [{"type": "circle", "i": i, "at": "l"}]
        elif uw >= 0.6 * rng and uw >= 2.2 * _body(c) and c["h"] >= _highest(cs, i - 12, i):
            yield i, -1, [{"type": "circle", "i": i, "at": "h"}]


def d_engulfing(cs, A):
    for i in range(20, len(cs)):
        p, c = cs[i - 1], cs[i]
        if _body(c) < A[i] * 0.9 or _body(p) < A[i] * 0.2:
            continue
        if p["c"] < p["o"] and c["c"] > c["o"] and c["c"] >= p["o"] and c["o"] <= p["c"] and min(p["l"], c["l"]) <= _lowest(cs, i - 10, i - 1):
            yield i, 1, [{"type": "box", "i1": i - 1, "i2": i, "lo": min(p["l"], c["l"]), "hi": max(p["h"], c["h"])}]
        elif p["c"] > p["o"] and c["c"] < c["o"] and c["c"] <= p["o"] and c["o"] >= p["c"] and max(p["h"], c["h"]) >= _highest(cs, i - 10, i - 1):
            yield i, -1, [{"type": "box", "i1": i - 1, "i2": i, "lo": min(p["l"], c["l"]), "hi": max(p["h"], c["h"])}]


def _swing_lows(cs, a, b, w=3):
    return [j for j in range(max(a, w), min(b, len(cs) - w)) if cs[j]["l"] == min(x["l"] for x in cs[j - w:j + w + 1])]


def _swing_highs(cs, a, b, w=3):
    return [j for j in range(max(a, w), min(b, len(cs) - w)) if cs[j]["h"] == max(x["h"] for x in cs[j - w:j + w + 1])]


def d_sweep(cs, A):
    for i in range(30, len(cs)):
        c = cs[i]
        lows = [j for j in _swing_lows(cs, i - 30, i - 4) if cs[j]["l"] == _lowest(cs, j, i)]
        if lows:
            j = lows[-1]; lvl = cs[j]["l"]
            if c["l"] < lvl - A[i] * 0.1 and c["c"] > lvl:
                yield i, 1, [{"type": "hline", "v": lvl, "i1": j, "i2": i, "label": "low"}, {"type": "circle", "i": i, "at": "l"}]
                continue
        highs = [j for j in _swing_highs(cs, i - 30, i - 4) if cs[j]["h"] == _highest(cs, j, i)]
        if highs:
            j = highs[-1]; lvl = cs[j]["h"]
            if c["h"] > lvl + A[i] * 0.1 and c["c"] < lvl:
                yield i, -1, [{"type": "hline", "v": lvl, "i1": j, "i2": i, "label": "high"}, {"type": "circle", "i": i, "at": "h"}]


def d_retest(cs, A):
    for i in range(40, len(cs)):
        for b in range(i - 7, i - 1):                    # breakout candle b, retest at i
            res = _highest(cs, b - 30, b - 3)
            if cs[b]["c"] > res + A[b] * 0.2 and cs[b - 1]["c"] <= res and min(x["l"] for x in cs[b + 1:i]) > res \
                    and cs[i]["l"] <= res + A[i] * 0.25 and cs[i]["c"] > res:
                yield i, 1, [{"type": "hline", "v": res, "i1": b - 30, "i2": i, "label": "R → S"},
                             {"type": "circle", "i": b, "at": "h", "small": True}, {"type": "circle", "i": i, "at": "l"}]
                break
            sup = _lowest(cs, b - 30, b - 3)
            if cs[b]["c"] < sup - A[b] * 0.2 and cs[b - 1]["c"] >= sup and max(x["h"] for x in cs[b + 1:i]) < sup \
                    and cs[i]["h"] >= sup - A[i] * 0.25 and cs[i]["c"] < sup:
                yield i, -1, [{"type": "hline", "v": sup, "i1": b - 30, "i2": i, "label": "S → R"},
                              {"type": "circle", "i": b, "at": "l", "small": True}, {"type": "circle", "i": i, "at": "h"}]
                break


def d_divergence(cs, A, R):
    for i in range(40, len(cs)):
        p = i - 2                                         # pivot confirmed two candles later
        lows = _swing_lows(cs, p - 30, p - 5, 2)
        if lows and cs[p]["l"] == min(x["l"] for x in cs[p - 2:i + 1]):
            j = lows[-1]
            if cs[p]["l"] < cs[j]["l"] and R[p] > R[j] + 3 and R[j] < 40:
                yield i, 1, [{"type": "seg", "i1": j, "v1": cs[j]["l"], "i2": p, "v2": cs[p]["l"]},
                             {"type": "rseg", "i1": j, "i2": p}]
                continue
        highs = _swing_highs(cs, p - 30, p - 5, 2)
        if highs and cs[p]["h"] == max(x["h"] for x in cs[p - 2:i + 1]):
            j = highs[-1]
            if cs[p]["h"] > cs[j]["h"] and R[p] < R[j] - 3 and R[j] > 60:
                yield i, -1, [{"type": "seg", "i1": j, "v1": cs[j]["h"], "i2": p, "v2": cs[p]["h"]},
                              {"type": "rseg", "i1": j, "i2": p}]


def d_double(cs, A):
    for i in range(40, len(cs)):
        lows = _swing_lows(cs, i - 30, i - 1, 2)
        for a in range(len(lows) - 1):
            j1, j2 = lows[a], lows[-1]
            if j2 - j1 < 6:
                continue
            l1, l2 = cs[j1]["l"], cs[j2]["l"]
            neck = _highest(cs, j1, j2)
            if abs(l1 - l2) <= A[j2] * 0.5 and neck - max(l1, l2) >= A[j2] * 2.5 and min(l1, l2) <= _lowest(cs, j1 - 10, i) \
                    and cs[i]["c"] > neck and cs[i - 1]["c"] <= neck and _lowest(cs, j2 + 1, i + 1) > min(l1, l2):
                yield i, 1, [{"type": "circle", "i": j1, "at": "l"}, {"type": "circle", "i": j2, "at": "l"},
                             {"type": "hline", "v": neck, "i1": j1, "i2": i, "label": "neckline"}]
                break
        highs = _swing_highs(cs, i - 30, i - 1, 2)
        for a in range(len(highs) - 1):
            j1, j2 = highs[a], highs[-1]
            if j2 - j1 < 6:
                continue
            h1, h2 = cs[j1]["h"], cs[j2]["h"]
            neck = _lowest(cs, j1, j2)
            if abs(h1 - h2) <= A[j2] * 0.5 and min(h1, h2) - neck >= A[j2] * 2.5 and max(h1, h2) >= _highest(cs, j1 - 10, i) \
                    and cs[i]["c"] < neck and cs[i - 1]["c"] >= neck and _highest(cs, j2 + 1, i + 1) < max(h1, h2):
                yield i, -1, [{"type": "circle", "i": j1, "at": "h"}, {"type": "circle", "i": j2, "at": "h"},
                              {"type": "hline", "v": neck, "i1": j1, "i2": i, "label": "neckline"}]
                break


def d_fvg(cs, A):
    for i in range(20, len(cs)):
        a, m, c = cs[i - 2], cs[i - 1], cs[i]
        if _body(m) < A[i] * 1.4:
            continue
        if c["l"] > a["h"] and m["c"] > m["o"] and c["l"] - a["h"] >= A[i] * 0.35:
            yield i, 1, [{"type": "zone", "lo": a["h"], "hi": c["l"], "i1": i - 2, "label": "FVG"}]
        elif c["h"] < a["l"] and m["c"] < m["o"] and a["l"] - c["h"] >= A[i] * 0.35:
            yield i, -1, [{"type": "zone", "lo": c["h"], "hi": a["l"], "i1": i - 2, "label": "FVG"}]


def d_ema(cs, A, E20, E50):
    for i in range(60, len(cs)):
        if E20[i] > E50[i] and E20[i - 1] <= E50[i - 1] and all(E20[j] < E50[j] for j in range(i - 12, i - 1)):
            yield i, 1, [{"type": "ema"}, {"type": "dot", "i": i, "v": E20[i]}]
        elif E20[i] < E50[i] and E20[i - 1] >= E50[i - 1] and all(E20[j] > E50[j] for j in range(i - 12, i - 1)):
            yield i, -1, [{"type": "ema"}, {"type": "dot", "i": i, "v": E20[i]}]


def detect(topic, cs):
    A = atr(cs)
    if topic == "divergence":
        return list(d_divergence(cs, A, rsi([c["c"] for c in cs])))
    if topic == "ema":
        cl = [c["c"] for c in cs]
        return list(d_ema(cs, A, ema(cl, 20), ema(cl, 50)))
    return list({"pinbar": d_pinbar, "engulfing": d_engulfing, "sweep": d_sweep, "retest": d_retest,
                 "double": d_double, "fvg": d_fvg}[topic](cs, A))


# ------------------------------------------------------------------ outcome (honest, both ways)
def outcome(cs, i, d, topic, marks):
    entry = cs[i]["c"]
    nxt = cs[i + 1:i + 1 + K]
    fav = max((x["h"] - entry) if d > 0 else (entry - x["l"]) for x in nxt) / entry * 100
    adv = max((entry - x["l"]) if d > 0 else (x["h"] - entry) for x in nxt) / entry * 100
    end = (nxt[-1]["c"] - entry) / entry * 100 * d
    res = {"fav": round(fav, 1), "adv": round(adv, 1), "end": round(end, 1), "worked": fav >= max(1.0, adv) and end > -adv * 0.5}
    if topic == "fvg":                                     # FVG: did price come back into the gap?
        z = marks[0]
        filled = any((x["l"] <= z["hi"]) if d > 0 else (x["h"] >= z["lo"]) for x in nxt)
        res["filled"] = filled
    return res


# ------------------------------------------------------------------ Armenian texts (checked by the spell gate)
def P(d, up, down):
    return up if d > 0 else down


def texts(topic, d):
    t = {
        "pinbar": dict(
            hook=P(d, "Մեկ մոմը ցույց տվեց, որ վաճառողները *հոգնել են*", "Մեկ մոմը ցույց տվեց, որ գնողները *հոգնել են*"),
            concept=[P(d, "Pin bar՝ երկար ստորին պոչ և փոքր մարմին։", "Pin bar՝ երկար վերին պոչ և փոքր մարմին։"),
                     P(d, "Գինն իջավ, բայց գնողները այն հետ բարձրացրին։", "Գինը բարձրացավ, բայց վաճառողները այն հետ իջեցրին։")],
            label="Pin bar", rule="Pin bar-ը ուժ ունի միայն *կարևոր մակարդակի* վրա։"),
        "engulfing": dict(
            hook="Այս մոմը «կլանեց» նախորդին ու *փոխեց ուղղությունը*",
            concept=["Engulfing՝ նոր մոմի մարմինը ամբողջությամբ ծածկում է նախորդինը։",
                     P(d, "Ուժը վաճառողներից անցավ գնողներին։", "Ուժը գնողներից անցավ վաճառողներին։")],
            label=P(d, "Bullish engulfing", "Bearish engulfing"), rule="Engulfing-ը ամենաուժեղն է *տրենդի ծայրում*։"),
        "sweep": dict(
            hook=P(d, "Գինը կոտրեց low-ը… ու *անմիջապես հետ դարձավ*", "Գինը կոտրեց high-ը… ու *անմիջապես հետ դարձավ*"),
            concept=[P(d, "Low-ի տակ շատերն են դնում stop loss։", "High-ի վրա շատերն են դնում stop loss։"),
                     P(d, "Գինը «հավաքում է» այդ stop-երը, հետո փակվում է մակարդակից վեր։",
                       "Գինը «հավաքում է» այդ stop-երը, հետո փակվում է մակարդակից ներքև։")],
            label="Liquidity sweep", rule="Մի՛ դիր stop loss-դ *բոլորի պես*՝ ուղիղ մակարդակի հետևում։"),
        "retest": dict(
            hook=P(d, "Դիմադրությունը կոտրվեց ու *դարձավ աջակցություն*", "Աջակցությունը կոտրվեց ու *դարձավ դիմադրություն*"),
            concept=[P(d, "Գինը կոտրեց մակարդակը և փակվեց վերևում։", "Գինը կոտրեց մակարդակը և փակվեց ներքևում։"),
                     "Retest՝ գինը վերադառնում է ստուգելու նույն մակարդակը։"],
            label="Breakout + retest", rule="Մի՛ շտապիր կոտրման պահին՝ *սպասիր retest-ին*։"),
        "divergence": dict(
            hook=P(d, "Գինը նոր low արեց, բայց RSI-ը՝ *ոչ*", "Գինը նոր high արեց, բայց RSI-ը՝ *ոչ*"),
            concept=["Divergence՝ գինը և RSI-ը գնում են տարբեր ուղղություններով։",
                     P(d, "Անկման ուժը թուլանում է, թեև գինը դեռ իջնում է։", "Աճի ուժը թուլանում է, թեև գինը դեռ բարձրանում է։")],
            label=P(d, "Bullish divergence", "Bearish divergence"), rule="Divergence-ը *նախազգուշացում է*, ոչ թե մուտքի ազդանշան։"),
        "double": dict(
            hook=P(d, "Գինը երկու անգամ դիպավ *նույն հատակին*", "Գինը երկու անգամ դիպավ *նույն գագաթին*"),
            concept=[P(d, "Double bottom՝ երկու հավասար low, իսկ մեջտեղում՝ գագաթ։", "Double top՝ երկու հավասար high, իսկ մեջտեղում՝ հատակ։"),
                     P(d, "Ազդանշանը գալիս է, երբ գինը փակվում է neckline-ից վեր։", "Ազդանշանը գալիս է, երբ գինը փակվում է neckline-ից ներքև։")],
            label=P(d, "Double bottom", "Double top"), rule="Առանց neckline-ի կոտրման՝ սա *դեռ ֆիգուր չէ*։"),
        "fvg": dict(
            hook="Այս «դատարկ» գոտին գինը *հաճախ լցնում է*",
            concept=["Fair Value Gap՝ երեք մոմ, որոնց միջև գինը չի առևտրվել։",
                     "Արագ շարժումը թողնում է անհավասարակշռություն, և գինը հաճախ վերադառնում է։"],
            label="Fair Value Gap", rule="FVG-ն *գոտի է*, ոչ թե ճշգրիտ գին։"),
        "ema": dict(
            hook="Երկու գիծ, որոնք ցույց են տալիս *տրենդի փոփոխությունը*",
            concept=["EMA 20-ը արագ է արձագանքում, EMA 50-ը՝ դանդաղ։",
                     P(d, "Երբ EMA 20-ը հատում է EMA 50-ը ներքևից վեր, տրենդը կարող է շրջվել դեպի աճ։",
                       "Երբ EMA 20-ը հատում է EMA 50-ը վերևից ներքև, տրենդը կարող է շրջվել դեպի անկում։")],
            label=P(d, "EMA 20 ↑ EMA 50", "EMA 20 ↓ EMA 50"), rule="Կողային շուկայում EMA-ների հատումները *հաճախ սխալ են*։"),
    }[topic]
    return t


def outcome_text(topic, d, res):
    if topic == "fvg":
        if res["filled"]:
            return ["Գինը վերադարձավ *FVG գոտի*", f"հաջորդ {K} մոմի ընթացքում։"]
        return ["Այս անգամ գինը *չվերադարձավ*։", "Gap-ը կարող է երկար մնալ չլցված։"]
    if res["worked"]:
        sign = "+" if d > 0 else "−"
        verb = "գինը բարձրացավ" if d > 0 else "գինն իջավ"
        return [f"Հաջորդ {K} մոմում {verb}", f"մինչև *{sign}{res['fav']:.1f}%*։"]
    return ["Այս անգամ *չաշխատեց*։", f"Գինը գնաց հակառակ՝ {res['adv']:.1f}%։ Ահա թե ինչու է պետք stop loss։"]


def kinetic(s):
    """Words() marks accent per word: '*a b*' -> '*a* *b*'."""
    import re
    return re.sub(r"\*([^*]+)\*", lambda m: " ".join(f"*{w}*" for w in m.group(1).split()), s)


def plain(s):
    return s.replace("*", "")


# ------------------------------------------------------------------ choose today's lesson
def find(topic, data, used, want_fail=False):
    """Most recent unused example. Teaching examples are the ones that worked; every 4th lesson shows one that did not
    (honesty: patterns fail, that is what stop loss is for). A topic with no fitting example is skipped today."""
    best = None
    for asset, cs in data.items():
        evs = [e for e in detect(topic, cs) if e[0] + K < len(cs) and e[0] >= BEFORE and e[0] >= len(cs) - (260 if ASSETS_INFO[asset]["tf"] == "4H" else 90)]
        for i, d, marks in reversed(evs):
            key = f"{topic}:{asset}:{cs[i]['t']}"
            if key in used:
                continue
            r = outcome(cs, i, d, topic, marks)
            ok = r.get("filled", r["worked"])
            cand = (asset, i, d, cs[i], marks, key)
            if ok != want_fail and (best is None or cs[i]["t"] > best[3]["t"]):
                best = cand
    return best


def _rel(m, s):
    m = dict(m)
    for k in ("i", "i1", "i2"):
        if k in m:
            m[k] = max(0, m[k] - s)
    return m


def build(st, now, data=None):
    """Returns (props, caption, meta). data={asset: candles} can be given for tests."""
    if data is None:
        data = {}
        for a in SCAN_ASSETS:
            try:
                cs = candles(a)
                if len(cs) >= 120:
                    data[a] = cs
            except Exception as exc:  # noqa: BLE001
                print("[chart_lesson] no data", a, exc)
    if not data:
        raise RuntimeError("chart lesson: no market data")
    used = set(st.get("chart_lessons_used", []))
    n0 = st.get("chart_lesson_n", 0)
    for k in range(len(TOPICS)):
        topic = TOPICS[(n0 + k) % len(TOPICS)]
        hit = find(topic, data, used, want_fail=(n0 % 4 == 3))
        if hit:
            break
    else:
        raise RuntimeError("chart lesson: no pattern found in any asset")
    asset, i, d, c, marks, key = hit
    cs = data[asset]
    s, e = i - BEFORE, i + 1 + K
    win = cs[s:e]
    res = outcome(cs, i, d, topic, marks)
    tx = texts(topic, d)
    info = ASSETS_INFO[asset]
    when = dt.datetime.fromtimestamp(c["t"], dt.timezone.utc).strftime("%d.%m.%Y")
    props = {
        "symbol": info["symbol"], "tf": info["tf"], "asset": asset, "date": when, "dir": d, "topic": topic,
        "candles": [{k2: x[k2] for k2 in "ohlc"} for x in win], "signal": BEFORE,
        "marks": [_rel(m, s) for m in marks],
        "hook": kinetic(tx["hook"]), "concept": tx["concept"], "label": tx["label"], "rule": kinetic(tx["rule"]),
        "outcome": outcome_text(topic, d, res), "worked": bool(res.get("filled", res["worked"])),
        "entry": fmt(asset, c["c"]),
    }
    if topic == "divergence":
        props["rsi"] = [round(v, 1) for v in rsi([x["c"] for x in cs])[s:e]]
    if topic == "ema":
        cl = [x["c"] for x in cs]
        props["ema20"], props["ema50"] = ema(cl, 20)[s:e], ema(cl, 50)[s:e]
    meta = {"topic": topic, "asset": asset, "key": key, "result": res, "n_next": (TOPICS.index(topic) + 1)}
    return props, caption(props, info, res), meta


def caption(p, info, res):
    tag = {"sweep": "#liquidity #smartmoney", "pinbar": "#pinbar #priceaction", "retest": "#breakout #supportresistance",
           "divergence": "#rsi #divergence", "engulfing": "#engulfing #candlestick", "double": "#doublebottom #chartpatterns",
           "fvg": "#fvg #ict", "ema": "#ema #movingaverage"}[p["topic"]]
    lines = [
        f"📊 {plain(p['hook'])}",
        "",
        *[plain(x) for x in p["concept"]],
        "",
        f"📍 Իրական օրինակ՝ {info['symbol']} · {info['tf']} · {p['date']}",
        "➡️ " + " ".join(plain(x) for x in p["outcome"]),
        "",
        f"✅ Կանոն՝ {plain(p['rule'])}",
        "",
        "📩 Ուզու՞մ ես սովորել chart կարդալ՝ գրիր DM «ԴԱՍ»",
        "💾 Պահիր, որ չմոռանաս",
        "",
        f"⚠️ {DISCLAIMER}։",
        "",
        "Թրեյդինգ հայերեն · տեխնիկական վերլուծություն · իրական գրաֆիկ",
        f"{tag} {info['tags']} #trading #թրեյդինգ #հայերեն",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ render
TOTAL = 35 * FPS


def _npx(*args):
    extra = [f"--browser-executable={os.environ['REMOTION_BROWSER']}"] if os.environ.get("REMOTION_BROWSER") else []
    subprocess.run(["npx", "--yes", "remotion", *args, *extra], cwd=MOTION, check=True)      # remotion/public: brand fonts + SFX


def render(props, mp4, cover, music=None):
    """4K (2160x3840) render. Remotion's own track (SFX cues) is mixed with the background music."""
    if not os.path.isdir(os.path.join(MOTION, "node_modules")):
        subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--silent"], cwd=MOTION, check=True)
    pj = os.path.join(MOTION, "props-chart.json")
    json.dump(props, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
    raw = mp4 + ".raw.mp4"
    _npx("render", "src/index.tsx", "ChartLesson", raw, f"--props={pj}", "--crf=16", "--scale=2")
    _npx("still", "src/index.tsx", "ChartLesson", cover, f"--props={pj}", "--frame=20", "--image-format=jpeg", "--scale=2", "--jpeg-quality=92")
    if music:
        end = TOTAL / FPS
        has_sfx = "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", raw],
                                            capture_output=True, text=True).stdout
        mus = f"[1:a]atrim=0:{end},afade=t=in:d=0.6,afade=t=out:st={end - 2}:d=2,loudnorm=I=-17:TP=-2:LRA=11,volume=0.85[m]"
        graph = f"{mus};[0:a]volume=1.0[s];[m][s]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" if has_sfx else mus.replace("[m]", "[a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-stream_loop", "-1", "-i", music,
                        "-filter_complex", graph, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-t", f"{end:.2f}", "-movflags", "+faststart", mp4], check=True)
        os.remove(raw)
    else:
        shutil.move(raw, mp4)
    return mp4, cover
