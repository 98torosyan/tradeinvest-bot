"""Free mini course page («Թրեյդինգի 7 քայլ») for new followers and «ԴԱՍ» leads: <site>/start/.
Brand TI Rise (Ink / Paper / Amber). Static, self-contained, mobile-first, no cookies; progress kept in localStorage."""
import html
import json
import os
import shutil

from .site import LOGO, FAVICON, IG, _font_css, analytics

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "minicourse.json")
DM = "https://ig.me/m/armtradeinvest"
PDF = "TradeInvest-Risk-Guide.pdf"
PDF_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", PDF)

CSS = """
:root{--ink:#0B0B0C;--ink2:#141416;--ink3:#1C1C1F;--line:rgba(242,239,232,.10);--paper:#F2EFE8;--mut:#A3A09A;--amb:#FF8A00;--amb2:#FFA640;--ok:#34C98A;--bad:#F2505E}
*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth}html,body{overflow-x:hidden}
body{background:var(--ink);color:var(--paper);font-family:Arm,system-ui,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.55}
a{color:inherit}
.wrap{max-width:760px;margin:0 auto;padding:0 20px 80px}
.top{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;padding:14px 20px;margin:0 -20px;background:rgba(11,11,12,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.top svg{width:26px;height:31px}.top b{font-weight:800;font-size:17px}.top b span{color:var(--amb);font-weight:500}
.top .pr{margin-left:auto;font:700 13px Mono,monospace;color:var(--mut)}
.prog{position:sticky;top:59px;z-index:5;height:3px;margin:0 -20px;background:var(--ink3)}.prog i{display:block;height:100%;width:0;background:var(--amb);transition:width .5s cubic-bezier(.2,.8,.2,1)}
.hero{padding:56px 0 36px;position:relative}
.hero:before{content:"";position:absolute;right:-120px;top:-40px;width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,rgba(255,138,0,.16),transparent 65%);pointer-events:none}
.kick{display:inline-flex;align-items:center;gap:10px;font-size:13px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--amb)}
.kick i{width:22px;height:2px;background:var(--amb)}
h1{margin-top:18px;font-size:clamp(40px,9vw,68px);line-height:1.02;font-weight:800;letter-spacing:-.02em}
h1 span{color:var(--amb)}
.lead{margin-top:18px;font-size:19px;color:#D9D5CC;max-width:560px}
.meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}
.chip{border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:14px;color:var(--mut)}.chip b{color:var(--paper)}
.go{display:inline-flex;align-items:center;gap:10px;margin-top:28px;background:var(--amb);color:var(--ink);font-weight:800;font-size:17px;padding:15px 26px;border-radius:14px;text-decoration:none;transition:transform .2s,box-shadow .2s}
.go:hover{transform:translateY(-2px);box-shadow:0 10px 30px rgba(255,138,0,.25)}
.pdf{display:block;margin-top:16px;color:var(--amb2);font-weight:700;font-size:15px;text-decoration:none}.pdf:hover{text-decoration:underline}
.toc{margin:10px 0 34px;display:grid;gap:8px}
.toc a{display:flex;align-items:center;gap:14px;padding:12px 14px;border:1px solid var(--line);border-radius:12px;text-decoration:none;color:#D9D5CC;font-size:15px;transition:border-color .2s,background .2s}
.toc a:hover{border-color:rgba(255,138,0,.5);background:var(--ink2)}
.toc a em{font:700 13px Mono,monospace;font-style:normal;color:var(--mut);width:26px}.toc a.done em{color:var(--ok)}
.toc a small{margin-left:auto;color:var(--mut);font-size:13px;white-space:nowrap;padding-left:10px}
.ls{margin-top:22px;border:1px solid var(--line);border-radius:22px;background:linear-gradient(180deg,var(--ink2),var(--ink));overflow:hidden;scroll-margin-top:80px}
.lh{display:flex;align-items:flex-start;gap:18px;padding:26px 24px 8px}
.num{font-size:64px;line-height:.8;font-weight:800;color:var(--amb);letter-spacing:-.04em;font-family:Arm}
.lh .tg{font-size:12px;font-weight:700;letter-spacing:.18em;color:var(--mut)}
.lh h2{margin-top:6px;font-size:clamp(22px,4.6vw,28px);line-height:1.18;font-weight:800}
.lb{padding:8px 24px 6px}.lb p{margin-top:12px;font-size:17px;color:#E2DED6}
.rule{margin:18px 24px 0;padding:16px 18px;border-left:3px solid var(--amb);background:rgba(255,138,0,.07);border-radius:0 12px 12px 0;font-weight:700;font-size:16px}
.rule small{display:block;font-size:11px;letter-spacing:.18em;color:var(--amb);margin-bottom:4px}
.qz{margin:20px 24px 24px;padding:18px;border:1px solid var(--line);border-radius:16px}
.qz .q{font-weight:800;font-size:16px}.qz .q small{display:block;font-size:11px;letter-spacing:.18em;color:var(--mut);font-weight:700;margin-bottom:6px}
.qz button{display:block;width:100%;text-align:left;margin-top:10px;padding:13px 15px;border-radius:12px;border:1px solid var(--line);background:var(--ink3);color:var(--paper);font:500 15px Arm,sans-serif;cursor:pointer;transition:border-color .2s,background .2s}
.qz button:hover{border-color:rgba(255,138,0,.55)}
.qz button.ok{border-color:var(--ok);background:rgba(52,201,138,.12)}.qz button.no{border-color:var(--bad);background:rgba(242,80,94,.10)}
.qz .why{display:none;margin-top:12px;font-size:14px;color:#D9D5CC}.qz.answered .why{display:block}
.end{margin-top:40px;padding:34px 26px;border-radius:24px;background:var(--amb);color:var(--ink);text-align:center}
.end h2{font-size:clamp(26px,6vw,36px);line-height:1.1;font-weight:800}
.end p{margin-top:12px;font-size:17px;font-weight:500}
.end a{display:inline-flex;margin-top:22px;background:var(--ink);color:var(--paper);text-decoration:none;font-weight:800;padding:15px 26px;border-radius:14px}
.end small{display:block;margin-top:14px;font-size:13px;opacity:.75}
footer{margin-top:36px;color:var(--mut);font-size:13px;text-align:center}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto}}
"""

JS = """
(function(){
  var K='ti_minicourse_v1', st={};
  try{st=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
  var total=document.querySelectorAll('.qz').length;
  function save(){try{localStorage.setItem(K,JSON.stringify(st))}catch(e){}}
  function paint(){
    var n=0;for(var k in st){if(st[k])n++}
    document.querySelector('.prog i').style.width=(100*n/total)+'%';
    document.querySelector('.top .pr').textContent=n+' / '+total;
    document.querySelectorAll('.toc a').forEach(function(a){a.classList.toggle('done',!!st[a.dataset.n])});
  }
  document.querySelectorAll('.qz').forEach(function(q){
    var ans=+q.dataset.a, n=q.dataset.n;
    q.querySelectorAll('button').forEach(function(b,i){
      b.addEventListener('click',function(){
        if(q.classList.contains('answered'))return;
        q.classList.add('answered');
        b.classList.add(i===ans?'ok':'no');
        if(i!==ans)q.querySelectorAll('button')[ans].classList.add('ok');
        st[n]=1;save();paint();
      });
    });
  });
  paint();
})();
"""


def _lesson(l):
    q = l["quiz"]
    opts = "".join(f"<button type='button'>{html.escape(o)}</button>" for o in q["options"])
    body = "".join(f"<p>{html.escape(p)}</p>" for p in l["body"])
    return (f'<article class="ls" id="l{l["n"]}"><div class="lh"><div class="num">{l["n"]:02d}</div><div>'
            f'<div class="tg">{html.escape(l["tag"])} · {html.escape(l["time"])}</div><h2>{html.escape(l["title"])}</h2></div></div>'
            f'<div class="lb">{body}</div>'
            f'<div class="rule"><small>ԿԱՆՈՆ</small>{html.escape(l["rule"])}</div>'
            f'<div class="qz" data-a="{q["answer"]}" data-n="{l["n"]}"><div class="q"><small>ՍՏՈՒԳԻՐ ՔԵԶ</small>{html.escape(q["q"])}</div>{opts}'
            f'<div class="why">{html.escape(q["why"])}</div></div></article>')


def build(out_dir):
    c = json.load(open(SRC, encoding="utf-8"))
    ls = c["lessons"]
    toc = "".join(f'<a href="#l{l["n"]}" data-n="{l["n"]}"><em>{l["n"]:02d}</em>{html.escape(l["title"])}<small>{html.escape(l["time"])}</small></a>' for l in ls)
    mins = sum(int(l["time"].split()[0]) for l in ls)
    title = f'{c["title"]} · TradeInvest'
    desc = "Անվճար մինի դասընթաց հայերեն՝ շուկա, մոմեր, support/resistance, ռիսկ, stop-loss, Risk/Reward, թրեյդերի պլան։"
    page = (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><meta name="description" content="{desc}"><meta name="theme-color" content="#0B0B0C">'
            f'<link rel="icon" href="data:image/svg+xml,{FAVICON}"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{desc}">'
            f'<style>{_font_css().replace("url(fonts/", "url(../fonts/")}{CSS}</style></head><body><div class="wrap">'
            f'<div class="top">{LOGO}<b>Trade<span>Invest</span></b><span class="pr">0 / {len(ls)}</span></div><div class="prog"><i></i></div>'
            f'<section class="hero"><div class="kick"><i></i>Free mini course</div>'
            f'<h1>{html.escape(c["title"])}<br><span>պարզ հայերենով</span></h1>'
            f'<p class="lead">{html.escape(c["subtitle"])}։ Կարդա հերթով, պատասխանիր հարցերին և ստուգիր քեզ։</p>'
            f'<div class="meta"><span class="chip"><b>{len(ls)}</b> դաս</span><span class="chip"><b>~{mins}</b> րոպե</span><span class="chip"><b>{len(ls)}</b> ինքնաստուգում</span></div>'
            f'<a class="go" href="#l1">Սկսել առաջին դասից →</a>'
            f'<a class="pdf" href="{PDF}" download>⬇ Անվճար PDF՝ «Ռիսկի կառավարում. 6 կանոն»</a>'
            f'<a class="pdf" href="../tools/">🧮 Թրեյդերի հաշվիչներ՝ position size, R/R →</a></section>'
            f'<nav class="toc" aria-label="Դասերի ցանկ">{toc}</nav>'
            f'{"".join(_lesson(l) for l in ls)}'
            f'<section class="end"><h2>Ուզում ես սովորել համակարգված՝ պրակտիկայով</h2>'
            f'<p>Անհատական դասընթաց՝ 3 ամիս, տեսություն, վերլուծություն, պրակտիկա և ռիսկի կառավարում։ Բոնուս՝ բոտ քո ռազմավարությամբ։</p>'
            f'<a href="{DM}" target="_blank" rel="noopener">Գրիր DM «ԴԱՍ» →</a><small>Պատասխանում ենք 24 ժամվա ընթացքում</small></section>'
            f'<footer><a href="{IG}" target="_blank" rel="noopener">@armtradeinvest</a> · <a href="../tools/">Հաշվիչներ</a> · <a href="../">Բոլոր դասերը</a><br>'
            f'Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ։ Թրեյդինգը կապված է կորստի ռիսկի հետ։</footer>'
            f'</div><script>{JS}</script>{analytics()}</body></html>')
    os.makedirs(os.path.join(out_dir, "start"), exist_ok=True)
    if os.path.exists(PDF_SRC):
        shutil.copy(PDF_SRC, os.path.join(out_dir, "start", PDF))
    path = os.path.join(out_dir, "start", "index.html")
    open(path, "w", encoding="utf-8").write(page)
    return path
