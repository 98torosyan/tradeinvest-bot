"""Educational carousels (1080x1350), brand TI Rise, 3 per week at 15:07 Yerevan (Mon/Wed/Fri).
Content: reels/content/carousels.json. Each carousel = cover -> topic slides -> rule (amber) -> CTA."""
import json
import os
import re

from .builder import esc
from .carousel import _page, _icon, render  # noqa: F401  (render re-exported)

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "carousels.json")
DISCLAIMER = "Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ։"

EXTRA = """<style>
.box{position:absolute;left:86px;right:86px;top:170px;bottom:160px;display:flex;flex-direction:column;justify-content:center}
.kick{font-family:Mono,monospace;font-size:26px;font-weight:700;letter-spacing:.14em;color:var(--a2)}
.cvh{margin-top:30px;font-size:104px;font-weight:800;line-height:1.04;letter-spacing:-.025em;font-stretch:75%}
.cvh .acc{color:var(--a2)}.sub{margin-top:34px;font-size:38px;line-height:1.3;color:var(--mut);font-weight:600}
.big{font-family:Mono,monospace;font-size:150px;font-weight:800;line-height:1;color:var(--a)}
.pt h2{margin-top:30px;font-size:76px;line-height:1.08;font-weight:800;letter-spacing:-.02em;font-stretch:80%}
.pt p{margin-top:30px;font-size:42px;line-height:1.38;color:var(--p)}
.hd{font-size:30px;font-weight:700;letter-spacing:.06em;color:var(--mut);margin-bottom:28px}
.tb{border-top:2px solid rgba(255,255,255,.12)}.tr{display:flex;justify-content:space-between;align-items:baseline;padding:28px 6px;border-bottom:2px solid rgba(255,255,255,.12);font-size:46px}
.tr b{font-weight:700}.tr span{font-family:ArmV,sans-serif;font-weight:800;color:var(--a2);font-size:44px}
.note{margin-top:28px;font-size:28px;color:var(--mut)}
.fm{font-size:62px;font-weight:800;line-height:1.2;padding:44px 40px;border-radius:28px;background:rgba(255,138,0,.10);border:2px solid rgba(255,138,0,.45)}
.fl{margin-top:36px;font-size:40px;line-height:1.5;color:var(--p)}.fl div:before{content:"→ ";color:var(--a2)}
.ls{display:flex;flex-direction:column;gap:6px}.li{display:flex;gap:28px;align-items:center;padding:22px 0;border-bottom:2px solid rgba(255,255,255,.10);font-size:42px;font-weight:600}
.li em{font-style:normal;font-family:Mono,monospace;font-weight:800;color:var(--a);font-size:34px;min-width:56px}
.rl{font-size:92px;font-weight:800;line-height:1.08;letter-spacing:-.02em;font-stretch:78%}
.rl .acc{text-decoration:underline;text-decoration-thickness:10px;text-underline-offset:14px}
.my{padding:44px 44px;border-radius:28px;background:rgba(242,80,94,.10);border:2px solid rgba(242,80,94,.45)}
.fc{margin-top:34px;padding:44px 44px;border-radius:28px;background:rgba(52,201,138,.10);border:2px solid rgba(52,201,138,.45)}
.my span,.fc span{display:block;font-size:30px;font-weight:800;letter-spacing:.08em;margin-bottom:18px}.my span{color:#F2505E}.fc span{color:#34C98A}
.my div{font-size:58px;font-weight:800;line-height:1.12;text-decoration:line-through;text-decoration-color:rgba(242,80,94,.7);text-decoration-thickness:5px}
.fc div{font-size:40px;line-height:1.38;color:var(--p)}
.qm{font-size:260px;line-height:.6;color:var(--a);font-weight:800;height:120px}
.qt{font-size:84px;font-weight:800;line-height:1.12;letter-spacing:-.02em;font-stretch:80%}.qt .acc{color:var(--a2)}
.qs{margin-top:50px;font-size:32px;color:var(--mut);font-weight:700;letter-spacing:.06em}
.g-paper .tr,.g-paper .tb,.g-paper .li{border-color:rgba(11,11,12,.14)}
</style>"""


def load():
    return json.load(open(SRC, encoding="utf-8"))["carousels"]


def _acc(s):
    return re.sub(r"\*([^*]+)\*", r'<span class="acc">\1</span>', esc(s))


def _candle():
    # anatomy of one bullish candle with labels (Open / Close / High / Low / Body / Wick)
    return ('<svg width="908" height="900" viewBox="0 0 908 900">'
            '<line x1="300" y1="80" x2="300" y2="820" stroke="#F2EFE8" stroke-width="10" stroke-linecap="round"/>'
            '<rect x="200" y="250" width="200" height="380" rx="14" fill="#FF8A00"/>'
            + "".join(f'<line x1="420" y1="{y}" x2="560" y2="{y}" stroke="#A3A09A" stroke-width="3" stroke-dasharray="10 8"/>'
                      f'<text x="580" y="{y + 14}" font-family="Mono" font-weight="800" font-size="42" fill="{c}">{t}</text>'
                      for y, t, c in ((80, "HIGH", "#F2EFE8"), (250, "CLOSE", "#FFA640"), (630, "OPEN", "#FFA640"), (820, "LOW", "#F2EFE8")))
            + '<text x="40" y="450" font-family="ArmV" font-weight="700" font-size="34" fill="#A3A09A">Մարմին</text>'
              '<text x="40" y="170" font-family="ArmV" font-weight="700" font-size="34" fill="#A3A09A">Wick</text>'
              '<text x="40" y="740" font-family="ArmV" font-weight="700" font-size="34" fill="#A3A09A">Wick</text></svg>')


def _slide(s):
    t = s["type"]
    if t == "candle":
        return f'<div class="box" style="align-items:center">{_candle()}</div>', "ink"
    if t == "point":
        return (f'<div class="box pt"><div class="big">{esc(s["n"])}</div><h2>{_acc(s["title"])}</h2>'
                f'<p>{esc(s["text"])}</p></div>'), "ink"
    if t == "table":
        rows = "".join(f'<div class="tr"><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in s["rows"])
        note = f'<div class="note">{esc(s["note"])}</div>' if s.get("note") else ""
        return f'<div class="box"><div class="hd">{esc(s["head"])}</div><div class="tb">{rows}</div>{note}</div>', "ink"
    if t == "formula":
        lines = "".join(f"<div>{esc(x)}</div>" for x in s.get("lines", []))
        return (f'<div class="box"><div class="hd">{esc(s.get("head", ""))}</div><div class="fm">{esc(s["formula"])}</div>'
                f'<div class="fl">{lines}</div></div>'), "ink"
    if t == "list":
        items = "".join(f'<div class="li"><em>{i:02d}</em>{esc(x)}</div>' for i, x in enumerate(s["items"], 1))
        return f'<div class="box"><div class="hd">{esc(s["head"])}</div><div class="ls">{items}</div></div>', "ink"
    if t == "myth":
        return (f'<div class="box"><div class="my"><span>❌ ՄԻՖ</span><div>{esc(s["myth"])}</div></div>'
                f'<div class="fc"><span>✅ ՓԱՍՏ</span><div>{esc(s["fact"])}</div></div></div>'), "ink"
    if t == "quote":
        return (f'<div class="box"><div class="qm">“</div><div class="qt">{_acc(s["text"])}</div>'
                f'<div class="qs">— TradeInvest</div></div>'), "ink"
    if t == "rule":
        return f'<div class="edge"></div><div class="box"><div class="kick">ԿԱՆՈՆ</div><div class="rl" style="margin-top:30px">{_acc(s["text"])}</div></div>', "amber"
    raise ValueError(f"unknown slide type {t}")


def slides(c, n):
    body = [(f'<div class="edge"></div><div class="box"><div class="kick">{esc(c["kicker"])}</div>'
             f'<div class="cvh">{_acc(c["title"])}</div><div class="sub">{esc(c["sub"])}</div></div>',
             "paper" if n % 2 else "ink")]
    body += [_slide(s) for s in c["slides"]]
    body.append(('<div class="edge"></div><div class="end"><h1>Պահիր։<br><span class="acc">Կիսվիր։</span></h1><div class="acts">'
                 f'<div class="act"><span>{_icon("book")}</span>Պահիր՝ կրկնելու համար</div>'
                 f'<div class="act"><span>{_icon("users")}</span>Ուղարկիր ընկերոջդ</div>'
                 f'<div class="act"><span>{_icon("school")}</span>Անվճար մինի դասընթաց՝ հղումը bio-ում</div></div></div>', "ink"))
    total = len(body)
    return [_page(EXTRA + b, i, total, last=(i == total), ground=g) for i, (b, g) in enumerate(body, 1)]


def caption(c):
    plain = re.sub(r"\*", "", c["title"])
    return (f"{plain}\n\n{c['caption']}\n\n📌 Պահիր՝ կրկնելու համար\n📩 Ուղարկիր նրան, ով սովորում է թրեյդինգ\n"
            f"🎓 Անվճար մինի դասընթաց և PDF՝ հղումը bio-ում\n\n⚠️ {DISCLAIMER}\n\n"
            f"Թրեյդինգ հայերեն · տեխնիկական վերլուծություն · ռիսկի կառավարում\n{c['tags']} #հայերեն #թրեյդինգհայերեն")


def next_one(st):
    done = st.get("edu_carousels_done", {})
    for i, c in enumerate(load()):
        if c["id"] not in done:
            return c, i + 1
    return None, 0
