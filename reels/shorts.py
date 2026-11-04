"""Short lesson Reels (12–20 s) rendered with Remotion (composition "Short") in brand «Գիշերային Սևան».
Scripts: reels/content/shorts.json. One per day at 12:37 Yerevan; «ԴԱՍ» CTA only on Mon/Wed/Fri/Sun."""
import json
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTION = os.path.join(ROOT, "remotion")
SCRIPTS = os.path.join(ROOT, "reels", "content", "shorts.json")
KW_DAYS = {0, 2, 4, 6}                      # Mon, Wed, Fri, Sun (executive decision)
DISCLAIMER = "Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ"


def load():
    return json.load(open(SCRIPTS, encoding="utf-8"))["shorts"]


def next_script(st):
    done = set(st.get("shorts_done", {}))
    left = [s for s in load() if s["id"] not in done]
    return (left[0] if left else None), len(left)


def _marks(s):
    """The renderer marks single words: turn *a b* / _a b_ into *a* *b* / _a_ _b_."""
    import re
    return re.sub(r"([*_])([^*_]+?)\1", lambda m: " ".join(m.group(1) + w + m.group(1) for w in m.group(2).split()), s)


def _plain(s):
    return s.replace("*", "").replace("_", "").replace("|", " ")


SEO = {"RISK": "Թրեյդինգ հայերեն · ռիսկի կառավարում · risk management · stop-loss",
       "MINDSET": "Թրեյդինգ հայերեն · թրեյդինգի հոգեբանություն · trading psychology · discipline"}


def caption(s, kw):
    lines = [_plain(s["hook"]), "", s.get("caption", ""), ""]
    for b in s["beats"]:
        lines.append("▪️ " + " ".join(x for x in (b.get("big"), _plain(b.get("text", ""))) if x))
    lines += ["", "👉 " + _plain(s["rule"]), ""]
    if kw:
        lines.append("📩 Ուզում ես սովորել համակարգված՝ գրիր «ԴԱՍ» DM-ում")
    else:
        lines.append("🔖 Պահիր, որ չմոռանաս  ·  📤 Ուղարկիր ընկերոջդ")
    lines += ["🎓 Անվճար մինի դասընթաց և PDF՝ հղումը bio-ում", "", f"⚠️ {DISCLAIMER}։", "",
              SEO.get(s.get("series"), SEO["RISK"]), (s.get("tags", "") + " #հայերեն #թրեյդինգհայերեն").strip()]
    return "\n".join(lines)


def _npx(*args):
    extra = [f"--browser-executable={os.environ['REMOTION_BROWSER']}"] if os.environ.get("REMOTION_BROWSER") else []
    subprocess.run(["npx", "--yes", "remotion", *args, *extra], cwd=MOTION, check=True)


def render(s, kw, mp4, cover, music=None):
    if not os.path.isdir(os.path.join(MOTION, "node_modules")):
        subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--silent"], cwd=MOTION, check=True)
    props = json.loads(json.dumps({k: s[k] for k in ("index", "series", "tag", "hook", "beats", "rule", "hero", "theme") if k in s}))
    props["hook"], props["rule"] = _marks(props["hook"]), _marks(props["rule"])
    for b in props["beats"]:
        if b.get("text"):
            b["text"] = _marks(b["text"])
    props.setdefault("index", s["id"].split("-")[-1][-2:])
    props["cta"] = "kw" if kw else "none"
    n = int("".join(c for c in s["id"] if c.isdigit()) or 0)
    props["variant"] = (n * 5) % 16                     # camera move × text entrance: 16 combinations
    if "theme" not in s or s.get("theme") == "auto":
        props["theme"] = "ti_paper" if (s.get("kind") == "ՀՈԳԵԲԱՆՈՒԹՅՈՒՆ" and n % 2 == 0) else "ti"
    props["visual"] = visual(s, n)
    pj = os.path.join(MOTION, "props_short.json")
    json.dump(props, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
    raw = mp4 + ".raw.mp4"
    _npx("render", "src/index.tsx", "Short", raw, f"--props={pj}", "--crf=18")
    _npx("still", "src/index.tsx", "Short", cover, f"--props={pj}", "--frame=20", "--image-format=jpeg")
    if music:
        # keep the SFX track and lay the music bed under it
        rd = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw],
                                  capture_output=True, text=True).stdout or 15)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-i", music, "-filter_complex",
                        f"[1:a]volume=0.35,afade=t=in:d=0.4,afade=t=out:st={max(0, rd - 1.2):.2f}:d=1.2[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", mp4], check=True)
        os.remove(raw)
    else:
        shutil.move(raw, mp4)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                               capture_output=True, text=True).stdout or 0)
    return dur


# ---------------------------------------------------------------- topic visuals from REAL candles
ASSETS = [("BTCUSDT", "BTC/USDT"), ("ETHUSDT", "ETH/USDT"), ("SOLUSDT", "SOL/USDT"), ("PAXGUSDT", "GOLD (PAXG)"), ("BNBUSDT", "BNB/USDT")]
TFS = ["1h", "4h", "1d"]


def _klines(sym, tf, limit=300):
    import requests
    for base in ("https://data-api.binance.vision/api/v3", "https://api.binance.com/api/v3"):
        try:
            rows = requests.get(f"{base}/klines", params={"symbol": sym, "interval": tf, "limit": limit}, timeout=25).json()
            return [{"o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4])} for r in rows][:-1]
        except Exception as exc:  # noqa: BLE001
            print("[shorts] klines", base, exc)
    raise RuntimeError("no candles for the short visual")


def visual(s, n):
    """Build the visual spec. n = script number (also picks asset/timeframe so consecutive Reels differ)."""
    kind = s.get("visual", "chart")
    if kind.startswith("image:"):
        return {"kind": "image", "image": kind.split(":", 1)[1]}
    if kind in ("multiplier", "grid"):
        return {"kind": kind}
    sym, label = ASSETS[n % len(ASSETS)]
    tf = TFS[(n // len(ASSETS)) % len(TFS)]
    allc = _klines(sym, tf)
    W = 42
    spec = {"kind": kind, "symbol": label, "tf": tf.upper()}
    if kind == "split":
        spec["cs"] = allc[-W:]
        # B: the steepest falling 42-candle window in the history (adding to a loser)
        best = min(range(0, len(allc) - W), key=lambda i: allc[i + W - 1]["c"] / allc[i]["o"])
        spec["cs2"] = allc[best:best + W]
        return spec
    if kind == "fomo":
        # a window where a spike top sits at ~65% and price falls after it
        cands = [i for i in range(W, len(allc) - 12)]
        top = max(cands, key=lambda i: allc[i]["h"] / min(c["l"] for c in allc[i + 1:i + 12]))
        a = max(0, top - int(W * 0.65)); cs = allc[a:a + W]
        spec.update(cs=cs, peak=top - a)
        return spec
    cs = allc[-W:]
    spec["cs"] = cs
    if kind == "level":
        lo = min(c["l"] for c in cs); hi = max(c["h"] for c in cs)
        spec["zone"] = [lo, lo + (hi - lo) * 0.06]
    if kind == "stop":
        k = int(W * 0.45); e = cs[k]["c"]
        after_low = min(c["l"] for c in cs[k + 1:])
        spec.update(entry=e, stop=max(after_low, e - (e - after_low) * 0.8) if after_low < e else e * 0.985)
    if kind == "rr":
        e = cs[-1]["c"]; risk = max(e * 0.01, (max(c["h"] for c in cs) - min(c["l"] for c in cs)) * 0.12)
        spec.update(entry=e, stop=e - risk, target=e + 3 * risk)
    return spec
