const EASE={out:x=>1-Math.pow(1-x,3),inOut:x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,
 expo:x=>x>=1?1:1-Math.pow(2,-10*x),back:x=>{const c=1.5;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2);}};
const clamp01=v=>Math.max(0,Math.min(1,v)); const prog=(t,a,d)=>clamp01((t-a)/d);
let SCENES=[]; const HOOKS=[];
function setupReel(){
  SCENES=[...document.querySelectorAll('.scene')].map(el=>({el,a:+el.dataset.in,b:+el.dataset.out,items:[...el.querySelectorAll('[data-fx]')]}));
  document.querySelectorAll('[data-fx="draw"]').forEach(p=>{const L=p.getTotalLength();p.dataset.len=L;p.style.strokeDasharray=L;p.style.strokeDashoffset=L;});
  // split hero lines into letters for the "chars" style (Armenian marks stay with their letter)
  document.querySelectorAll('[data-fx="chars"]').forEach(el=>{const t=el.textContent;el.textContent='';
    t.split(/( )/).forEach(part=>{if(part===' '){el.appendChild(document.createTextNode(' '));return;}   // words never break inside
      const w=document.createElement('span');w.className='cw';
      [...part].forEach(c=>{const s=document.createElement('span');s.className='ch';s.textContent=c;w.appendChild(s);});el.appendChild(w);});});
  document.querySelectorAll('[data-fx="type"]').forEach(el=>{el.dataset.full=el.textContent;});
}
// deterministic flicker for neon (same frame -> same value)
function flick(x,seed){const s=Math.sin((x*91.7+seed)*12.9898)*43758.5453;return s-Math.floor(s);}
function applyFx(it,local){
  const at=+(it.dataset.at||0),dur=+(it.dataset.dur||.7),raw=prog(local,at,dur),k=EASE.out(raw);
  switch(it.dataset.fx){
    case 'rise':it.style.opacity=k;it.style.transform=`translateY(${(1-k)*50}px)`;break;
    case 'fade':it.style.opacity=k;break;
    case 'lines':it.querySelectorAll('.ln').forEach((ln,i)=>{const r=prog(local,at+i*.14,dur),e=EASE.expo(r);
      ln.style.opacity=r>0?1:0;ln.style.transform=`translateY(${(1-e)*110}%) rotate(${(1-e)*3}deg)`;});break;
    case 'words':{const rate=+it.dataset.rate;it.querySelectorAll('.w').forEach((w,i)=>{const r=EASE.out(prog(local,at+i*rate,.45));
      w.style.opacity=.14+.86*r;w.style.transform=`translateY(${(1-r)*14}px)`;w.style.filter=`blur(${(1-r)*3}px)`;});break;}
    case 'draw':it.style.strokeDashoffset=(+it.dataset.len)*(1-EASE.inOut(raw));break;
    case 'count':{const f=+(it.dataset.from||0),to=+it.dataset.to,v=f+(to-f)*EASE.expo(raw);
      let txt=Math.abs(v).toFixed(+(it.dataset.dec||0));
      if(it.dataset.grp){const [i,d]=txt.split('.');txt=i.replace(/\B(?=(\d{3})+(?!\d))/g,',')+(d?'.'+d:'');}
      it.textContent=(it.dataset.pre||'')+(v<0?'−':'')+txt+(it.dataset.post||'');break;}
    case 'scalex':it.style.transform=`scaleX(${EASE.inOut(raw)})`;break;
    case 'scaley':it.style.transform=`scaleY(${EASE.inOut(raw)})`;break;
    case 'shrink':it.style.transform=`scaleX(${1-raw})`;it.style.opacity=raw>=1?0:1;break;
    case 'fill':it.style.transform=`scaleX(${(+it.dataset.w||1)*EASE.out(raw)})`;break;
    case 'pop':{const e=raw<=0?0:EASE.back(raw);it.style.opacity=clamp01(raw*3);it.style.transform=`scale(${.4+.6*e})`;break;}
    case 'card':it.style.opacity=k;it.style.transform=`translateY(${(1-k)*40}px) scale(${.96+.04*k})`;break;
    case 'tilt':{const e=EASE.out(raw);it.style.opacity=clamp01(raw*2.5);
      it.style.transform=`perspective(1400px) rotateX(${(1-e)*28}deg) translateY(${(1-e)*90}px) scale(${.92+.08*e})`;break;}
    case 'flip':{const e=EASE.inOut(raw);it.style.opacity=raw>0?1:0;it.style.transform=`perspective(1400px) rotateY(${(1-e)*-80}deg)`;break;}
    case 'slam':{const e=raw<=0?0:EASE.back(raw);it.style.opacity=clamp01(raw*3);
      it.style.transform=`scale(${1.18-.18*e})`;it.style.filter=`blur(${(1-clamp01(raw*2.2))*6}px)`;break;}
    case 'mask':{const s=it.firstElementChild;if(!s)break;const e=EASE.expo(raw);it.style.opacity=raw>0?1:0;
      s.style.transform=`translateY(${(1-e)*115}%)`;break;}
    case 'type':{const full=it.dataset.full||'';const n=[...full].length;const c=Math.floor(n*raw);
      it.textContent=[...full].slice(0,c).join('')||'​';it.style.opacity=raw>0?1:0;
      it.classList.toggle('typing',raw>0&&raw<1||(raw>=1&&Math.floor(local*2.2)%2===0&&local<at+dur+1.4));break;}
    case 'glow':{if(raw<=0){it.style.opacity=0;break;}const f=raw<.6?(flick(Math.floor(local*24),at*7)>.45?1:.15):1;
      it.style.opacity=f;it.style.transform=`scale(${1.05-.05*EASE.out(raw)})`;break;}
    case 'chars':it.querySelectorAll('.ch').forEach((c,i)=>{const r=EASE.back(prog(local,at+i*.035,.45));
      c.style.opacity=clamp01(prog(local,at+i*.035,.2));c.style.transform=`translateY(${(1-r)*60}px) rotate(${(1-r)*8}deg)`;});break;
    case 'strike':it.style.backgroundSize=`${EASE.inOut(raw)*100}% 10px`;it.style.opacity=raw>=1?.75:1;break;
    case 'state':{const on=local>=at;it.parentElement.classList.toggle(it.dataset.cls,on);break;}
  }
}
// scene transitions: body[data-trans] = slide | push | zoom | iris | wipe
function sceneFx(sc,t){
  const mode=document.body.dataset.trans||'slide',el=sc.el;
  const inK=EASE.out(prog(t,sc.a,.6)),outK=EASE.inOut(prog(t,sc.b-.5,.5)),life=prog(t,sc.a,sc.b-sc.a);
  el.style.clipPath='none';el.style.filter='none';
  if(mode==='zoom'){el.style.opacity=Math.min(inK,1-outK);el.style.transform=`scale(${1.14-.14*inK-.08*outK+.02*life})`;
    el.style.filter=`blur(${(1-inK)*10+outK*8}px)`;}
  else if(mode==='push'){el.style.opacity=Math.min(clamp01(inK*1.4),1-outK);el.style.transform=`translateY(${(1-inK)*120-outK*120}px)`;}
  else if(mode==='iris'){const r=EASE.inOut(prog(t,sc.a,.65));el.style.opacity=1-outK;
    el.style.clipPath=sc.a<0.01?'none':`circle(${r*130}% at 50% 48%)`;el.style.transform=`scale(${1+.03*life-.04*outK})`;}
  else if(mode==='wipe'){const r=EASE.inOut(prog(t,sc.a,.45));el.style.opacity=1-outK;
    el.style.clipPath=sc.a<0.01?'none':`inset(0 ${100-r*100}% 0 0)`;el.style.transform='none';}
  else{el.style.opacity=Math.min(inK,1-outK);el.style.transform=`translateX(${(1-inK)*70-outK*70}px) scale(${1+.03*life})`;}
}
window.seek=function(t){
  for(const sc of SCENES){
    const vis=t>=sc.a-.001&&t<sc.b;
    sc.el.style.visibility=vis?'visible':'hidden';
    if(!vis)continue;
    sceneFx(sc,t);
    sc.items.forEach(it=>applyFx(it,t-sc.a));
  }
  HOOKS.forEach(h=>h(t));
};
// captions: body[data-cap] = pop | rise | type | blur | mark
function captionFx(){
  HOOKS.push(t=>{const mode=document.body.dataset.cap||'pop';
    for(const sc of SCENES){if(!sc.el.classList.contains('beat'))continue;const l=t-sc.a;
      sc.el.querySelectorAll('.chunk').forEach(c=>{const s=+c.dataset.s,on=l>=s&&l<+c.dataset.e+(c.nextElementSibling?0:9);
        c.style.display=on?'block':'none';if(!on)return;const r=clamp01((l-s)/.32);
        c.style.transform='none';c.style.opacity=1;c.style.filter='none';c.style.clipPath='none';c.classList.remove('typing');
        if(mode==='pop'){const k=Math.min(1,EASE.back(clamp01((l-s)/.22)));c.style.transform=`scale(${.88+.12*k})`;}
        else if(mode==='rise'){const k=EASE.expo(r);c.style.transform=`translateY(${(1-k)*70}px)`;c.style.opacity=clamp01(r*2);
          c.style.clipPath=`inset(0 0 ${(1-k)*100}% 0)`;}
        else if(mode==='blur'){const k=EASE.out(r);c.style.filter=`blur(${(1-k)*14}px)`;c.style.opacity=k;
          c.style.transform=`scale(${1.08-.08*k})`;}
        else if(mode==='type'){const k=clamp01((l-s)/.5);c.style.clipPath=`inset(0 ${(1-k)*100}% 0 0)`;
          if(k<1)c.classList.add('typing');}
        else if(mode==='mark'){const k=EASE.out(clamp01((l-s)/.25));c.style.transform=`translateY(${(1-k)*30}px)`;c.style.opacity=k;}
      });
      sc.el.querySelectorAll('.w').forEach(w=>{const s=+w.dataset.s,e=+w.dataset.e,on=l>=s&&l<e;w.classList.toggle('on',on);
        if(mode==='mark'){const k=on?EASE.out(clamp01((l-s)/.25)):0;w.style.backgroundSize=`${k*100}% 100%`;w.style.color=k>=.98?'var(--onacc)':'#fff';}});
    }});
}
// Logo: blocks drop in one by one, then the accent block rises.
function logoFx(t0){
  HOOKS.push(t=>{document.querySelectorAll('.scene .logo rect').forEach((r,i)=>{
    const a=t0+(+r.dataset.i)*.16, k=prog(t,a,.75);
    const e=k<=0?0:EASE.back(k); const drop=(1-e)*-260;
    const lift=r.dataset.lift?-34*EASE.inOut(prog(t,t0+1.25,.55)):0;
    r.style.opacity=clamp01(k*4); r.style.transform=`translateY(${drop+lift}px)`;
  });});
}
