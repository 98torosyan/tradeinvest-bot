"""Sunday «Շաբաթը մեկ հայացքով» Reel: weekly % change of BTC, ETH, SOL, gold and Nasdaq from real daily closes."""
import datetime as dt
import json
import os
import subprocess

import requests

from .analysis import UA, T, MOTION
from .shorts import _npx

MONTHS_EN = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DISCLAIMER = "Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ"
MARKETS = [("Bitcoin", "BTC", "binance", "BTCUSDT"), ("Ethereum", "ETH", "binance", "ETHUSDT"),
           ("Solana", "SOL", "binance", "SOLUSDT"), ("Ոսկի", "XAU", "yahoo", "GC=F"), ("Nasdaq", "NDX", "yahoo", "^NDX")]


def _binance_daily(sym):
    for base in ("https://data-api.binance.vision/api/v3", "https://api.binance.com/api/v3"):
        try:
            rows = requests.get(f"{base}/klines", params={"symbol": sym, "interval": "1d", "limit": 9}, headers=UA, timeout=T).json()
            return [(dt.datetime.utcfromtimestamp(r[0] / 1000).date(), float(r[4])) for r in rows[:-1]]   # closed days only
        except Exception as exc:  # noqa: BLE001
            print("[weekly] binance", base, exc)
    raise RuntimeError(f"no candles for {sym}")


def _yahoo_daily(sym):
    d = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}", params={"range": "1mo", "interval": "1d"},
                     headers=UA, timeout=T).json()["chart"]["result"][0]
    out = [(dt.datetime.utcfromtimestamp(ts).date(), c) for ts, c in zip(d["timestamp"], d["indicators"]["quote"][0]["close"]) if c]
    return out


def build(now):
    """Closes over the last 7 days (plus the close before them) -> % change."""
    end = now.date()
    start = end - dt.timedelta(days=7)
    rows = []
    for name, sym, src, code in MARKETS:
        try:
            ser = _binance_daily(code) if src == "binance" else _yahoo_daily(code)
        except Exception as exc:  # noqa: BLE001
            print("[weekly] skip", sym, exc); continue
        base = [c for d, c in ser if d <= start]
        week = [c for d, c in ser if start < d <= end]
        if not base or len(week) < 3:
            print("[weekly] not enough data", sym); continue
        closes = [base[-1]] + week
        rows.append({"name": name, "sym": sym, "closes": [round(c, 4) for c in closes], "pct": round((closes[-1] / closes[0] - 1) * 100, 1)})
    if len(rows) < 3:
        raise RuntimeError("weekly: not enough markets")
    s1 = start + dt.timedelta(days=1)
    rng = f"{MONTHS_EN[s1.month - 1]} {s1.day} – {MONTHS_EN[end.month - 1]} {end.day}"
    return {"range": rng, "rows": rows}


def caption(props):
    rs = props["rows"]
    best = max(rs, key=lambda r: r["pct"]); worst = min(rs, key=lambda r: r["pct"])
    sign = lambda v: f"+{v:.1f}%" if v >= 0 else f"−{abs(v):.1f}%"  # noqa: E731
    lines = ["📊 Շաբաթը մեկ հայացքով", "", *[f"{'🟢' if r['pct'] >= 0 else '🔴'} {r['name']} ({r['sym']})՝ {sign(r['pct'])}" for r in rs], "",
             f"🏆 Հաղթող՝ {best['name']} · 📉 Պարտվող՝ {worst['name']}", "",
             "💬 Ո՞ր ակտիվն էր քոնը այս շաբաթ։ Գրիր comment-ում", "",
             f"⚠️ {DISCLAIMER}։ Տվյալները՝ օրական փակման գներով։", "",
             "Շաբաթական ամփոփում · crypto · ոսկի · Nasdaq · թրեյդինգ հայերեն",
             "#bitcoin #crypto #gold #nasdaq #weeklyrecap #հայերեն #թրեյդինգհայերեն"]
    return "\n".join(lines)


def render(props, mp4, cover, music=None):
    if not os.path.isdir(os.path.join(MOTION, "node_modules")):
        subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--silent"], cwd=MOTION, check=True)
    pj = os.path.join(MOTION, "props_weekly.json")
    json.dump(props, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
    raw = mp4 + ".raw.mp4"
    _npx("render", "src/index.tsx", "Weekly", raw, f"--props={pj}", "--crf=18")
    _npx("still", "src/index.tsx", "Weekly", cover, f"--props={pj}", "--frame=170", "--image-format=jpeg")
    if music:
        rd = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw],
                                  capture_output=True, text=True).stdout or 15)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-i", music, "-filter_complex",
                        f"[1:a]volume=0.35,afade=t=in:d=0.4,afade=t=out:st={max(0, rd - 1.2):.2f}:d=1.2[m];"
                        "[0:a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", mp4], check=True)
        os.remove(raw)
    else:
        os.replace(raw, mp4)
    return mp4, cover
