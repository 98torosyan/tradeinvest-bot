// Daily analysis Reel (1080x1920, 10 s). All numbers come from props.json, written by reels/analysis.py
// from real candles; nothing here is invented. Text stays inside the Reel safe zone (x 65-1015, y 270-1250).
import React from "react";
import {registerRoot, Composition, AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, staticFile, Easing, getInputProps} from "remotion";

type C = {o: number; h: number; l: number; c: number};
export type Props = {
  symbol: string; tf: string; asset: "BTC" | "ETH" | "GOLD" | "SPX" | "NDX"; date: string; subtitle: string;
  candles: C[]; start: number;
  zone: [number, number]; zoneKind: "S" | "R"; touches: number[];
  other: number; fib: Record<string, number>; last: number;
  head: string; headAccent: string;
  scenarios: {text: string; strong: string; accent: boolean}[];
  fmt: {other: string; zone: string; last: string};
};

const INK = "#0B0B0C", PAPER = "#F4F2EE", AMB = "#FF8A00", AMB2 = "#FFA640", MUT = "#8E8A83", DN = "#5A5650";
const X0 = 70, X1 = 840, XC = 750, Y0 = 600, Y1 = 1035, AX = 858;
const E = Easing.bezier(0.2, 0.8, 0.2, 1);
const pr = (f: number, a: number, b: number) => interpolate(f, [a, b], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: E});

// Generic asset symbols (no company logos).
const Icon = ({asset, size}: {asset: Props["asset"]; size: number}) => {
  const t = (s: string, fs: number, fill = "#fff") => <text x="32" y={32 + fs * 0.36} textAnchor="middle" fontSize={fs} fontWeight="800" fill={fill} fontFamily="Mono, Arial">{s}</text>;
  return (
    <svg width={size} height={size} viewBox="0 0 64 64">
      {asset === "BTC" && <><circle cx="32" cy="32" r="32" fill="#F7931A" />{t("₿", 40)}</>}
      {asset === "ETH" && <><circle cx="32" cy="32" r="32" fill="#3C3C3D" />
        <path d="M32 10 L46 33 L32 41 L18 33 Z" fill="#fff" opacity=".9" /><path d="M32 44 L46 36 L32 55 L18 36 Z" fill="#fff" opacity=".7" /></>}
      {asset === "GOLD" && <><circle cx="32" cy="32" r="32" fill="#C9A227" />
        <path d="M14 42 L20 28 L44 28 L50 42 Z" fill="#FFE7A0" stroke="#8A6A10" strokeWidth="2.5" strokeLinejoin="round" /><path d="M23 28 L26 20 L38 20 L41 28" fill="#FFD95E" stroke="#8A6A10" strokeWidth="2.5" strokeLinejoin="round" /></>}
      {asset === "SPX" && <><rect width="64" height="64" rx="16" fill="#1F3A68" />{t("500", 22)}</>}
      {asset === "NDX" && <><rect width="64" height="64" rx="16" fill="#0E6E5C" />{t("100", 22)}</>}
    </svg>
  );
};

const Tag = ({y, text, fill, a}: {y: number; text: string; fill: boolean; a: number}) => (
  <g opacity={a} transform={`translate(${(1 - a) * 30},0)`}>
    <rect x={AX} y={y - 24} width={152} height={48} rx={10} fill={fill ? AMB : INK} stroke={AMB} strokeWidth={3} />
    <text x={AX + 76} y={y + 10} textAnchor="middle" fontSize={text.length > 7 ? 24 : 27} fontWeight={700} fill={fill ? INK : AMB} fontFamily="Mono">{text}</text>
  </g>
);

export const Analysis: React.FC<Props> = (P) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const CS = P.candles.slice(P.start);
  const N = CS.length;
  const lo = Math.min(...CS.map(c => c.l)), hi = Math.max(...CS.map(c => c.h)), pad = (hi - lo) * 0.06;
  const ys = (v: number) => Y1 - (v - (lo - pad)) / (hi - lo + 2 * pad) * (Y1 - Y0);
  const xs = (i: number) => X0 + (i + 0.5) * (XC - X0) / N;
  const w = (XC - X0) / N * 0.62;
  const isS = P.zoneKind === "S";

  const pop = spring({frame: f, fps, config: {damping: 14}});
  const shown = interpolate(f, [18, 105], [0, N], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const zone = pr(f, 108, 135), oLine = pr(f, 150, 175), fib = pr(f, 170, 195), path = pr(f, 200, 245), alt = pr(f, 230, 255);
  const disc = pr(f, 262, 280);
  const [zLo, zHi] = P.zone;
  const edge = isS ? zLo : zHi;                       // the side of the zone price would break through
  const lx = xs(N - 1), ly = ys(P.last), tx = X1 - 6, ty = ys(P.other);
  const tIdx = P.touches.map(i => i - P.start).filter(i => i >= 0 && i < N);
  const pulse = 1 + 0.25 * Math.sin(f / 5);
  const dir = isS ? 1 : -1;                            // alternative (break) arrow: down below support, up above resistance
  const ay = ys(edge) + dir * 46;

  return (
    <AbsoluteFill style={{background: INK, fontFamily: "Arm", color: PAPER}}>
      <style>{`@font-face{font-family:Arm;src:url(${staticFile("ttf/NotoSansArmenian.ttf")})}@font-face{font-family:Mono;font-weight:700;src:url(${staticFile("fonts/jetbrains-mono-latin-700-normal.woff2")})}`}</style>
      <div style={{position: "absolute", left: 70, right: 70, top: 280, display: "flex", alignItems: "center", gap: 22, opacity: pop, transform: `translateY(${(1 - pop) * 30}px)`}}>
        <Icon asset={P.asset} size={86} />
        <div>
          <div style={{fontFamily: "Mono", fontSize: P.symbol.length > 6 ? 58 : 66, fontWeight: 700, whiteSpace: "nowrap"}}>{P.symbol} <span style={{color: AMB}}>· {P.tf}</span></div>
          <div style={{fontSize: 29, fontWeight: 600, color: MUT, letterSpacing: ".06em"}}>{P.subtitle}</div>
        </div>
        <div style={{marginLeft: "auto", fontFamily: "Mono", fontSize: 30, fontWeight: 700, color: AMB, border: `3px solid ${AMB}`, padding: "6px 16px", borderRadius: 10}}>{P.date}</div>
      </div>
      <div style={{position: "absolute", left: 70, right: 70, top: 412, fontSize: 64, fontWeight: 800, lineHeight: 1.04, fontStretch: "80%", opacity: pr(f, 10, 30), transform: `translateY(${(1 - pr(f, 10, 30)) * 24}px)`}}>
        {P.head} <span style={{color: AMB, whiteSpace: "nowrap"}}>{P.headAccent}</span>
      </div>

      <svg width={1080} height={1920} style={{position: "absolute"}}>
        {[0, 1, 2, 3, 4].map(g => <line key={g} x1={X0} x2={X1} y1={Y0 + g * (Y1 - Y0) / 4} y2={Y0 + g * (Y1 - Y0) / 4} stroke="rgba(255,255,255,.05)" strokeWidth={2} />)}
        <rect x={X0} y={ys(zHi)} width={(X1 - X0) * zone} height={Math.max(14, ys(zLo) - ys(zHi))} fill="rgba(255,138,0,.17)" stroke={AMB} strokeOpacity={.55} strokeWidth={2} rx={6} />
        {Object.entries(P.fib).filter(([, v]) => Math.abs(ys(v) - ys(P.other)) > 26 && ys(v) > Y0 - 10 && ys(v) < Y1 + 10).map(([lab, v]) => (
          <g key={lab} opacity={fib * 0.85}>
            <line x1={X0} x2={X0 + (X1 - X0) * fib} y1={ys(v)} y2={ys(v)} stroke={PAPER} strokeOpacity={.35} strokeWidth={2} strokeDasharray="6 10" />
            <text x={X1 - 4} textAnchor="end" y={ys(v) - 10} fontSize={26} fontWeight={700} fill={MUT} fontFamily="Mono">Fib {lab}</text>
          </g>
        ))}
        {CS.map((c, i) => {
          const a = Math.max(0, Math.min(1, shown - i)); if (a <= 0) return null;
          const up = c.c >= c.o, col = up ? PAPER : DN;
          const top = ys(Math.max(c.o, c.c)), bot = ys(Math.min(c.o, c.c));
          return <g key={i} opacity={a} transform={`translate(0,${(1 - a) * 18})`}>
            <line x1={xs(i)} x2={xs(i)} y1={ys(c.h)} y2={ys(c.l)} stroke={col} strokeWidth={2.5} />
            <rect x={xs(i) - w / 2} y={top} width={w} height={Math.max(3, bot - top)} fill={up ? col : INK} stroke={col} strokeWidth={2.5} rx={1.5} />
          </g>;
        })}
        <line x1={X0} x2={X0 + (X1 - X0) * oLine} y1={ty} y2={ty} stroke={AMB} strokeWidth={4} strokeLinecap="round" />
        {tIdx.map((i, n) => { const a = pr(f, 120 + n * 9, 136 + n * 9); return <circle key={i} cx={xs(i)} cy={ys(isS ? CS[i].l : CS[i].h)} r={24 * a + 1} fill="none" stroke={AMB2} strokeWidth={4} opacity={a} />; })}
        <path d={`M${lx},${ly} C${lx + 50},${ly} ${tx - 40},${ty + dir * 60} ${tx},${ty}`} stroke={PAPER} strokeWidth={5} fill="none" strokeDasharray="12 10"
          style={{clipPath: `inset(0 ${100 - path * 100}% 0 0)`}} />
        <circle cx={tx} cy={ty} r={11 * pr(f, 240, 250)} fill={PAPER} />
        <g opacity={alt}>
          <path d={`M${lx},${ly + dir * 8} L${lx + 20},${ay}`} stroke={AMB} strokeWidth={5} strokeDasharray="10 9" fill="none" />
          <path d={`M${lx + 8},${ay - dir * 12} L${lx + 21},${ay + dir * 8} L${lx + 34},${ay - dir * 16}`} stroke={AMB} strokeWidth={5} fill="none" strokeLinejoin="round" />
        </g>
        <circle cx={lx} cy={ly} r={8 * pulse} fill={AMB} opacity={shown >= N ? 1 : 0} />
      </svg>
      <svg width={1080} height={1920} style={{position: "absolute"}}>
        <Tag y={ty} text={P.fmt.other} fill={false} a={oLine} />
        <Tag y={ly} text={P.fmt.last} fill={true} a={pr(f, 100, 115)} />
        <Tag y={ys(edge) + (isS ? 6 : -6)} text={P.fmt.zone} fill={false} a={zone} />
      </svg>

      {P.scenarios.map((s, n) => {
        const a = pr(f, 215 + n * 25, 235 + n * 25);
        return <div key={n} style={{position: "absolute", left: 70, right: 70, top: 1090 + n * 56, display: "flex", alignItems: "center", gap: 18, fontSize: 38, fontWeight: 600, color: "#D9D5CC", opacity: a, transform: `translateX(${(1 - a) * -30}px)`, whiteSpace: "nowrap"}}>
          <span style={{width: 14, height: 14, borderRadius: 7, background: s.accent ? AMB : PAPER, flex: "none"}} />
          {s.text} → <b style={{color: s.accent ? AMB : PAPER}}>{s.strong}</b>
        </div>;
      })}
      <div style={{position: "absolute", left: 70, right: 70, top: 1210, fontSize: 28, fontWeight: 600, color: MUT, opacity: disc}}>
        Կրթական վերլուծություն է, ոչ թե ֆինանսական խորհուրդ
      </div>
    </AbsoluteFill>
  );
};

const DEMO: Props = {
  symbol: "BTCUSD", tf: "4H", asset: "BTC", date: "03.11", subtitle: "ՕՐՎԱ ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ",
  candles: [{o: 1, h: 2, l: 0.5, c: 1.5}, {o: 1.5, h: 2.2, l: 1, c: 1.2}], start: 0,
  zone: [0.5, 0.7], zoneKind: "S", touches: [0], other: 2.2, fib: {}, last: 1.2,
  head: "Demo", headAccent: "", scenarios: [], fmt: {other: "2.2", zone: "0.5", last: "1.2"},
};

registerRoot(() => (
  <Composition id="Analysis" component={Analysis as any} durationInFrames={300} fps={30} width={1080} height={1920}
    defaultProps={{...DEMO, ...(getInputProps() as Partial<Props>)}} />
));
