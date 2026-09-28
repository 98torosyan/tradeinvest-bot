"""Daily quiz Story (retrieval practice) from yesterday's lessons: question, 3 options,
3-2-1 countdown, answer reveal. Plain video Story (stickers are not possible via API)."""
from .builder import ASSETS, esc, logo_svg
from .palettes import css_vars


def pick(cur, state, yesterday):
    pub = state.get("published", {})
    ids = [lid for lid, p in pub.items() if p.get("date") == yesterday]
    lessons = [l for l in cur["lessons"] if l["id"] in ids and l.get("quiz")]
    if not lessons:
        return None
    return lessons[state.get("quiz_count", 0) % len(lessons)]


def html(lesson, palette):
    q = dict(lesson["quiz"])
    order = sorted(range(3), key=lambda i: int.from_bytes(__import__("hashlib").md5(f"{lesson['id']}{i}".encode()).digest()[:4], "big"))     # shuffled, but stable per lesson
    q["options"] = [lesson["quiz"]["options"][i] for i in order]; q["a"] = order.index(lesson["quiz"]["a"])
    opts = "".join(f'<div class="o{" ok" if i == q["a"] else ""}" data-fx="rise" data-at="{0.9 + i * 0.35:.2f}" data-dur=".5">'
                   f'<b>{"ABC"[i]}</b>{esc(o)}</div>' for i, o in enumerate(q["options"]))
    return f'''<!doctype html><html lang="hy"><head><meta charset="utf-8"><link rel="stylesheet" href="{ASSETS}/fonts.css"><style>
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1080px;height:1920px;overflow:hidden}}
body{{background:var(--bg);color:var(--txt);font-family:ArmSans,sans-serif}}
.scene{{position:absolute;inset:0;visibility:hidden}}.top{{position:absolute;top:270px;left:0;right:0;text-align:center}}
.top span{{font-size:36px;font-weight:700;color:var(--onacc);background:linear-gradient(135deg,var(--a2),var(--a));padding:14px 30px;border-radius:40px}}
.q{{position:absolute;top:420px;left:80px;right:80px;text-align:center;font-family:ArmSerif,serif;font-weight:800;font-size:74px;line-height:1.18}}
.opts{{position:absolute;top:880px;left:90px;right:90px;display:flex;flex-direction:column;gap:26px}}
.o{{display:flex;align-items:center;gap:26px;font-size:52px;font-weight:700;padding:28px 34px;border-radius:28px;background:rgba(255,255,255,.07);border:2.5px solid rgba(255,255,255,.14)}}
.o b{{width:76px;height:76px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.1)}}
.cd{{position:absolute;top:1400px;left:0;right:0;text-align:center;font-size:150px;font-weight:800;color:var(--a2)}}
.lesson{{position:absolute;top:1450px;left:80px;right:80px;text-align:center;font-size:36px;color:var(--mut)}}
.logo{{position:absolute;left:490px;top:1560px;width:100px;height:100px}}</style></head><body style="{css_vars(palette)}">
<section class="scene" data-in="-1" data-out="13"><div class="top"><span>Quiz · երեկվա դասից</span></div>
<div class="q" data-fx="rise" data-at=".2" data-dur=".6">{esc(q["q"])}</div><div class="opts">{opts}</div>
<div class="cd" id="cd"></div><div class="lesson" id="ls">Դաս՝ «{esc(lesson["title"])}»</div>{logo_svg().replace("opacity:0", "opacity:1")}</section>
<script src="{ASSETS}/engine.js"></script><script>window.DURATION=12;
HOOKS.push(t=>{{const cd=document.getElementById('cd');const n=3-Math.floor(t-3.2);
 cd.textContent=(t>=3.2&&t<6.2)?n:'';cd.style.display=(t>=3.2&&t<6.2)?'block':'none';
 document.getElementById('ls').style.opacity=t>=6.4?1:0;
 document.querySelectorAll('.o').forEach(o=>{{if(t>=6.2){{if(o.classList.contains('ok')){{o.style.background='rgba(61,220,151,.22)';o.style.borderColor='#3DDC97';}}
  else o.style.opacity=.35;}}}});}});setupReel();</script></body></html>'''
