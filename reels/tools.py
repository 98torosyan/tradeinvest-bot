"""Trader tools page (<site>/tools/): position size, Risk/Reward, recovery and leverage calculators.
Armenian, brand TI Rise, mobile-first, no external libraries, nothing leaves the browser."""
import os

from .site import LOGO, FAVICON, IG, _font_css, analytics

DM = "https://ig.me/m/armtradeinvest"

CSS = """
:root{--ink:#0B0B0C;--ink2:#141416;--ink3:#1C1C1F;--line:rgba(242,239,232,.10);--paper:#F2EFE8;--mut:#A3A09A;--amb:#FF8A00;--amb2:#FFA640;--up:#34C98A;--dn:#F2505E}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--ink);color:var(--paper);font-family:Arm,system-ui,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.5}
a{color:inherit}
.wrap{max-width:760px;margin:0 auto;padding:0 20px 80px}
.top{display:flex;align-items:center;gap:12px;padding:16px 0;border-bottom:1px solid var(--line)}
.top svg{width:26px;height:31px}.top b{font-weight:800;font-size:17px}.top b span{color:var(--amb);font-weight:500}
.top a.bk{margin-left:auto;font-size:14px;color:var(--mut);text-decoration:none}
.hero{padding:44px 0 18px}
.kick{display:inline-flex;align-items:center;gap:10px;font-size:13px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--amb)}
.kick i{width:22px;height:2px;background:var(--amb)}
h1{margin-top:14px;font-size:clamp(34px,8vw,56px);line-height:1.04;font-weight:800;letter-spacing:-.02em}h1 span{color:var(--amb)}
.lead{margin-top:14px;font-size:17px;color:#D9D5CC;max-width:560px}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0 6px}
.tabs button{border:1px solid var(--line);background:var(--ink2);color:var(--paper);border-radius:999px;padding:9px 15px;font:600 14px Arm,sans-serif;cursor:pointer}
.tabs button.on{background:var(--amb);color:var(--ink);border-color:var(--amb)}
.card{margin-top:16px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(180deg,var(--ink2),var(--ink));padding:22px}
.card h2{font-size:22px;font-weight:800}.card .d{margin-top:6px;color:var(--mut);font-size:14px}
.grid{margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
label{display:block;font-size:13px;color:var(--mut);font-weight:600}
input{margin-top:6px;width:100%;background:var(--ink3);border:1px solid var(--line);border-radius:12px;padding:12px 13px;color:var(--paper);font:700 17px Mono,monospace;outline:none}
input:focus{border-color:rgba(255,138,0,.6)}
.out{margin-top:18px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
.o{border-radius:14px;padding:14px;background:rgba(255,138,0,.07);border:1px solid rgba(255,138,0,.28)}
.o small{display:block;font-size:12px;color:var(--mut);font-weight:700;letter-spacing:.04em}
.o b{display:block;margin-top:6px;font:800 22px Mono,monospace;color:var(--amb2)}
.o.big{grid-column:1/-1}.o.big b{font-size:30px;color:var(--paper)}
.o .up{color:var(--up)}.o .dn{color:var(--dn)}
.note{margin-top:12px;font-size:13px;color:var(--mut)}
.hide{display:none}
.end{margin-top:34px;padding:28px 22px;border-radius:22px;background:var(--amb);color:var(--ink);text-align:center}
.end h2{font-size:26px;line-height:1.15;font-weight:800}.end a{display:inline-flex;margin-top:16px;background:var(--ink);color:var(--paper);text-decoration:none;font-weight:800;padding:13px 22px;border-radius:12px}
footer{margin-top:30px;color:var(--mut);font-size:13px;text-align:center}
@media(max-width:340px){.grid,.out{grid-template-columns:1fr}}
"""

JS = """
(function(){
  var $=function(id){return document.getElementById(id)};
  var n=function(id){var v=parseFloat(($(id).value||'').replace(',','.'));return isFinite(v)?v:NaN};
  var f=function(v,d){if(!isFinite(v))return '—';return v.toLocaleString('en-US',{maximumFractionDigits:d==null?2:d}).replace(/,/g,' ')};
  function size(){
    var acc=n('acc'),rp=n('rp'),en=n('en'),sl=n('sl');
    var risk=acc*rp/100, dist=Math.abs(en-sl), units=risk/dist, val=units*en;
    $('o_risk').textContent='$'+f(risk);
    $('o_dist').textContent='$'+f(dist,4)+(en?' ('+f(dist/en*100)+'%)':'');
    $('o_units').textContent=f(units,6);
    $('o_val').textContent='$'+f(val);
    $('o_lev').textContent=isFinite(val/acc)?'x'+f(Math.max(1,val/acc),1):'—';
  }
  function rr(){
    var en=n('r_en'),sl=n('r_sl'),tp=n('r_tp');
    var r=Math.abs(en-sl), w=Math.abs(tp-en), k=w/r;
    $('o_rr').textContent=isFinite(k)?'1 : '+f(k,2):'—';
    $('o_be').textContent=isFinite(k)?f(100/(1+k),1)+'%':'—';
  }
  function rec(){
    var l=n('loss'); var g=l/(100-l)*100;
    $('o_rec').textContent=(isFinite(g)&&l<100&&l>0)?'+'+f(g,1)+'%':'—';
  }
  function lev(){
    var x=n('lev'); $('o_lev2').textContent=(x>0)?'≈ −'+f(100/x,2)+'%':'—';
  }
  ['acc','rp','en','sl'].forEach(function(i){$(i).addEventListener('input',size)});
  ['r_en','r_sl','r_tp'].forEach(function(i){$(i).addEventListener('input',rr)});
  $('loss').addEventListener('input',rec); $('lev').addEventListener('input',lev);
  size();rr();rec();lev();
  document.querySelectorAll('.tabs button').forEach(function(b){
    b.addEventListener('click',function(){
      document.querySelectorAll('.tabs button').forEach(function(x){x.classList.toggle('on',x===b)});
      document.querySelectorAll('.card[data-t]').forEach(function(c){c.classList.toggle('hide',c.dataset.t!==b.dataset.t)});
    });
  });
})();
"""


def _inp(id_, label, val):
    return f'<div><label for="{id_}">{label}</label><input id="{id_}" inputmode="decimal" value="{val}"></div>'


def build(out_dir):
    title = "Թրեյդերի հաշվիչներ · TradeInvest"
    desc = "Position size, Risk/Reward, վնասի վերականգնում և leverage՝ անվճար հաշվիչներ հայերենով։"
    cards = (
        '<section class="card" data-t="size"><h2>Position size</h2><p class="d">Որքան գնել, որ վնասը stop-ում չգերազանցի ընտրած ռիսկը։</p>'
        f'<div class="grid">{_inp("acc", "Հաշիվ, $", "1000")}{_inp("rp", "Ռիսկ, %", "1")}{_inp("en", "Մուտք", "100")}{_inp("sl", "Stop-loss", "95")}</div>'
        '<div class="out"><div class="o big"><small>ՉԱՓԸ (ՀԱՏ)</small><b id="o_units">—</b></div>'
        '<div class="o"><small>ՌԻՍԿ $</small><b id="o_risk">—</b></div><div class="o"><small>STOP-Ի ՀԵՌԱՎՈՐՈՒԹՅՈՒՆ</small><b id="o_dist">—</b></div>'
        '<div class="o"><small>ԴԻՐՔԻ ԱՐԺԵՔ</small><b id="o_val">—</b></div><div class="o"><small>ԱՆՀՐԱԺԵՇՏ LEVERAGE</small><b id="o_lev">—</b></div></div>'
        '<p class="note">Չափ = (Հաշիվ × Ռիսկ %) ÷ |Մուտք − Stop|։ Միջնորդավճարները և slippage-ը հաշվի չեն առնված։</p></section>'
        '<section class="card hide" data-t="rr"><h2>Risk / Reward</h2><p class="d">Որքան է հնարավոր շահույթը ռիսկի համեմատ և քանի տոկոս պետք է ճիշտ լինել։</p>'
        f'<div class="grid">{_inp("r_en", "Մուտք", "100")}{_inp("r_sl", "Stop-loss", "95")}{_inp("r_tp", "Թիրախ", "115")}</div>'
        '<div class="out"><div class="o big"><small>RISK / REWARD</small><b id="o_rr">—</b></div>'
        '<div class="o big"><small>ԶՐՈՅԱԿԱՆ ԱՐԴՅՈՒՆՔԻ ՀԱՄԱՐ ՊԵՏՔ Է ՃԻՇՏ ԼԻՆԵԼ</small><b id="o_be">—</b></div></div></section>'
        '<section class="card hide" data-t="rec"><h2>Վնասի վերականգնում</h2><p class="d">Որքան աճ է պետք՝ վնասից հետո նախկին գումարին վերադառնալու համար։</p>'
        f'<div class="grid">{_inp("loss", "Վնաս, %", "50")}</div>'
        '<div class="out"><div class="o big"><small>ՊԵՏՔ Է ԱՃ</small><b id="o_rec" class="dn">—</b></div></div></section>'
        '<section class="card hide" data-t="lev"><h2>Leverage</h2><p class="d">Մոտավորապես որքան շարժում դեմ քեզ է ջնջում ամբողջ մարժան։</p>'
        f'<div class="grid">{_inp("lev", "Leverage, x", "10")}</div>'
        '<div class="out"><div class="o big"><small>ԳՆԻ ՇԱՐԺՈՒՄ ԴԵՄ ՔԵԶ</small><b id="o_lev2">—</b></div></div>'
        '<p class="note">Պարզեցված հաշվարկ։ Իրականում liquidation-ը տեղի է ունենում ավելի շուտ (maintenance margin, միջնորդավճարներ)։</p></section>')
    page = (f'<!doctype html><html lang="hy"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><meta name="description" content="{desc}"><meta name="theme-color" content="#0B0B0C">'
            f'<link rel="icon" href="data:image/svg+xml,{FAVICON}"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:image" content="https://98torosyan.github.io/tradeinvest-bot/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">'
            f'<style>{_font_css().replace("url(fonts/", "url(../fonts/")}{CSS}</style></head><body><div class="wrap">'
            f'<div class="top">{LOGO}<b>Trade<span>Invest</span></b><a class="bk" href="../start/">← Մինի դասընթաց</a></div>'
            '<section class="hero"><div class="kick"><i></i>Free tools</div><h1>Թրեյդերի <span>հաշվիչներ</span></h1>'
            '<p class="lead">Հաշվիր ռիսկը մինչև մուտքը։ Ամեն ինչ աշխատում է քո բրաուզերում, ոչինչ չի ուղարկվում։</p></section>'
            '<div class="tabs"><button class="on" data-t="size">Position size</button><button data-t="rr">Risk/Reward</button>'
            '<button data-t="rec">Վերականգնում</button><button data-t="lev">Leverage</button></div>'
            f'{cards}'
            f'<section class="end"><h2>Ուզում ես սովորել համակարգված՝ պրակտիկայով</h2><a href="{DM}" target="_blank" rel="noopener">Գրիր DM «ԴԱՍ» →</a></section>'
            f'<footer><a href="{IG}" target="_blank" rel="noopener">@armtradeinvest</a> · <a href="../start/">Մինի դասընթաց</a><br>'
            'Կրթական գործիք է, ոչ թե ֆինանսական խորհուրդ։ Թրեյդինգը կապված է կորստի ռիսկի հետ։</footer>'
            f'</div><script>{JS}</script>{analytics()}</body></html>')
    os.makedirs(os.path.join(out_dir, "tools"), exist_ok=True)
    path = os.path.join(out_dir, "tools", "index.html")
    open(path, "w", encoding="utf-8").write(page)
    return path
