// Daily analysis Reel v2 (1080x1920, 10 s body + 1 s end card), built on the brand library (theme «ti»).
// Every number comes from props.json, written by reels/analysis.py from real candles; nothing here is invented.
// Text stays inside the Reel safe zone (x 65-1015, y 270-1250); below it the chart's reflection fills the frame.
//
// Motion is blocked as phases (Disney-style: establish → reveal → anticipation → contact → overshoot → settle):
//   0-20    establish   header + headline legible almost at once (hook)
//   14-110  reveal      candles grow one by one (body rises open→close, wicks follow), last price counts up
//   104-120 anticipate  camera eases back a touch…
//   120-150 contact     …then pushes into the zone as it sweeps in; touches land with an impact and overshoot
//   150-200 levels      opposite level + Fibonacci draw on
//   200-260 decision    two scenario paths, then the two if/then rows
//   262-300 settle      disclaimer, resolve chime, slow drift
//   300-330 end card    brand ident + «Գրիր DM «ԴԱՍ»»
import React from "react";
import {Easing, Sequence, interpolate, useCurrentFrame} from "remotion";
import {ThemeRoot, useTheme, Cue, pr, ff, fmtNum} from "./lib/core";
import {Candles, Grid, Zone, Level, PathArrow, Touch, PriceTag, Reflection, makeScale, stackTags, OHLC} from "./lib/Chart";
import {Camera} from "./lib/Motion";
import {Label} from "./lib/Atmosphere";
import {EndCard, END_FRAMES} from "./lib/EndCard";
import {getTheme} from "./theme";

export type Props = {
  symbol: string; tf: string; asset: "BTC" | "ETH" | "GOLD" | "SPX" | "NDX"; date: string; subtitle: string;
  candles: OHLC[]; start: number;
  zone: [number, number]; zoneKind: "S" | "R"; touches: number[];
  other: number; fib: Record<string, number>; last: number;
  head: string; headAccent: string;
  scenarios: {text: string; strong: string; accent: boolean}[];
  fmt: {other: string; zone: string; last: string};
  theme?: string;
};

export const BODY = 300;
export const ANALYSIS_FRAMES = BODY + END_FRAMES;

const BOX = {x: 70, y: 690, w: 750, h: 370};        // chart plot; price tags sit to its right (x 834-984)
const outExpo = Easing.bezier(0.16, 1, 0.3, 1);
const outBack = Easing.out(Easing.back(1.7));

// Generic asset symbols (no company logos).
const Icon: React.FC<{asset: Props["asset"]; size: number}> = ({asset, size}) => {
  const t = (s: string, fs: number) => <text x="32" y={32 + fs * 0.36} textAnchor="middle" fontSize={fs} fontWeight="800" fill="#fff" fontFamily="TI Mono, monospace">{s}</text>;
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

const Header: React.FC<Props> = (P) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const a = pr(f, 0, 14, outExpo), h = pr(f, 4, 20, outExpo);
  return <>
    <div style={{position: "absolute", left: 70, right: 70, top: 282, display: "flex", alignItems: "center", gap: 22, opacity: a, translate: `0px ${(1 - a) * 24}px`}}>
      <div style={{scale: String(0.7 + 0.3 * pr(f, 0, 16, outBack))}}><Icon asset={P.asset} size={86} /></div>
      <div>
        <div style={{fontFamily: ff(t, "mono"), fontSize: P.symbol.length > 6 ? 56 : 64, fontWeight: 700, whiteSpace: "nowrap", color: t.c.fg}}>
          {P.symbol} <span style={{color: t.c.accent}}>· {P.tf}</span></div>
        <Label text={P.subtitle} size={28} />
      </div>
      <div style={{marginLeft: "auto", fontFamily: ff(t, "mono"), fontSize: 30, fontWeight: 700, color: t.c.accent, border: `3px solid ${t.c.accent}`, padding: "6px 16px", borderRadius: 10}}>{P.date}</div>
    </div>
    <div style={{position: "absolute", left: 70, right: 70, top: 414, fontFamily: ff(t, "display"), fontVariationSettings: t.type.displayVar,
      fontSize: 92, lineHeight: 0.98, letterSpacing: "-0.01em", color: t.c.fg, opacity: h, translate: `0px ${(1 - h) * 30}px`}}>
      {P.head} <span style={{color: t.c.accent, whiteSpace: "nowrap"}}>{P.headAccent}</span>
    </div>
  </>;
};

const Chart: React.FC<Props> = (P) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const CS = P.candles.slice(P.start), N = CS.length;
  const s = makeScale(CS, BOX, {pad: 0.07, include: [P.other, P.zone[0], P.zone[1]], slots: N + 4});
  const isS = P.zoneKind === "S", dir = isS ? 1 : -1;
  const [zLo, zHi] = P.zone, edge = isS ? zLo : zHi;

  // phases
  const reveal = interpolate(f, [14, 110], [0, N], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.33, 0, 0.25, 1)});
  const zone = pr(f, 120, 146, outExpo), lvl = pr(f, 150, 176, outExpo), fib = pr(f, 168, 196, outExpo);
  const pHold = pr(f, 200, 240, Easing.inOut(Easing.cubic)), pBreak = pr(f, 222, 258, Easing.inOut(Easing.cubic));
  const tagLast = pr(f, 12, 26, outExpo);

  // camera: slow push on the last price; anticipation pull-back, then a push with overshoot when the zone lands
  const drift = 0.035 * pr(f, 0, BODY, (x) => x);
  const antic = -0.012 * pr(f, 104, 120, Easing.inOut(Easing.sin));
  const push = 0.045 * interpolate(f, [120, 140, 156], [0, 1.18, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic)});
  const z = 1 + drift + antic + push;
  const cx = s.x(N - 1), cy = s.y(edge);
  // a short, decaying shake on each touch impact (deterministic)
  const touchIdx = P.touches.map(i => i - P.start).filter(i => i >= 0 && i < N);
  const impacts = touchIdx.map((_, n) => 132 + n * 8);
  const shake = impacts.reduce((acc, at) => { const d = f - at; return d >= 0 && d < 10 ? acc + Math.sin(d * 2.6) * 5 * (1 - d / 10) : acc; }, 0);

  // live last price: counts from the first visible close to the real last close while candles appear
  const lastNow = interpolate(f, [14, 110], [CS[0].c, P.last], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.33, 0, 0.25, 1)});
  const lastTxt = f < 110 ? fmtNum(lastNow, P.last < 100 ? 2 : 0) : P.fmt.last;
  const lastV = Math.min(Math.max(CS[Math.min(N - 1, Math.floor(Math.max(0, reveal - 1)))].c, s.lo), s.hi);

  // Fibonacci levels: drawn only where they don't collide with the opposite level and stay inside the plot
  const fibs = (Object.entries(P.fib) as [string, number][]).filter(([, v]) => Math.abs(s.y(v) - s.y(P.other)) > 30 && s.y(v) > BOX.y && s.y(v) < BOX.y + BOX.h);
  const tagYs = [s.y(f < 110 ? lastV : P.last), s.y(P.other), s.y(edge)];
  const dy = stackTags(tagYs, 58);

  // scenario paths, in chart coordinates (index, price): hold → towards the opposite level; break → through the zone
  const hold: [number, number][] = [[N - 1, P.last], [N + 0.6, (P.last + edge) / 2 + (isS ? 0 : 0)], [N + 1.6, (P.last + P.other) / 2], [N + 2.5, P.other]];
  const brk: [number, number][] = [[N - 1, P.last], [N + 0.8, edge + (P.last - edge) * 0.25], [N + 2.1, edge - dir * (Math.abs(zHi - zLo) + (s.hi - s.lo) * 0.06)]];

  const chart = <>
    <Grid s={s} rows={5} opacity={pr(f, 0, 20)} />
    {fibs.map(([lab, v], k) => <g key={lab} opacity={fib * 0.9}>
      <line x1={BOX.x} x2={BOX.x + BOX.w * Math.max(0, Math.min(1, fib * 1.3 - k * 0.3))} y1={s.y(v)} y2={s.y(v)} stroke={t.c.fg} strokeOpacity={0.32} strokeWidth={2} strokeDasharray="6 10" />
      <text x={BOX.x + BOX.w - 8} textAnchor="end" y={s.y(v) - 10} fontSize={26} fontWeight={700} fill={t.c.muted} fontFamily={ff(t, "mono")}>Fib {lab}</text>
    </g>)}
    <Zone s={s} lo={zLo} hi={zHi} p={zone} from={0} />
    <Candles cs={CS} s={s} reveal={reveal} focus={(i) => (zone > 0 && f < 200 ? 0.55 + 0.45 * (1 - zone) + (touchIdx.includes(i) ? 0.45 * zone : 0) : 1)} />
    {touchIdx.map((i, n) => <Touch key={i} s={s} i={i} v={isS ? CS[i].l : CS[i].h} below={isS} label={(isS ? s.y(CS[i].l) + 90 : s.y(CS[i].h) - 90) < BOX.y + BOX.h + 10 && (isS ? s.y(CS[i].l) + 90 : s.y(CS[i].h) - 90) > BOX.y ? String(n + 1) : undefined}
      p={interpolate(f, [impacts[n], impacts[n] + 8, impacts[n] + 14], [0, 1.15, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"})} />)}
    <Level s={s} v={P.other} p={lvl} from={0} />
    <PathArrow s={s} pts={hold} p={pHold} color={t.c.fg} width={6} />
    <PathArrow s={s} pts={brk} p={pBreak} color={t.c.accent} width={6} />
    {reveal >= N - 0.05 && <circle cx={s.x(N - 1)} cy={s.y(P.last)} r={9 + 3 * Math.sin(f / 5)} fill={t.c.accent} />}
  </>;

  return <svg width={1080} height={1920} style={{position: "absolute", inset: 0}}>
    <g transform={`translate(${shake},${shake * 0.4})`}>
      <Camera z={z} cx={cx} cy={cy}>
        {/* reflection of the candles only, starting below the text safe zone so it never sits behind copy */}
        <Reflection s={s} gap={206} depth={440} strength={0.24}><Candles cs={CS} s={s} reveal={reveal} /></Reflection>
        {chart}
        <PriceTag s={s} v={f < 110 ? lastV : P.last} text={lastTxt} p={tagLast} fill dy={dy[0]} w={160} />
        <PriceTag s={s} v={P.other} text={P.fmt.other} p={lvl} dy={dy[1]} w={160} />
        <PriceTag s={s} v={edge} text={P.fmt.zone} p={zone} dy={dy[2]} w={160} />
      </Camera>
    </g>
  </svg>;
};

const Scenarios: React.FC<Props> = (P) => {
  const f = useCurrentFrame();
  const t = useTheme();
  return <>
    {P.scenarios.map((sc, n) => {
      const a = pr(f, 214 + n * 24, 236 + n * 24, outExpo);
      const col = sc.accent ? t.c.accent : t.c.fg;
      return <div key={n} style={{position: "absolute", left: 70, right: 70, top: 1086 + n * 60, display: "flex", alignItems: "center", gap: 18,
        fontFamily: ff(t, "body"), fontVariationSettings: "'wght' 600, 'wdth' 100", fontSize: 40, color: t.c.fg, opacity: a, translate: `${(1 - a) * -36}px 0px`, whiteSpace: "nowrap"}}>
        <svg width={30} height={14} style={{flex: "none"}}><line x1={2} x2={28} y1={7} y2={7} stroke={col} strokeWidth={5} strokeLinecap="round" strokeDasharray={sc.accent ? "0" : "7 6"} /></svg>
        {sc.text} → <b style={{color: col, fontVariationSettings: "'wght' 800, 'wdth' 100"}}>{sc.strong}</b>
      </div>;
    })}
    <div style={{position: "absolute", left: 70, right: 70, top: 1212, fontFamily: ff(t, "body"), fontVariationSettings: "'wght' 500, 'wdth' 100",
      fontSize: 28, color: t.c.muted, opacity: pr(f, 262, 280)}}>
      Կրթական վերլուծություն է, ոչ թե ֆինանսական խորհուրդ
    </div>
  </>;
};

export const Analysis: React.FC<Props> = (P) => {
  const theme = getTheme(P.theme ?? "ti");
  const touches = P.touches.filter(i => i >= P.start).length;
  return (
    <ThemeRoot theme={theme}>
      <Sequence durationInFrames={BODY} layout="none">
        <Chart {...P} />
        <Header {...P} />
        <Scenarios {...P} />
      </Sequence>
      <Sequence from={BODY} layout="none"><EndCard cta="dm" /></Sequence>
      <Cue at={0} name="hook" volume={0.4} />
      <Cue at={14} name="build" volume={0.25} />
      <Cue at={120} name="draw" volume={0.45} />
      {Array.from({length: touches}, (_, n) => <Cue key={n} at={132 + n * 8} name="hit" volume={0.4} />)}
      <Cue at={150} name="reveal" volume={0.4} />
      <Cue at={200} name="draw" volume={0.35} />
      {P.scenarios.map((_, n) => <Cue key={`s${n}`} at={214 + n * 24} name="word" volume={0.45} />)}
      <Cue at={268} name="resolve" volume={0.4} />
      <Cue at={BODY} name="ident" volume={0.65} />
    </ThemeRoot>
  );
};
