// «Իրական chart դաս» — 35 s lesson Reel on a REAL chart. Every candle, level and % comes from props
// (reels/chart_lesson.py); nothing is invented here. Text stays inside the Reel safe zone (x 65–1015, y 270–1250).
// Flow: hook (legible at frame 0, real chart ghosted behind) → concept while the chart draws in →
// the pattern marked on the chart → «Ի՞նչ եղավ հետո» (the next candles appear) → rule + CTA → end card.
import React from "react";
import {Sequence, useCurrentFrame, interpolate, Easing} from "remotion";
import {ThemeRoot, useTheme, Cue, pr, ff} from "./lib/core";
import {Words} from "./lib/Kinetic";
import {EndCard, END_FRAMES} from "./lib/EndCard";
import {getTheme, Theme} from "./theme";

// Clean frame (owner, Nov 2026): no viewfinder corners and no orange floor line — only what helps the viewer.
const TI0 = getTheme("ti");
const CLEAN: Theme = {...TI0, fx: {...TI0.fx!, corners: undefined, floorY: undefined}} as Theme;

type C = {o: number; h: number; l: number; c: number};
type Mark = {type: string; i?: number; i1?: number; i2?: number; v?: number; v1?: number; v2?: number; lo?: number; hi?: number;
  at?: "h" | "l"; label?: string; small?: boolean};
export type ChartLessonProps = {
  symbol: string; tf: string; asset: string; date: string; dir: number; topic: string;
  candles: C[]; signal: number; marks: Mark[];
  hook: string; concept: string[]; label: string; rule: string; outcome: string[]; worked: boolean; entry: string;
  lines?: {vals: number[]; accent?: boolean; dash?: boolean}[];          // overlays on price (EMA, Bollinger bands)
  panel?: {vals: number[]; vals2?: number[]; lo: number; hi: number; levels: number[]; label: string; hist?: number[]};   // RSI / MACD
};

export const CL = {concept: 75, signal: 300, after: 600, rule: 810, body: 1020};
export const CL_TOTAL = CL.body + END_FRAMES;

const E = Easing.bezier(0.2, 0.8, 0.2, 1);
const p = (f: number, a: number, b: number) => interpolate(f, [a, b], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: E});
const X0 = 70, X1 = 955;          // right edge kept clear of Instagram's side buttons

const Icon: React.FC<{asset: string}> = ({asset}) => {
  const t = useTheme();
  const bg: Record<string, string> = {BTC: "#F7931A", ETH: "#3C3C3D", GOLD: "#C9A227", SPX: "#1F3A68", NDX: "#0E6E5C"};
  const sym: Record<string, string> = {BTC: "₿", ETH: "Ξ", GOLD: "Au", SPX: "500", NDX: "100"};
  return <div style={{width: 76, height: 76, borderRadius: asset === "SPX" || asset === "NDX" ? 18 : 38, background: bg[asset] ?? "#333",
    display: "flex", alignItems: "center", justifyContent: "center", fontFamily: ff(t, "mono"), fontWeight: 800,
    fontSize: (sym[asset] ?? "").length > 2 ? 26 : 40, color: "#fff", flex: "none"}}>{sym[asset]}</div>;
};

const Chart: React.FC<{P: ChartLessonProps}> = ({P}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const A = t.c.accent, FG = t.c.fg, DN = t.c.down, MUT = t.c.muted;
  const PN = P.panel, hasR = !!PN;
  const py = (v: number) => 1155 - (v - (PN ? PN.lo : 0)) / ((PN ? PN.hi - PN.lo : 1) || 1) * 112;
  const Y0 = 690, Y1 = hasR ? 1000 : 1170;
  const CS = P.candles, N = CS.length, S = P.signal;
  const vals = [...CS.flatMap(c => [c.h, c.l]), ...(P.lines ?? []).flatMap(l => l.vals)];
  const lo = Math.min(...vals), hi = Math.max(...vals), pad = (hi - lo) * 0.08;
  const ys = (v: number) => Y1 - (v - (lo - pad)) / (hi - lo + 2 * pad) * (Y1 - Y0);
  const xs = (i: number) => X0 + (i + 0.5) * (X1 - X0) / N;
  const w = (X1 - X0) / N * 0.62;

  // how many candles are visible: ghost during the hook, draw-in during the concept, the rest after the signal
  const drawn = interpolate(f, [CL.concept, CL.signal - 20], [S * 0.35, S + 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const after = interpolate(f, [CL.after + 10, CL.after + 110], [0, N - S - 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const shown = f < CL.after ? Math.max(f < CL.concept ? S + 1 : 0, drawn) : S + 1 + after;
  const ghost = f < CL.concept ? 0.2 : interpolate(f, [CL.concept, CL.concept + 20], [0.2, 1], {extrapolateRight: "clamp"});
  const mk = p(f, CL.signal + 20, CL.signal + 70);           // pattern marks
  const focus = f >= CL.signal && f < CL.after ? 1 - 0.55 * p(f, CL.signal + 10, CL.signal + 40) * (1 - p(f, CL.after - 30, CL.after)) : 1;
  const sx = xs(S), pulse = 1 + 0.18 * Math.sin(f / 5);
  const entryY = ys(CS[S].c);
  const good = P.worked ? A : t.c.warn;

  const line = (vals2: number[] | undefined, col: string, wdt: number, dash?: string) => {
    if (!vals2) return null;
    const k = Math.min(vals2.length, Math.ceil(shown));
    const d = vals2.slice(0, k).map((v, i) => `${i ? "L" : "M"}${xs(i).toFixed(1)},${ys(v).toFixed(1)}`).join(" ");
    return <path d={d} stroke={col} strokeWidth={wdt} fill="none" strokeDasharray={dash} strokeLinecap="round" strokeLinejoin="round" opacity={ghost} />;
  };

  return <svg width={1080} height={1920} style={{position: "absolute", left: 0, top: 0}}>
    {[0, 1, 2, 3, 4].map(g => <line key={g} x1={X0} x2={X1} y1={Y0 + g * (Y1 - Y0) / 4} y2={Y0 + g * (Y1 - Y0) / 4} stroke={t.c.grid} strokeWidth={2} />)}
    {/* signal column highlight */}
    <rect x={sx - w * 1.4} y={Y0 - 10} width={w * 2.8} height={Y1 - Y0 + 20} rx={10} fill={A} opacity={0.10 * mk} />
    {/* zones under candles */}
    {P.marks.filter(m => m.type === "zone" || m.type === "box").map((m, k) => {
      const x1 = xs((m.i1 ?? 0)) - w, x2 = m.type === "box" ? xs(m.i2 ?? S) + w : X0 + (X1 - X0) * (0.25 + 0.75 * mk);
      return <g key={k} opacity={mk}>
        <rect x={x1} y={ys(m.hi!)} width={Math.max(0, x2 - x1)} height={Math.max(8, ys(m.lo!) - ys(m.hi!))} rx={6} fill={t.c.zone} stroke={A} strokeOpacity={0.7} strokeWidth={2.5} />
        {m.label && <text x={m.type === "zone" ? X1 - 8 : x1 + 12} textAnchor={m.type === "zone" ? "end" : "start"} y={P.dir > 0 ? ys(m.lo!) + 36 : ys(m.hi!) - 12}
          fontSize={28} fontWeight={700} fill={A} fontFamily={ff(t, "mono")}>{m.label}</text>}
      </g>;
    })}
    {(P.lines ?? []).map((l, k) => <React.Fragment key={k}>{line(l.vals, l.accent ? A : MUT, 4, l.dash ? "10 9" : undefined)}</React.Fragment>)}
    {CS.map((c, i) => {
      const a = Math.max(0, Math.min(1, shown - i)); if (a <= 0) return null;
      const up = c.c >= c.o, col = up ? FG : DN;
      const top = ys(Math.max(c.o, c.c)), bot = ys(Math.min(c.o, c.c));
      const dim = i === S ? 1 : (i < S ? focus : 1);
      return <g key={i} opacity={a * ghost * dim} transform={`translate(0,${(1 - a) * 16})`}>
        <line x1={xs(i)} x2={xs(i)} y1={ys(c.h)} y2={ys(c.l)} stroke={i === S ? A : col} strokeWidth={2.6} />
        <rect x={xs(i) - w / 2} y={top} width={w} height={Math.max(3, bot - top)} fill={i === S ? A : (up ? col : t.c.bg)} stroke={i === S ? A : col} strokeWidth={2.6} rx={1.5} />
      </g>;
    })}
    {P.marks.map((m, k) => {
      if (m.type === "hline") {
        const x1 = xs(m.i1 ?? 0), x2 = x1 + (X1 - x1) * mk;
        return <g key={k}><line x1={x1} x2={x2} y1={ys(m.v!)} y2={ys(m.v!)} stroke={A} strokeWidth={4} strokeDasharray="14 10" strokeLinecap="round" />
          {m.label && <text x={x1 + 40} y={ys(m.v!) + (P.dir > 0 ? 40 : -16)} fontSize={28} fontWeight={700} fill={A} fontFamily={ff(t, "mono")} opacity={mk}>{m.label}</text>}</g>;
      }
      if (m.type === "circle") {
        const c = CS[m.i!]; const cy = m.at === "h" ? ys(c.h) : ys(c.l);
        const a = p(f, CL.signal + 30 + k * 8, CL.signal + 55 + k * 8);
        return <circle key={k} cx={xs(m.i!)} cy={cy} r={(m.small ? 18 : 30) * a * (m.i === S ? pulse : 1)} fill="none" stroke={t.c.a} strokeWidth={4.5} opacity={a} />;
      }
      if (m.type === "seg") {
        const x1 = xs(m.i1!), y1 = ys(m.v1!), x2 = xs(m.i2!), y2 = ys(m.v2!);
        return <line key={k} x1={x1} y1={y1} x2={x1 + (x2 - x1) * mk} y2={y1 + (y2 - y1) * mk} stroke={A} strokeWidth={5} strokeLinecap="round" />;
      }
      if (m.type === "dot") return <circle key={k} cx={xs(m.i!)} cy={ys(m.v!)} r={13 * mk * pulse} fill={A} />;
      return null;
    })}
    {/* entry line + outcome after the signal */}
    {f >= CL.after && <g opacity={p(f, CL.after, CL.after + 15)}>
      <line x1={sx} x2={X1} y1={entryY} y2={entryY} stroke={FG} strokeOpacity={0.5} strokeWidth={2.5} strokeDasharray="6 8" />
      <rect x={sx + w * 1.4} y={Y0 - 10} width={Math.max(0, xs(S + 1 + after) - sx)} height={Y1 - Y0 + 20} rx={10} fill={good} opacity={0.07} />
    </g>}
    {PN && <g opacity={ghost}>
      <rect x={X0} y={1025} width={X1 - X0} height={135} rx={12} fill={t.c.surface} opacity={0.55} />
      {PN.levels.map(v => <line key={v} x1={X0} x2={X1} y1={py(v)} y2={py(v)} stroke={MUT} strokeOpacity={0.35} strokeWidth={2} strokeDasharray="5 8" />)}
      {PN.hist && PN.hist.slice(0, Math.ceil(shown)).map((v, i) => <rect key={i} x={xs(i) - w / 2} width={w} y={Math.min(py(v), py(0))} height={Math.abs(py(v) - py(0))}
        fill={v >= 0 ? FG : DN} opacity={0.35} />)}
      {PN.vals2 && <path d={PN.vals2.slice(0, Math.ceil(shown)).map((v, i) => `${i ? "L" : "M"}${xs(i).toFixed(1)},${py(v).toFixed(1)}`).join(" ")} stroke={A} strokeWidth={3} fill="none" />}
      <path d={PN.vals.slice(0, Math.ceil(shown)).map((v, i) => `${i ? "L" : "M"}${xs(i).toFixed(1)},${py(v).toFixed(1)}`).join(" ")} stroke={FG} strokeWidth={3} fill="none" />
      {P.marks.filter(m => m.type === "rseg").map((m, k) => {
        const x1 = xs(m.i1!), y1 = py(PN.vals[m.i1!]), x2 = xs(m.i2!), y2 = py(PN.vals[m.i2!]);
        return <line key={k} x1={x1} y1={y1} x2={x1 + (x2 - x1) * mk} y2={y1 + (y2 - y1) * mk} stroke={A} strokeWidth={5} strokeLinecap="round" />;
      })}
      {P.marks.filter(m => m.type === "pdot").map((m, k) => <circle key={k} cx={xs(m.i!)} cy={py(PN.vals[m.i!])} r={16 * mk} fill="none" stroke={t.c.a} strokeWidth={4} />)}
      <text x={X0 + 14} y={1058} fontSize={26} fontWeight={700} fill={MUT} fontFamily={ff(t, "mono")}>{PN.label}</text>
    </g>}
  </svg>;
};

// Calm, deep background: slow amber light that melts into the black on every side, a giant blurred ghost of the
// same real chart drifting behind (depth), and a soft vignette. The area behind the text stays the darkest.
const Backdrop: React.FC<{P: ChartLessonProps}> = ({P}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const A = t.c.accent;
  const CS = P.candles, N = CS.length;
  const lo = Math.min(...CS.map(c => c.l)), hi = Math.max(...CS.map(c => c.h));
  const gy = (v: number) => 1820 - (v - lo) / (hi - lo || 1) * 560;      // below the real chart, fills the calm lower half
  const gx = (i: number) => -120 + i * (1560 / (N - 1));
  const drift = interpolate(f, [0, CL.body], [0, -160]);
  const breathe = 0.5 + 0.5 * Math.sin(f / 70);
  const orb = (x: number, y: number, r: number, a: number) =>
    <div style={{position: "absolute", left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: "50%",
      background: `radial-gradient(circle, ${A}${Math.round(a * 255).toString(16).padStart(2, "0")} 0%, ${A}${Math.round(a * 110).toString(16).padStart(2, "0")} 30%, transparent 70%)`}} />;
  const ghost = CS.map((c, i) => `${i ? "L" : "M"}${gx(i).toFixed(0)},${gy(c.c).toFixed(0)}`).join(" ");
  return <div style={{position: "absolute", inset: 0, overflow: "hidden"}}>
    {orb(880 + 60 * Math.sin(f / 90), 1480 + 40 * Math.cos(f / 110), 620, 0.16 + 0.05 * breathe)}
    {orb(120 + 50 * Math.cos(f / 120), 1750, 520, 0.08)}
    {orb(1020, 250 + 30 * Math.sin(f / 100), 380, 0.07)}
    <svg width={1500} height={1920} style={{position: "absolute", left: 0, top: 0, opacity: 0.5, translate: `${drift}px 0px`}}>
      <defs><linearGradient id="gfade" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stopColor={A} stopOpacity="0" /><stop offset=".35" stopColor={A} stopOpacity="1" /><stop offset=".8" stopColor={A} stopOpacity="1" /><stop offset="1" stopColor={A} stopOpacity="0" /></linearGradient></defs>
      {[[46, 0.05], [26, 0.08], [10, 0.14]].map(([sw, op]) =>       /* stacked strokes = soft glow without an expensive blur filter */
        <path key={sw} d={ghost} stroke="url(#gfade)" strokeOpacity={op} strokeWidth={sw} fill="none" strokeLinejoin="round" strokeLinecap="round" />)}
    </svg>
    <div style={{position: "absolute", inset: 0, background: "radial-gradient(130% 75% at 50% 42%, transparent 35%, rgba(0,0,0,.55) 100%)"}} />
    <div style={{position: "absolute", left: 0, right: 0, top: 230, height: 470, background: "linear-gradient(180deg, transparent, rgba(11,11,12,.55) 30%, rgba(11,11,12,.55) 75%, transparent)"}} />
  </div>;
};

const Block: React.FC<{from: number; to: number; children: React.ReactNode; top?: number}> = ({from, to, children, top = 400}) => {
  const f = useCurrentFrame();
  if (f < from - 1 || f > to + 12) return null;
  const a = from === 0 ? 1 : p(f, from, from + 14);
  const o = 1 - p(f, to - 4, to + 10);
  return <div style={{position: "absolute", left: 65, right: 65, top, opacity: a * o, translate: `0px ${(1 - a) * 26 - (1 - o) * 18}px`}}>{children}</div>;
};

const Scene: React.FC<ChartLessonProps> = (P) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const body = (s: string, size = 50, col?: string, w = 600) =>
    <div style={{fontFamily: ff(t, "body"), fontVariationSettings: `'wght' ${w}, 'wdth' 92`, fontSize: size, lineHeight: 1.16, color: col ?? t.c.fg}}>{s}</div>;
  const hl = (s: string, col: string) => s.split(/(\*[^*]+\*)/).map((x, k) => x.startsWith("*") ? <span key={k} style={{color: col}}>{x.slice(1, -1)}</span> : x);
  const good = P.worked ? t.c.accent : t.c.warn;
  const chip = (txt: string, fill = false) => <div style={{fontFamily: ff(t, "mono"), fontSize: 28, fontWeight: 700, padding: "8px 18px", borderRadius: 10,
    border: `3px solid ${t.c.accent}`, color: fill ? t.c.onAccent : t.c.accent, background: fill ? t.c.accent : "transparent", whiteSpace: "nowrap"}}>{txt}</div>;
  const cta = p(f, CL.rule + 80, CL.rule + 96);
  return <>
    <Backdrop P={P} />
    {/* header */}
    <div style={{position: "absolute", left: 65, right: 65, top: 280, display: "flex", alignItems: "center", gap: 20}}>
      <Icon asset={P.asset} />
      <div style={{fontFamily: ff(t, "mono"), fontWeight: 700, fontSize: P.symbol.length > 6 ? 46 : 54, color: t.c.fg, whiteSpace: "nowrap"}}>
        {P.symbol} <span style={{color: t.c.accent}}>· {P.tf}</span></div>
      <div style={{marginLeft: "auto"}}>{chip(P.date)}</div>
    </div>
    <Chart P={P} />

    <Block from={0} to={CL.concept}>
      <Words text={P.hook} mode="settle" size={P.hook.replace(/\*/g, "").length > 44 ? 72 : 86} lh={1.04} />
    </Block>
    <Block from={CL.concept} to={CL.signal}>
      {body(P.concept[0], 52, t.c.fg, 700)}
      <div style={{height: 26, opacity: p(f, CL.concept + 95, CL.concept + 110)}} />
      <div style={{opacity: p(f, CL.concept + 100, CL.concept + 116)}}>{body(P.concept[1], 46, t.c.muted, 600)}</div>
    </Block>
    <Block from={CL.signal} to={CL.after}>
      <div style={{fontFamily: ff(t, "body"), fontVariationSettings: "'wght' 600, 'wdth' 100", fontSize: 32, letterSpacing: "0.12em", color: t.c.muted}}>ԻՐԱԿԱՆ ՕՐԻՆԱԿ</div>
      <div style={{marginTop: 14, fontFamily: ff(t, "mono"), fontWeight: 800, fontSize: P.label.length > 16 ? 62 : 74, color: t.c.accent, lineHeight: 1.05}}>{P.label}</div>
      <div style={{marginTop: 16, opacity: p(f, CL.signal + 60, CL.signal + 76)}}>{body(`Փակում՝ ${P.entry}`, 40, t.c.muted, 600)}</div>
    </Block>
    <Block from={CL.after} to={CL.rule}>
      <div style={{fontFamily: ff(t, "body"), fontVariationSettings: "'wght' 600, 'wdth' 100", fontSize: 32, letterSpacing: "0.12em", color: t.c.muted}}>Ի՞ՆՉ ԵՂԱՎ ՀԵՏՈ</div>
      <div style={{marginTop: 14, opacity: p(f, CL.after + 90, CL.after + 106)}}>{body(P.outcome[0].replace(/\*/g, ""), 56, t.c.fg, 700)}</div>
      <div style={{marginTop: 10, opacity: p(f, CL.after + 104, CL.after + 120)}}>
        <div style={{fontFamily: ff(t, "body"), fontVariationSettings: "'wght' 700, 'wdth' 92", fontSize: /%/.test(P.outcome[1]) && P.outcome[1].length < 20 ? 96 : 44, lineHeight: 1.1, color: t.c.fg}}>{hl(P.outcome[1], good)}</div>
      </div>
    </Block>
    <Block from={CL.rule} to={CL.body + 20}>
      <div style={{fontFamily: ff(t, "body"), fontVariationSettings: "'wght' 600, 'wdth' 100", fontSize: 32, letterSpacing: "0.12em", color: t.c.muted, marginBottom: 14}}>ԿԱՆՈՆ</div>
      <Words text={P.rule} start={CL.rule + 4} mode="rise" size={70} lh={1.06} />
    </Block>
    {f >= CL.rule + 70 && <div style={{position: "absolute", left: 65, top: 1188, opacity: cta, translate: `0px ${(1 - cta) * 20}px`}}>{chip("Գրիր «ԴԱՍ» comment-ում →", true)}</div>}
    <div style={{position: "absolute", left: 65, right: 65, top: 1200, fontFamily: ff(t, "body"), fontSize: 28, fontWeight: 600, color: t.c.muted,
      opacity: f < CL.signal ? 0 : p(f, CL.signal, CL.signal + 20) * (f >= CL.rule + 70 ? 0 : 1)}}>
      Կրթական վերլուծություն է, ոչ թե ֆինանսական խորհուրդ</div>
    {f >= CL.rule + 70 && <div style={{position: "absolute", left: 470, right: 65, top: 1186, textAlign: "right", fontFamily: ff(t, "body"), fontSize: 28, fontWeight: 600,
      color: t.c.muted, lineHeight: 1.2, opacity: cta}}>Կրթական վերլուծություն է,<br />ոչ թե ֆինանսական խորհուրդ</div>}
  </>;
};

export const ChartLesson: React.FC<ChartLessonProps> = (P) => (
  <ThemeRoot theme={CLEAN}>
    <Sequence durationInFrames={CL.body} layout="none"><Scene {...P} /></Sequence>
    <Sequence from={CL.body} layout="none"><EndCard cta="kw" line={false} /></Sequence>
    <Cue at={0} name="hook" volume={0.45} />
    <Cue at={CL.concept} name="swap" volume={0.4} />
    <Cue at={CL.signal + 20} name="hit" volume={0.5} />
    <Cue at={CL.after} name="swap" volume={0.4} />
    <Cue at={CL.after + 104} name="resolve" volume={0.45} />
    <Cue at={CL.rule} name="swap" volume={0.4} />
    <Cue at={CL.body} name="ident" volume={0.7} />
  </ThemeRoot>
);
