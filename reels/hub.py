"""Home page of the site (<site>/index.html): one clean hub for everything a new follower needs.
Replaces the old lesson-library page (those Reels are being archived), brand TI Rise."""
import os

from .site import LOGO, FAVICON, IG, _font_css, analytics

DM = "https://ig.me/m/armtradeinvest"

CSS = """
:root{--ink:#0B0B0C;--ink2:#141416;--line:rgba(242,239,232,.10);--paper:#F2EFE8;--mut:#A3A09A;--amb:#FF8A00;--amb2:#FFA640}
*{box-sizing:border-box;margin:0;padding:0}
html,body{overflow-x:hidden}
body{background:var(--ink);color:var(--paper);font-family:Arm,system-ui,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.5}
a{color:inherit;text-decoration:none}
.wrap{max-width:720px;margin:0 auto;padding:0 20px 70px}
.top{display:flex;align-items:center;gap:12px;padding:18px 0}
.top svg{width:28px;height:33px}.top b{font-weight:800;font-size:18px}.top b span{color:var(--amb);font-weight:500}
.top a.ig{margin-left:auto;border:1px solid rgba(255,138,0,.5);color:var(--amb2);border-radius:999px;padding:7px 14px;font-weight:700;font-size:14px}
.hero{position:relative;padding:46px 0 24px}
.hero:before{content:"";position:absolute;right:-140px;top:-60px;width:440px;height:440px;border-radius:50%;background:radial-gradient(circle,rgba(255,138,0,.17),transparent 65%);pointer-events:none}
.kick{display:inline-flex;align-items:center;gap:10px;font-size:13px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--amb)}.kick i{width:22px;height:2px;background:var(--amb)}
h1{margin-top:16px;font-size:clamp(38px,9vw,64px);line-height:1.02;font-weight:800;letter-spacing:-.02em}h1 span{color:var(--amb)}
.lead{margin-top:16px;font-size:18px;color:#D9D5CC;max-width:540px}
.cards{margin-top:26px;display:grid;gap:12px}
.c{display:flex;align-items:center;gap:16px;padding:18px;border:1px solid var(--line);border-radius:18px;background:var(--ink2);transition:border-color .2s,transform .2s}
.c:hover{border-color:rgba(255,138,0,.55);transform:translateY(-2px)}
.c .ic{flex:none;width:52px;height:52px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:26px;background:rgba(255,138,0,.12);border:1px solid rgba(255,138,0,.35)}
.c b{display:block;font-size:18px;font-weight:800}.c small{display:block;margin-top:2px;color:var(--mut);font-size:14px}
.c em{margin-left:auto;font-style:normal;color:var(--amb2);font-weight:800;font-size:20px}
.c.main{background:var(--amb);border-color:var(--amb);color:var(--ink)}.c.main small{color:#3A2A10}.c.main .ic{background:rgba(11,11,12,.1);border-color:rgba(11,11,12,.25)}.c.main em{color:var(--ink)}
.sched{margin-top:34px;border:1px solid var(--line);border-radius:18px;padding:18px 20px}
.sched h2{font-size:14px;letter-spacing:.16em;color:var(--mut);font-weight:700}
.sched div{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid var(--line);font-size:15px}.sched div:last-child{border:0}
.sched span{font:700 15px Mono,monospace;color:var(--amb2)}
footer{margin-top:34px;color:var(--mut);font-size:13px;text-align:center}
"""


def _card(href, icon, title, sub, main=False, ext=False):
    tgt = ' target="_blank" rel="noopener"' if ext else ""
    return (f'<a class="c{" main" if main else ""}" href="{href}"{tgt}><span class="ic">{icon}</span>'
            f'<span><b>{title}</b><small>{sub}</small></span><em>→</em></a>')


def build(out_dir):
    title = "TradeInvest · Թրեյդինգ հայերեն"
    desc = "Թրեյդինգ պարզ հայերենով՝ անվճար մինի դասընթաց, PDF ուղեցույց, հաշվիչներ և ամենօրյա վերլուծություն։"
    cards = "".join([
        _card("start/", "🎓", "Անվճար մինի դասընթաց", "«Թրեյդինգի 7 քայլ»՝ ~25 րոպե, հարցերով", main=True),
        _card("start/TradeInvest-Risk-Guide.pdf", "📄", "PDF՝ Ռիսկի կառավարում", "6 կանոն, բանաձև և checklist մեկ էջում"),
        _card("tools/", "🧮", "Թրեյդերի հաշվիչներ", "Position size, Risk/Reward, leverage"),
        _card(IG, "📊", "Ամենօրյա դասեր և վերլուծություն", "@armtradeinvest Instagram-ում", ext=True),
        _card(DM, "✉️", "Անհատական դասընթաց", "Գրիր DM «ԴԱՍ»՝ օնլայն կամ օֆլայն, հայերեն", ext=True),
    ])
    sched = "".join(f"<div>{a}<span>{b}</span></div>" for a, b in [
        ("Կարճ դաս (Reel)", "12:37"), ("Կարուսել կամ պոստեր", "15:07"), ("Օրվա վերլուծություն (Reel)", "19:07"),
        ("Շաբաթվա ամփոփում", "Կիրակի 17:07")])
    page = (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><meta name="description" content="{desc}"><meta name="theme-color" content="#0B0B0C">'
            f'<link rel="icon" href="data:image/svg+xml,{FAVICON}"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">'
            f'<style>{_font_css()}{CSS}</style></head><body><div class="wrap">'
            f'<div class="top">{LOGO}<b>Trade<span>Invest</span></b><a class="ig" href="{IG}" target="_blank" rel="noopener">@armtradeinvest</a></div>'
            '<section class="hero"><div class="kick"><i></i>Trading Academy</div>'
            '<h1>Թրեյդինգ՝ <span>պարզ հայերենով</span></h1>'
            '<p class="lead">Ռիսկի կառավարում, գրաֆիկներ և թրեյդերի հոգեբանություն՝ առանց խոստումների և «արագ փողի»։</p>'
            f'<div class="cards">{cards}</div></section>'
            f'<section class="sched"><h2>ԺԱՄԱՆԱԿԱՑՈՒՅՑ · ԵՐԵՎԱՆԻ ԺԱՄՈՎ</h2>{sched}</section>'
            '<footer>Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ։ Թրեյդինգը կապված է կորստի ռիսկի հետ։</footer>'
            f'</div>{analytics()}</body></html>')
    path = os.path.join(out_dir, "index.html")
    open(path, "w", encoding="utf-8").write(page)
    return path
