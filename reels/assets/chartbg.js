/* TradeInvest animated trading backgrounds (deterministic: everything is a function of t).
   Styles: candles | line | depth | tape | heat. Data: window.BGDATA, scenes: window.BGSCENES. */
(function(){
const W=1080,H=1920,cv=document.getElementById('bgc'),ctx=cv.getContext('2d');
const D=window.BGDATA,S=window.BGSCENES,UP='#2fd18b',DN='#ff5f6d';
function rgba(hex,a){const n=parseInt(hex.slice(1),16);return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`;}
function sceneAt(t){for(const s of S){if(t>=s.a&&t<s.b)return s;}return S[S.length-1];}
function grid(acc){ctx.strokeStyle='rgba(255,255,255,.045)';ctx.lineWidth=2;
 for(let x=0;x<=W;x+=120){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
 for(let y=0;y<=H;y+=120){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}}
function range(c){let lo=1e18,hi=-1e18;for(const k of c){lo=Math.min(lo,k.l);hi=Math.max(hi,k.h);}return [lo,hi];}
function candles(t,s){const n=46,c=D.candles,off=Math.floor(s.seed%Math.max(1,c.length-n-40));
 const shift=(t-s.a)*0.55, i0=off+Math.floor(shift), fr=shift-Math.floor(shift);
 const vis=c.slice(i0,i0+n+1);const [lo,hi]=range(vis);const top=330,bot=1600,cw=W/(n-1);
 const Y=v=>bot-(v-lo)/(hi-lo||1)*(bot-top);
 vis.forEach((k,i)=>{const x=(i-fr)*cw;const up=k.c>=k.o;const col=up?UP:DN;
  ctx.strokeStyle=rgba(col,.55);ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(x,Y(k.h));ctx.lineTo(x,Y(k.l));ctx.stroke();
  ctx.fillStyle=rgba(col,.42);const y1=Y(Math.max(k.o,k.c)),y2=Y(Math.min(k.o,k.c));ctx.fillRect(x-cw*.32,y1,cw*.64,Math.max(3,y2-y1));});
 const last=vis[vis.length-2]||vis[0];const ly=Y(last.c);ctx.setLineDash([12,12]);ctx.strokeStyle=rgba(s.acc,.55);ctx.lineWidth=3;
 ctx.beginPath();ctx.moveTo(0,ly);ctx.lineTo(W,ly);ctx.stroke();ctx.setLineDash([]);
 if(D.real){ctx.fillStyle=rgba(s.acc,.85);ctx.fillRect(W-210,ly-26,210,52);ctx.fillStyle='#0b1220';ctx.font='700 30px ArmSans,sans-serif';
 ctx.fillText(D.symbol+' '+last.c.toLocaleString('en-US',{maximumFractionDigits:last.c>100?0:2}),W-200,ly+11);}}
function line(t,s){const c=D.candles,n=90,off=Math.floor((s.seed*7)%Math.max(1,c.length-n-5));const vis=c.slice(off,off+n);
 const [lo,hi]=range(vis);const top=420,bot=1560,dx=W/(n-1),Y=v=>bot-(v-lo)/(hi-lo||1)*(bot-top);
 const p=Math.min(1,(t-s.a)/Math.max(.8,(s.b-s.a)*.7));const m=Math.max(2,Math.floor(n*(.35+.65*p)));
 const g=ctx.createLinearGradient(0,top,0,bot);g.addColorStop(0,rgba(s.acc,.30));g.addColorStop(1,rgba(s.acc,0));
 ctx.beginPath();ctx.moveTo(0,bot);for(let i=0;i<m;i++)ctx.lineTo(i*dx,Y(vis[i].c));ctx.lineTo((m-1)*dx,bot);ctx.closePath();ctx.fillStyle=g;ctx.fill();
 ctx.beginPath();for(let i=0;i<m;i++){const y=Y(vis[i].c);i?ctx.lineTo(i*dx,y):ctx.moveTo(0,y);}ctx.strokeStyle=rgba(s.acc,.8);ctx.lineWidth=5;
 ctx.shadowColor=s.acc;ctx.shadowBlur=24;ctx.stroke();ctx.shadowBlur=0;
 const ex=(m-1)*dx,ey=Y(vis[m-1].c),pu=.6+.4*Math.sin(t*5);ctx.fillStyle=rgba(s.acc,.9);ctx.beginPath();ctx.arc(ex,ey,10+6*pu,0,7);ctx.fill();}
function depth(t,s){const mid=W/2,base=1560,top=600,k=t-s.a;
 for(const side of [-1,1]){ctx.beginPath();ctx.moveTo(mid,base);let acc=0;
  for(let i=0;i<=40;i++){const x=mid+side*i*(mid/40);acc+=8+14*Math.abs(Math.sin(i*1.7+s.seed+k*.8))+i*.9;ctx.lineTo(x,base-Math.min(base-top,acc*1.1));}
  ctx.lineTo(side<0?0:W,base);ctx.closePath();ctx.fillStyle=rgba(side<0?UP:DN,.22);ctx.fill();ctx.strokeStyle=rgba(side<0?UP:DN,.6);ctx.lineWidth=4;ctx.stroke();}
 ctx.fillStyle='rgba(255,255,255,.35)';ctx.font='600 30px ArmSans,sans-serif';ctx.fillText('BID',70,base+60);ctx.fillText('ASK',W-140,base+60);}
function tape(t,s){const rows=D.coins,k=(t-s.a)*38;ctx.font='700 46px ArmSans,sans-serif';
 for(let r=0;r<16;r++){const y=((r*128+k)%(16*128))-60;const q=rows[(r+Math.floor(s.seed))%rows.length];
  ctx.fillStyle='rgba(255,255,255,.22)';ctx.fillText(q.s,90,y);if(q.p){ctx.fillStyle='rgba(255,255,255,.30)';ctx.fillText(q.p,420,y);}
  ctx.fillStyle=rgba(q.ch>=0?UP:DN,.6);ctx.fillText((q.ch>=0?'+':'')+q.ch.toFixed(2)+'%',W-310,y);}}
function heat(t,s){const rows=D.coins,cols=3,cw=W/cols,ch=230,k=t-s.a;
 for(let i=0;i<24;i++){const q=rows[(i+Math.floor(s.seed))%rows.length],x=(i%cols)*cw,y=300+Math.floor(i/cols)*ch;
  const a=.10+.18*Math.min(1,Math.abs(q.ch)/6)*(0.85+.15*Math.sin(k*2+i));ctx.fillStyle=rgba(q.ch>=0?UP:DN,a);ctx.fillRect(x+8,y+8,cw-16,ch-16);
  ctx.fillStyle='rgba(255,255,255,.38)';ctx.font='800 50px ArmSans,sans-serif';ctx.fillText(q.s,x+34,y+100);
  ctx.font='600 34px ArmSans,sans-serif';ctx.fillText((q.ch>=0?'+':'')+q.ch.toFixed(1)+'%',x+34,y+160);}}
function plain(){}
const STY={candles,line,depth,tape,heat,plain};
HOOKS.unshift(t=>{const s=sceneAt(t);ctx.fillStyle='#070b14';ctx.fillRect(0,0,W,H);
 const g=ctx.createRadialGradient(W/2,H*.42,80,W/2,H*.42,1300);g.addColorStop(0,rgba(s.acc,.16));g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
 grid();ctx.save();const z=1+.035*Math.sin((t-s.a)*.6);ctx.translate(W/2,H/2);ctx.scale(z,z);ctx.translate(-W/2,-H/2);
 (STY[s.style]||candles)(t,s);ctx.restore();
 const v=ctx.createLinearGradient(0,0,0,H);v.addColorStop(0,'rgba(5,8,15,.55)');v.addColorStop(.35,'rgba(5,8,15,.15)');v.addColorStop(.7,'rgba(5,8,15,.25)');v.addColorStop(1,'rgba(5,8,15,.8)');ctx.fillStyle=v;ctx.fillRect(0,0,W,H);});
})();
