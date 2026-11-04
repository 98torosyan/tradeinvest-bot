// Sunday «Շաբաթը մեկ հայացքով» Reel: weekly % change of 5 markets from real daily closes.
// Intro → 5 rows (sparkline draws, counter rolls) → winner / loser → question → end card.
import React from "react";
import {Sequence, useCurrentFrame} from "remotion";
import {ThemeRoot, useTheme, Cue, pr, ff} from "./lib/core";
import {Words} from "./lib/Kinetic";
import {EditorialMarks} from "./lib/Atmosphere";
import {EndCard, END_FRAMES} from "./lib/EndCard";
import {getTheme} from "./theme";

export type WeeklyRow = {name: string; sym: string; closes: number[]; pct: number};
export type WeeklyProps = {range: string; rows: WeeklyRow[]};

const UP = "#7BC47F", DOWN = "#E25B4B";
const INTRO = 50, STEP = 24, HOLD = 40, SUM = 75, ASK = 60;
export const weeklyTotal = (n: number) => INTRO + n * STEP + HOLD + SUM + ASK + END_FRAMES;

const Spark: React.FC<{closes: number[]; at: number; color: string}> = ({closes, at, color}) => {
  const f = useCurrentFrame();
  const W = 250, H = 90;
  const lo = Math.min(...closes), hi = Math.max(...closes), k = hi - lo || 1;
  const pts = closes.map((c, i) => [i * W / (closes.length - 1), H - (c - lo) / k * H]);
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
  const p = pr(f, at, at + 22);
  const len = 900;
  const last = pts[pts.length - 1];
  return <svg width={W + 20} height={H + 20} viewBox={`-10 -10 ${W + 20} ${H + 20}`}>
    <path d={d} fill="none" stroke={color} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
    <circle cx={last[0]} cy={last[1]} r={9 * pr(f, at + 18, at + 24)} fill={color} />
  </svg>;
};

const ICON_BG: Record<string, string> = {BTC: "#F7931A", ETH: "#627EEA", SOL: "#14F195", XAU: "#D4AF37", NDX: "#3B82F6"};
// Simple drawn glyphs (no official logo files): ₿-style B, diamond, slanted bars, gold bars, index chart.
const Icon: React.FC<{sym: string}> = ({sym}) => {
  const bg = ICON_BG[sym] ?? "#FF8A00";
  const W = "#FFFFFF", K = "#0B0B0C";
  let g: React.ReactNode = null;
  if (sym === "BTC") g = <g fill="none" stroke={W} strokeWidth={6} strokeLinejoin="round" strokeLinecap="round">
    <path d="M38 28 V68 M38 28 H54 Q64 28 64 38 Q64 47 54 47 H38 M38 47 H56 Q67 47 67 57.5 Q67 68 56 68 H38" />
    <path d="M45 21 V28 M53 21 V28 M45 68 V75 M53 68 V75" /></g>;
  if (sym === "ETH") g = <g fill={W}><path d="M48 16 L68 49 L48 60 L28 49 Z" opacity={0.95} /><path d="M48 64 L68 53 L48 81 L28 53 Z" opacity={0.75} /></g>;
  if (sym === "SOL") g = <g fill={K}>{[30, 45, 60].map((y, i) => <path key={i} d={`M${i === 1 ? 26 : 32} ${y} H72 L${i === 1 ? 72 : 66} ${y + 9} H${i === 1 ? 20 : 26} Z`} transform={i === 1 ? "scale(-1 1) translate(-96 0)" : undefined} />)}</g>;
  if (sym === "XAU") g = <g fill={K} opacity={0.85}><path d="M22 66 L28 54 H46 L52 66 Z" /><path d="M46 66 L52 54 H70 L76 66 Z" /><path d="M34 52 L40 40 H58 L64 52 Z" /></g>;
  if (sym === "NDX") g = <g fill="none" stroke={W} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round"><path d="M24 66 L40 50 L52 58 L72 34" /><path d="M60 34 H72 V46" /></g>;
  return <svg width={96} height={96} viewBox="0 0 96 96" style={{flex: "none", marginRight: 26}}><circle cx={48} cy={48} r={46} fill={bg} />{g}</svg>;
};

const Row: React.FC<{r: WeeklyRow; at: number; y: number; dim: number}> = ({r, at, y, dim}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const a = pr(f, at, at + 12);
  const color = r.pct >= 0 ? UP : DOWN;
  const v = r.pct * pr(f, at + 4, at + 26, (x) => 1 - Math.pow(1 - x, 3));
  return <div style={{position: "absolute", left: 70, right: 70, top: y, height: 190, display: "flex", alignItems: "center",
    borderTop: `2px solid ${t.c.fg}1A`, opacity: a * dim, translate: `${(1 - a) * 80}px 0px`}}>
    <Icon sym={r.sym} />
    <div style={{width: 280}}>
      <div style={{fontFamily: ff(t, "display"), fontVariationSettings: t.type.displayVar, fontSize: 58, lineHeight: 1}}>{r.name}</div>
      <div style={{fontFamily: ff(t, "mono"), fontSize: 26, color: t.c.muted, marginTop: 10, letterSpacing: "0.08em"}}>{r.sym}</div>
    </div>
    <Spark closes={r.closes} at={at + 2} color={color} />
    <div style={{marginLeft: "auto", fontFamily: ff(t, "mono"), fontWeight: 800, fontSize: 62, color}}>
      {r.pct >= 0 ? "+" : "−"}{Math.abs(v).toFixed(1)}%</div>
  </div>;
};

const Scene: React.FC<WeeklyProps> = ({range, rows}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const n = rows.length;
  const sumAt = INTRO + n * STEP + HOLD;
  const askAt = sumAt + SUM;
  const best = rows.reduce((a, b) => (b.pct > a.pct ? b : a));
  const worst = rows.reduce((a, b) => (b.pct < a.pct ? b : a));
  const listOut = 1 - pr(f, sumAt - 8, sumAt + 4);
  return <>
    <EditorialMarks index="W" left="WEEKLY" right={range} y0={276} />
    {f < sumAt + 6 && <>
      <div style={{position: "absolute", left: 70, right: 70, top: 340, opacity: listOut}}>
        <Words text={"Շաբաթը *մեկ* հայացքով"} mode="settle" size={104} lh={1.02} />
      </div>
      {rows.map((r, i) => <Row key={r.sym} r={r} at={INTRO + i * STEP} y={620 + i * 196} dim={listOut} />)}
    </>}
    {f >= sumAt - 2 && f < askAt + 4 && <div style={{position: "absolute", left: 70, right: 70, top: 470, opacity: 1 - pr(f, askAt - 6, askAt + 2)}}>
      {[{lab: "ՇԱԲԱԹՎԱ ՀԱՂԹՈՂ", r: best, c: UP, at: sumAt}, {lab: "ՇԱԲԱԹՎԱ ՊԱՐՏՎՈՂ", r: worst, c: DOWN, at: sumAt + 14}].map(({lab, r, c, at}) => {
        const a = pr(f, at, at + 14);
        return <div key={lab} style={{marginBottom: 90, opacity: a, translate: `0px ${(1 - a) * 50}px`}}>
          <div style={{fontFamily: ff(t, "mono"), fontSize: 30, letterSpacing: "0.16em", color: t.c.muted}}>{lab}</div>
          <div style={{display: "flex", alignItems: "baseline", gap: 30, marginTop: 14}}>
            <div style={{fontFamily: ff(t, "display"), fontVariationSettings: t.type.displayVar, fontSize: 120, lineHeight: 1}}>{r.name}</div>
            <div style={{fontFamily: ff(t, "mono"), fontWeight: 800, fontSize: 96, color: c}}>{r.pct >= 0 ? "+" : "−"}{Math.abs(r.pct).toFixed(1)}%</div>
          </div>
        </div>;
      })}
    </div>}
    {f >= askAt && <div style={{position: "absolute", left: 70, right: 70, top: 560}}>
      <Words text={"Ո՞ր ակտիվն էր *քոնը* այս շաբաթ։"} start={askAt} mode="rise" size={110} lh={1.04} />
      <div style={{marginTop: 50, fontSize: 46, color: t.c.muted, opacity: pr(f, askAt + 18, askAt + 30)}}>Գրիր comment-ում 👇</div>
    </div>}
    <div style={{position: "absolute", left: 70, right: 70, bottom: 225, fontSize: 24, color: t.c.muted}}>
      Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ։ Տվյալները՝ օրական փակման գներով։</div>
  </>;
};

export const Weekly: React.FC<WeeklyProps> = (P) => {
  const n = P.rows.length;
  const body = weeklyTotal(n) - END_FRAMES;
  const sumAt = INTRO + n * STEP + HOLD;
  return <ThemeRoot theme={getTheme("ti")}>
    <Sequence durationInFrames={body} layout="none"><Scene {...P} /></Sequence>
    <Sequence from={body} layout="none"><EndCard cta="none" /></Sequence>
    <Cue at={0} name="hook" volume={0.45} />
    {P.rows.map((r, i) => <Cue key={i} at={INTRO + i * STEP} name="tap" volume={0.5} />)}
    <Cue at={sumAt} name="hit" volume={0.5} />
    <Cue at={sumAt + SUM} name="swap" volume={0.45} />
    <Cue at={body} name="ident" volume={0.7} />
  </ThemeRoot>;
};
