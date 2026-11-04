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


def caption(s, kw):
    lines = [_plain(s["hook"]), "", s.get("caption", ""), ""]
    for b in s["beats"]:
        lines.append("▪️ " + " ".join(x for x in (b.get("big"), _plain(b.get("text", ""))) if x))
    lines += ["", "👉 " + _plain(s["rule"]), ""]
    if kw:
        lines.append("📩 Ուզում ես սովորել համակարգված՝ գրիր «ԴԱՍ» comment-ում կամ DM-ում")
    else:
        lines.append("🔖 Պահիր, որ չմոռանաս  ·  📤 Ուղարկիր ընկերոջդ")
    lines += ["", f"⚠️ {DISCLAIMER}։", "", (s.get("tags", "") + " #հայերեն").strip()]
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
        props["theme"] = "tuff" if (s["series"] == "ՀՈԳԵԲԱՆՈՒԹՅՈՒՆ" and n % 2 == 0) else "sevan"
    pj = os.path.join(MOTION, "props_short.json")
    json.dump(props, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
    raw = mp4 + ".raw.mp4"
    _npx("render", "src/index.tsx", "Short", raw, f"--props={pj}", "--crf=18")
    _npx("still", "src/index.tsx", "Short", cover, f"--props={pj}", "--frame=20", "--image-format=jpeg")
    if music:
        # keep the SFX track and lay the music bed under it
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-i", music, "-filter_complex",
                        "[1:a]volume=0.35,afade=t=in:d=0.4[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", mp4], check=True)
        os.remove(raw)
    else:
        shutil.move(raw, mp4)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                               capture_output=True, text=True).stdout or 0)
    return dur
