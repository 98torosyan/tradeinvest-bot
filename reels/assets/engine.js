const EASE={out:x=>1-Math.pow(1-x,3),inOut:x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,
 expo:x=>x>=1?1:1-Math.pow(2,-10*x),back:x=>{const c=1.5;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2);}};
const clamp01=v=>Math.max(0,Math.min(1,v)); const prog=(t,a,d)=>clamp01((t-a)/d);
let SCENES=[]; const HOOKS=[];
function setupReel(){
  SCENES=[...document.querySelectorAll('.scene')].map(el=>({el,a:+el.dataset.in,b:+el.dataset.out,items:[...el.querySelectorAll('[data-fx]')]}));
  document.querySelectorAll('[data-fx="draw"]').forEach(p=>{const L=p.getTotalLength();p.dataset.len=L;p.style.strokeDasharray=L;p.style.strokeDashoffset=L;});
}
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
      it.textContent=(it.dataset.pre||'')+v.toFixed(+(it.dataset.dec||0))+(it.dataset.post||'');break;}
    case 'scalex':it.style.transform=`scaleX(${EASE.inOut(raw)})`;break;
    case 'pop':{const e=raw<=0?0:EASE.back(raw);it.style.opacity=clamp01(raw*3);it.style.transform=`scale(${.4+.6*e})`;break;}
    case 'card':it.style.opacity=k;it.style.transform=`translateY(${(1-k)*40}px) scale(${.96+.04*k})`;break;
  }
}
window.seek=function(t){
  for(const sc of SCENES){
    const vis=t>=sc.a-.001&&t<sc.b; const inK=EASE.out(prog(t,sc.a,.7)); const outK=EASE.inOut(prog(t,sc.b-.55,.55));
    const life=prog(t,sc.a,sc.b-sc.a);
    sc.el.style.visibility=vis?'visible':'hidden';
    sc.el.style.opacity=Math.min(inK,1-outK);
    sc.el.style.transform=`translateX(${(1-inK)*70-outK*70}px) scale(${1+.03*life})`;
    if(vis)sc.items.forEach(it=>applyFx(it,t-sc.a));
  }
  HOOKS.forEach(h=>h(t));
};
// Logo: blocks drop in one by one, then the accent block rises.
function logoFx(t0){
  HOOKS.push(t=>{document.querySelectorAll('.logo rect').forEach((r,i)=>{
    const a=t0+(+r.dataset.i)*.16, k=prog(t,a,.75);
    const e=k<=0?0:EASE.back(k); const drop=(1-e)*-260;
    const lift=r.dataset.lift?-34*EASE.inOut(prog(t,t0+1.25,.55)):0;
    r.style.opacity=clamp01(k*4); r.style.transform=`translateY(${drop+lift}px)`;
  });});
}
