"""Course website (link in bio), brand system v2: series colour-coded, published lessons link to Instagram.
Self-hosted fonts (no third-party requests besides the optional cookie-free analytics)."""
import html
import os
import shutil

from .builder import ASSETS
from .palettes import BRAND, SERIES

IG = "https://www.instagram.com/armtradeinvest/"
FONTS = ["noto-sans-armenian-armenian-500-normal.woff2", "noto-sans-armenian-armenian-700-normal.woff2",
         "noto-sans-armenian-armenian-800-normal.woff2", "noto-sans-armenian-latin-500-normal.woff2",
         "noto-sans-armenian-latin-700-normal.woff2", "noto-sans-armenian-latin-800-normal.woff2",
         "jetbrains-mono-latin-700-normal.woff2"]
ARM = "U+0308,U+0530-058F,U+2010,U+2024,U+25CC,U+FB13-FB17"


def _font_css():
    out = ""
    for w in (500, 700, 800):
        out += (f"@font-face{{font-family:Arm;font-weight:{w};font-display:swap;src:url(fonts/noto-sans-armenian-armenian-{w}-normal.woff2) format('woff2');unicode-range:{ARM}}}"
                f"@font-face{{font-family:Arm;font-weight:{w};font-display:swap;src:url(fonts/noto-sans-armenian-latin-{w}-normal.woff2) format('woff2')}}")
    return out + "@font-face{font-family:Mono;font-weight:700;font-display:swap;src:url(fonts/jetbrains-mono-latin-700-normal.woff2) format('woff2')}"


CSS = """*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0B0B0C;--bg2:#141416;--card:rgba(255,255,255,.045);--line:rgba(255,255,255,.09);--txt:#F4F2EE;--mut:#A3A09A;--a:#FF8A00;--a2:#FFA640}
html{scroll-behavior:smooth}body{background:var(--bg);color:var(--txt);font-family:Arm,system-ui,-apple-system,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:inherit}.wrap{max-width:760px;margin:0 auto;padding:0 18px}
.top{display:flex;align-items:center;gap:10px;padding:18px 0}.top svg{width:24px;height:30px}.top b{font-size:17px;font-weight:800;letter-spacing:-.01em}
.top .ig{margin-left:auto;font-size:14px;font-weight:700;color:var(--a2);text-decoration:none;padding:8px 14px;border:1px solid rgba(255,138,0,.4);border-radius:99px}
.hero{position:relative;padding:34px 0 30px;overflow:hidden}
.hero::before{content:"";position:absolute;right:-260px;top:-260px;width:620px;height:620px;border-radius:50%;background:radial-gradient(circle,rgba(255,138,0,.10),transparent 62%);pointer-events:none}
.kick{display:flex;align-items:center;gap:10px;font-size:14px;font-weight:700;color:var(--a2)}.kick i{width:9px;height:9px;border-radius:2px;background:var(--a)}
h1{margin-top:14px;font-size:clamp(34px,9vw,54px);font-weight:800;line-height:1.05;letter-spacing:-.03em}h1 span{color:var(--a2)}
.lead{margin-top:14px;font-size:17px;color:var(--mut);max-width:560px}
.stats{margin-top:24px;display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.stat{padding:14px;border-radius:14px;background:var(--card);border:1px solid var(--line)}.stat b{display:block;font-family:Mono,Arm,monospace;font-size:24px;font-weight:700}
.stat span{font-size:13px;color:var(--mut)}
.cta{display:inline-flex;align-items:center;gap:10px;margin-top:22px;padding:14px 22px;border-radius:14px;background:var(--a);color:#0B0B0C;font-weight:800;text-decoration:none;font-size:16px}
.cta:hover{filter:brightness(1.08)}
.bar{margin-top:22px;height:8px;border-radius:8px;background:rgba(255,255,255,.08);overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--a),var(--a2))}
.barl{margin-top:8px;font-size:13px;color:var(--mut)}
h2{margin:38px 0 14px;font-size:13px;font-weight:700;letter-spacing:.08em;color:var(--mut);text-transform:uppercase}
.latest{display:grid;gap:10px}
.lc{position:relative;display:block;padding:16px 16px 16px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);text-decoration:none;overflow:hidden}
.lc::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--c)}
.lc small{font-size:12px;font-weight:700;color:var(--c2)}.lc b{display:block;font-size:17px;font-weight:700;margin-top:2px}
.lc:hover{border-color:rgba(255,255,255,.2)}
.find{width:100%;margin-top:2px;padding:14px 16px;border-radius:14px;border:1px solid var(--line);background:var(--bg2);color:var(--txt);font:inherit;font-size:16px;outline:none}
.find:focus{border-color:var(--a)}
details{margin:12px 0;border-radius:16px;background:var(--card);border:1px solid var(--line);overflow:hidden;position:relative}
details::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--c)}
summary{cursor:pointer;list-style:none;padding:16px 18px 16px 22px;display:flex;align-items:center;gap:12px}summary::-webkit-details-marker{display:none}
summary .t{font-size:17px;font-weight:800;flex:1}summary .n{font-family:Mono,Arm,monospace;font-size:13px;color:var(--mut)}
summary .ch{width:9px;height:9px;border-right:2px solid var(--mut);border-bottom:2px solid var(--mut);transform:rotate(45deg);transition:transform .2s}
details[open] summary .ch{transform:rotate(-135deg)}
.sb{height:4px;margin:0 18px 0 22px;border-radius:4px;background:rgba(255,255,255,.07);overflow:hidden}.sb i{display:block;height:100%;background:var(--c)}
ol{list-style:none;padding:8px 10px 12px 14px;counter-reset:n}
li{counter-increment:n;display:flex;align-items:baseline;gap:12px;padding:9px 8px;border-radius:10px;color:var(--mut);font-size:15px}
li::before{content:counter(n,decimal-leading-zero);font-family:Mono,Arm,monospace;font-size:12px;color:rgba(255,255,255,.3);min-width:22px}
li a{color:var(--txt);text-decoration:none;font-weight:600;flex:1}li a::after{content:" ↗";color:var(--c2)}li a:hover{color:var(--c2)}
li em{margin-left:auto;font-style:normal;font-size:12px;color:rgba(255,255,255,.35);white-space:nowrap}
li.hide{display:none}
.course{margin-top:26px;padding:20px;border-radius:16px;background:#FF8A00;color:#0B0B0C}.course b{display:block;font-size:20px;font-weight:800}
.course span{display:block;margin-top:6px;font-size:15px;line-height:1.45}.course a{display:inline-block;margin-top:12px;padding:10px 16px;border-radius:12px;background:#0B0B0C;color:#F4F2EE;font-weight:800;text-decoration:none}
footer{margin-top:44px;padding:26px 0 44px;border-top:1px solid var(--line);font-size:13px;color:var(--mut)}footer a{color:var(--a2)}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}"""

JS = """const q=document.getElementById('q');q&&q.addEventListener('input',()=>{const v=q.value.trim().toLowerCase();
document.querySelectorAll('details').forEach(d=>{let any=false;d.querySelectorAll('li').forEach(li=>{const m=!v||li.textContent.toLowerCase().includes(v);
li.classList.toggle('hide',!m);any=any||m;});d.style.display=any?'':'none';if(v)d.open=any;});});"""

LOGO = ('<svg viewBox="0 -96 366 436" aria-hidden="true"><rect x="0" y="0" width="252" height="78" rx="16" fill="#F4F2EE"/>'
        '<rect x="84" y="0" width="84" height="340" rx="16" fill="#F4F2EE"/><rect x="282" y="-96" width="84" height="436" rx="16" fill="#FF8A00"/></svg>')


FAVICON = ("%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='-60 -150 486 560'%3E%3Crect x='-60' y='-150' width='486' height='560' rx='90' fill='%230B0B0C'/%3E"
           "%3Crect x='0' y='0' width='252' height='78' rx='16' fill='%23F4F2EE'/%3E%3Crect x='84' y='0' width='84' height='340' rx='16' fill='%23F4F2EE'/%3E"
           "%3Crect x='282' y='-96' width='84' height='436' rx='16' fill='%23FF8A00'/%3E%3C/svg%3E")


def analytics():
    """Privacy-friendly, cookie-free visitor stats for the bio link page."""
    cf = os.environ.get("CF_ANALYTICS_TOKEN", "").strip()
    gc = os.environ.get("GOATCOUNTER_CODE", "").strip()
    if cf:
        return (f"<script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
                f"data-cf-beacon='{{\"token\": \"{html.escape(cf)}\"}}'></script>")
    if gc:
        return f'<script data-goatcounter="https://{html.escape(gc)}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
    return ""


def _col(n):
    return "--c:#FF8A00;--c2:#FFA640"          # v3: one accent; series are told apart by number


def build(cur, state, out_dir):
    pub = {k: v for k, v in state.get("published", {}).items() if v.get("permalink") and not v.get("skipped")}
    lessons = cur["lessons"]
    total, done_all = len(lessons), sum(1 for l in lessons if l["id"] in pub)
    hits = bool(cur.get("series"))
    parts = []
    for m in cur["modules"]:
        ls = [l for l in lessons if l["module"] == m["n"]]
        if not ls:
            continue
        done = sum(1 for l in ls if l["id"] in pub)
        items = "".join(f'<li><a href="{html.escape(pub[l["id"]]["permalink"])}" target="_blank" rel="noopener">{html.escape(l["title"])}</a></li>'
                        if l["id"] in pub else f'<li>{html.escape(l["title"])}<em>շուտով</em></li>' for l in ls)
        name = html.escape(m["title"]) if hits else f'Մոդուլ {m["n"]}. {html.escape(m["title"])}'
        parts.append(f'<details style="{_col(m["n"])}"{" open" if m["n"] == cur["modules"][0]["n"] else ""}><summary><span class="t">{name}</span>'
                     f'<span class="n">{done}/{len(ls)}</span><span class="ch"></span></summary>'
                     f'<div class="sb"><i style="width:{100 * done / len(ls):.0f}%"></i></div><ol>{items}</ol></details>')
    by_id = {l["id"]: l for l in lessons}
    recent = sorted((p.get("date", ""), p.get("hour", 0), k) for k, p in pub.items() if k in by_id)[-3:][::-1]
    latest = "".join(f'<a class="lc" style="{_col(by_id[k]["module"])}" href="{html.escape(pub[k]["permalink"])}" target="_blank" rel="noopener">'
                     f'<small>{html.escape(by_id[k].get("series") or "")}</small><b>{html.escape(by_id[k]["title"])}</b></a>' for _, _, k in recent)
    n_series = len(cur.get("series") or cur["modules"])
    title = "TradeInvest. Թրեյդինգ հայերեն" if hits else "TradeInvest. Crypto և թրեյդինգ դասընթաց հայերեն"
    desc = (f"Անվճար թրեյդինգ դասեր հայերեն՝ գրաֆիկներ, ինդիկատորներ, ռիսկի կառավարում, թրեյդերների սխալներ. {total} դաս։")
    page = (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><meta name="description" content="{desc}"><meta name="theme-color" content="#0A0E17">'
            f'<link rel="icon" href="data:image/svg+xml,{FAVICON}">'
            f'<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">'
            f'<link rel="preload" href="fonts/noto-sans-armenian-armenian-800-normal.woff2" as="font" type="font/woff2" crossorigin>'
            f'<style>{_font_css()}{CSS}</style></head><body>'
            f'<div class="wrap"><div class="top">{LOGO}<b>TradeInvest</b><a class="ig" href="{IG}" target="_blank" rel="noopener">@armtradeinvest</a></div>'
            f'<section class="hero"><div class="kick"><i></i>Անվճար դասեր Instagram-ում</div>'
            f'<h1>Թրեյդինգ հայերեն՝<br><span>պարզ և կարճ</span></h1>'
            f'<p class="lead">Կարճ Reels դասեր գրաֆիկների, ինդիկատորների, ռիսկի և թրեյդերների սխալների մասին։ Ամեն օր՝ նոր դաս։</p>'
            f'<div class="stats"><div class="stat"><b>{total}</b><span>դաս</span></div><div class="stat"><b>{n_series}</b><span>շարք</span></div>'
            f'<div class="stat"><b>3</b><span>դաս օրական</span></div></div>'
            f'<a class="cta" href="{IG}" target="_blank" rel="noopener">Դիտել Instagram-ում →</a>'
            f'<div class="bar"><i style="width:{100 * done_all / max(1, total):.0f}%"></i></div>'
            f'<div class="barl">Հրապարակված է {done_all}՝ {total}-ից</div></section>'
            + '<div class="course"><b>Անհատական դասընթաց</b><span>3 ամիս՝ տեսություն, վերլուծություն, պրակտիկա և ռիսկի կառավարում։ Բոնուս՝ բոտ քո ռազմավարությամբ։</span>'
              f'<a href="https://ig.me/m/armtradeinvest" target="_blank" rel="noopener">Գրիր DM «ԴԱՍ» →</a></div>'
            + (f'<h2>Վերջին դասերը</h2><div class="latest">{latest}</div>' if latest else "")
            + f'<h2>Բոլոր դասերը</h2><input class="find" id="q" type="search" placeholder="Գտնել դասը. օրինակ՝ RSI" aria-label="Գտնել դասը">'
            f'{"".join(parts)}'
            f'<footer>@armtradeinvest · Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ։'
            f'<br>Գրաֆիկները՝ <a href="https://www.tradingview.com/">TradingView</a> Lightweight Charts™ '
            f'(Copyright © 2025 TradingView, Inc.)</footer></div><script>{JS}</script>{analytics()}</body></html>')
    os.makedirs(os.path.join(out_dir, "fonts"), exist_ok=True)
    for f in FONTS:
        src = os.path.join(ASSETS, "fonts", f)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(out_dir, "fonts", f))
    open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(page)
    return os.path.join(out_dir, "index.html")
