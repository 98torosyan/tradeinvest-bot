"""Course-map website (link in bio): every module and lesson, published ones link to Instagram."""
import html
import os

from . import curriculum

CSS = """*{box-sizing:border-box;margin:0;padding:0}body{background:#07101F;color:#EEF3FA;font-family:system-ui,-apple-system,'Noto Sans Armenian',sans-serif;line-height:1.5}
header{padding:48px 20px 28px;text-align:center;background:radial-gradient(80% 120% at 50% 0,#16295A,#07101F)}
h1{font-size:30px}header p{color:#93A3C4;margin-top:8px}main{max-width:760px;margin:0 auto;padding:10px 16px 60px}
details{background:#0C1A33;border:1px solid #1d2d52;border-radius:16px;margin:12px 0;overflow:hidden}
summary{cursor:pointer;padding:16px 18px;font-weight:700;font-size:18px;list-style:none;display:flex;justify-content:space-between;gap:10px}
summary span{color:#93A3C4;font-weight:500;font-size:14px}ol{padding:0 18px 16px 44px}li{padding:6px 0;color:#93A3C4}
li a{color:#9CC2FF;text-decoration:none}li.done{color:#EEF3FA}footer{text-align:center;color:#93A3C4;font-size:13px;padding:30px}"""


def build(cur, state, out_dir):
    pub = state.get("published", {})
    parts = []
    for m in cur["modules"]:
        ls = [l for l in cur["lessons"] if l["module"] == m["n"]]
        done = sum(1 for l in ls if l["id"] in pub)
        items = []
        for l in ls:
            p = pub.get(l["id"])
            t = html.escape(l["title"])
            items.append(f'<li class="done"><a href="{html.escape(p["permalink"])}">{t}</a></li>' if p and p.get("permalink")
                         else f"<li>{t}</li>")
        parts.append(f'<details{" open" if 0 < done < len(ls) or m["n"] == 1 else ""}><summary>Մոդուլ {m["n"]}. '
                     f'{html.escape(m["title"])}<span>{done}/{len(ls)}</span></summary><ol>{"".join(items)}</ol></details>')
    total = len(cur["lessons"])
    page = (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>TradeInvest. Crypto և թրեյդինգ դասընթաց հայերեն</title>'
            f'<meta name="description" content="Անվճար crypto և թրեյդինգ դասընթաց հայերեն՝ զրոյից մինչև պրոֆեսիոնալ մակարդակ. {total} դաս, 11 մոդուլ։">'
            f'<style>{CSS}</style></head><body><header><h1>📚 TradeInvest դասընթաց</h1>'
            f'<p>Crypto և թրեյդինգ հայերեն՝ զրոյից մինչև պրոֆեսիոնալ մակարդակ · {total} դաս · 11 մոդուլ</p></header>'
            f'<main>{"".join(parts)}</main><footer>@armtradeinvest · Կրթական բովանդակություն, ոչ ֆինանսական խորհուրդ</footer></body></html>')
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(page)
    return os.path.join(out_dir, "index.html")
