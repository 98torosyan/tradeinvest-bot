// Animated candlestick chart from real OHLC arrays + drawing primitives (zone, level, fib, trendline, path, tags).
// Pure functions of props: pass a progress value (0..1 or candle count) computed from the frame in the scene.
import React, {useId} from "react";
import {useTheme, ff} from "./core";

export type OHLC = {o: number; h: number; l: number; c: number};
export type Box = {x: number; y: number; w: number; h: number};
export type Scale = {x: (i: number) => number; y: (v: number) => number; cw: number; n: number; lo: number; hi: number; box: Box};

/** Price/index -> pixel mapping. `include` widens the price range (targets, stops) so they stay on screen. */
export const makeScale = (cs: OHLC[], box: Box, opts: {pad?: number; include?: number[]; slots?: number} = {}): Scale => {
  const vals = [...cs.flatMap(c => [c.h, c.l]), ...(opts.include ?? [])];
  const lo0 = Math.min(...vals), hi0 = Math.max(...vals), pad = (hi0 - lo0) * (opts.pad ?? 0.08);
  const lo = lo0 - pad, hi = hi0 + pad;
  const n = opts.slots ?? cs.length;                  // slots > candles leaves room on the right for paths
  const cw = box.w / n;
  return {n, lo, hi, box, cw, x: (i) => box.x + (i + 0.5) * cw, y: (v) => box.y + box.h - ((v - lo) / (hi - lo)) * box.h};
};

/** Horizontal grid lines (no numbers: price tags carry the numbers). */
export const Grid: React.FC<{s: Scale; rows?: number; opacity?: number}> = ({s, rows = 5, opacity = 1}) => {
  const t = useTheme();
  return <g opacity={opacity}>{Array.from({length: rows}, (_, g) => {
    const y = s.box.y + (g * s.box.h) / (rows - 1);
    return <line key={g} x1={s.box.x} x2={s.box.x + s.box.w} y1={y} y2={y} stroke={t.c.grid} strokeWidth={2} />;
  })}</g>;
};

/**
 * Candles. `reveal` = how many candles are drawn (float: the last one "grows" live from open to close).
 * `focus(i)` returns an opacity multiplier so a scene can spotlight part of the chart.
 */
export const Candles: React.FC<{cs: OHLC[]; s: Scale; reveal?: number; focus?: (i: number) => number; width?: number; color?: (i: number, up: boolean) => string}> =
  ({cs, s, reveal = cs.length, focus, width = 0.62, color}) => {
    const t = useTheme();
    const w = s.cw * width;
    const id = useId().replace(/:/g, "");
    const sc = t.fx?.candle === "sculpt" ? t.fx.sculpt : undefined;   // gradient-lit bodies + soft light bloom
    return <g filter={sc ? `url(#gl${id})` : undefined}>
      {sc && <defs>
        <linearGradient id={`up${id}`} x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor={sc.upTop} /><stop offset="1" stopColor={sc.upBot} /></linearGradient>
        <linearGradient id={`dn${id}`} x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor={sc.dnTop} /><stop offset="1" stopColor={sc.dnBot} /></linearGradient>
        <filter id={`gl${id}`} x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="0" stdDeviation="7" floodColor={sc.glow} /></filter>
      </defs>}
      {cs.map((c, i) => {
      const a = Math.max(0, Math.min(1, reveal - i));
      if (a <= 0) return null;
      const cc = c.o + (c.c - c.o) * a;                         // live close while the candle forms
      const top0 = Math.max(c.o, cc), bot0 = Math.min(c.o, cc);
      const hh = top0 + (c.h - Math.max(c.o, c.c)) * a;
      const ll = bot0 - (Math.min(c.o, c.c) - c.l) * a;
      const up = c.c >= c.o;
      const col = color ? color(i, up) : up ? t.c.up : t.c.down;
      const top = s.y(top0), bot = s.y(bot0);
      return <g key={i} opacity={(focus ? focus(i) : 1) * Math.min(1, a * 3)}>
        <line x1={s.x(i)} x2={s.x(i)} y1={s.y(Math.max(hh, top0))} y2={s.y(Math.min(ll, bot0))} stroke={col} strokeWidth={Math.max(2, w * 0.14)} strokeLinecap="round" />
        {sc && !color
          ? <rect x={s.x(i) - w / 2} y={top} width={w} height={Math.max(3, bot - top)} rx={Math.min(2, w * 0.1)} fill={`url(#${up ? "up" : "dn"}${id})`}
              stroke={!up && sc.dnStroke ? sc.dnStroke : undefined} strokeWidth={!up && sc.dnStroke ? 1.5 : undefined} />
          : <rect x={s.x(i) - w / 2} y={top} width={w} height={Math.max(3, bot - top)} rx={Math.min(3, w * 0.15)} fill={up ? col : t.c.bg} stroke={col} strokeWidth={Math.max(2, w * 0.14)} />}
      </g>;
    })}</g>;
  };

/** Price zone (support/resistance band) that sweeps in from the left. */
export const Zone: React.FC<{s: Scale; lo: number; hi: number; p: number; from?: number; minH?: number; color?: string}> = ({s, lo, hi, p, from = 0, minH = 16, color}) => {
  const t = useTheme();
  const x0 = s.x(from) - s.cw / 2, x1 = s.box.x + s.box.w;
  const y0 = s.y(hi), h = Math.max(minH, s.y(lo) - y0);
  return <rect x={x0} y={y0 - (h === minH ? (minH - (s.y(lo) - y0)) / 2 : 0)} width={(x1 - x0) * p} height={h} rx={6}
    fill={color ? color + "33" : t.c.zone} stroke={color ?? t.c.accent} strokeOpacity={0.7} strokeWidth={2} opacity={p > 0 ? 1 : 0} />;
};

/** Horizontal level line (solid or dashed) drawn left-to-right. */
export const Level: React.FC<{s: Scale; v: number; p: number; color?: string; dashed?: boolean; width?: number; from?: number}> = ({s, v, p, color, dashed, width = 4, from = 0}) => {
  const t = useTheme();
  const x0 = s.x(from) - s.cw / 2, x1 = s.box.x + s.box.w;
  return <line x1={x0} x2={x0 + (x1 - x0) * p} y1={s.y(v)} y2={s.y(v)} stroke={color ?? t.c.accent} strokeWidth={width}
    strokeDasharray={dashed ? "10 10" : undefined} strokeLinecap="round" opacity={p > 0 ? 1 : 0} />;
};

/** Fibonacci retracement between two prices, labelled on the right. */
export const Fib: React.FC<{s: Scale; a: number; b: number; p: number; levels?: number[]}> = ({s, a, b, p, levels = [0.382, 0.5, 0.618]}) => {
  const t = useTheme();
  return <g>{levels.map((r, k) => {
    const v = b - (b - a) * r, q = Math.max(0, Math.min(1, p * 1.4 - k * 0.2));
    return <g key={r} opacity={q}>
      <line x1={s.box.x} x2={s.box.x + s.box.w * q} y1={s.y(v)} y2={s.y(v)} stroke={t.c.fg} strokeOpacity={0.35} strokeWidth={2} strokeDasharray="6 10" />
      <text x={s.box.x + s.box.w + 14} y={s.y(v) + 10} textAnchor="start" fontSize={28} fontWeight={700} fill={t.c.muted} fontFamily={ff(t, "mono")}>{r}</text>
    </g>;
  })}</g>;
};

/** Trendline through two anchor points (index, price), extended to index `to`, drawn on with p. */
export const Trendline: React.FC<{s: Scale; i1: number; v1: number; i2: number; v2: number; to?: number; p: number; color?: string}> = ({s, i1, v1, i2, v2, to, p, color}) => {
  const t = useTheme();
  const end = to ?? i2, k = (v2 - v1) / (i2 - i1);
  const x1 = s.x(i1), y1 = s.y(v1), x2 = s.x(i1 + (end - i1) * p), y2 = s.y(v1 + k * (end - i1) * p);
  return <g opacity={p > 0 ? 1 : 0}>
    <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color ?? t.c.accent} strokeWidth={5} strokeLinecap="round" />
    <circle cx={s.x(i1)} cy={y1} r={8} fill={color ?? t.c.accent} />
    {p > (i2 - i1) / (end - i1) && <circle cx={s.x(i2)} cy={s.y(v2)} r={8} fill={color ?? t.c.accent} />}
  </g>;
};

// Catmull-Rom -> cubic bezier so scenario paths look hand-drawn but stay deterministic.
const smooth = (pts: [number, number][]) => {
  if (pts.length < 3) return `M${pts.map(p => p.join(",")).join(" L")}`;
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    d += ` C${p1[0] + (p2[0] - p0[0]) / 6},${p1[1] + (p2[1] - p0[1]) / 6} ${p2[0] - (p3[0] - p1[0]) / 6},${p2[1] - (p3[1] - p1[1]) / 6} ${p2[0]},${p2[1]}`;
  }
  return d;
};

/** Projected path (scenario) through chart points [index, price]; draws on with p, arrowhead at the end. */
export const PathArrow: React.FC<{s: Scale; pts: [number, number][]; p: number; color?: string; dashed?: boolean; width?: number}> = ({s, pts, p, color, dashed = true, width = 6}) => {
  const t = useTheme();
  const id = useId().replace(/:/g, "");
  const px = pts.map(([i, v]) => [s.x(i), s.y(v)] as [number, number]);
  const d = smooth(px);
  const col = color ?? t.c.accent;
  const [ex, ey] = px[px.length - 1], [bx, by] = px[px.length - 2];
  const ang = Math.atan2(ey - by, ex - bx), L = 22;
  const head = `M${ex - L * Math.cos(ang - 0.5)},${ey - L * Math.sin(ang - 0.5)} L${ex},${ey} L${ex - L * Math.cos(ang + 0.5)},${ey - L * Math.sin(ang + 0.5)}`;
  return <g opacity={p > 0 ? 1 : 0}>
    <mask id={id} maskUnits="userSpaceOnUse"><path d={d} pathLength={1} stroke="#fff" strokeWidth={width + 8} fill="none" strokeDasharray={`${p} 2`} /></mask>
    <path d={d} stroke={col} strokeWidth={width} fill="none" strokeLinecap="round" strokeDasharray={dashed ? "14 12" : undefined} mask={`url(#${id})`} />
    <path d={head} stroke={col} strokeWidth={width} fill="none" strokeLinecap="round" strokeLinejoin="round" opacity={Math.max(0, (p - 0.92) / 0.08)} />
  </g>;
};

/** Ring that pops on a touch point; optional number inside a chip above it. */
export const Touch: React.FC<{s: Scale; i: number; v: number; p: number; label?: string; below?: boolean; color?: string}> = ({s, i, v, p, label, below, color}) => {
  const t = useTheme();
  const cx = s.x(i), cy = s.y(v), col = color ?? t.c.accent;
  const ly = below ? cy + 62 : cy - 62;
  return <g opacity={Math.min(1, p * 2)}>
    <circle cx={cx} cy={cy} r={6 + 20 * p} fill="none" stroke={col} strokeWidth={4} />
    {label && <g transform={`translate(${cx},${ly}) scale(${0.6 + 0.4 * p})`}>
      <rect x={-26} y={-26} width={52} height={52} rx={26} fill={col} />
      <text y={12} textAnchor="middle" fontSize={32} fontWeight={800} fill={t.c.onAccent} fontFamily={ff(t, "mono")}>{label}</text>
    </g>}
  </g>;
};

/** Price tag box at the right edge (x = box right + gap). */
export const PriceTag: React.FC<{s: Scale; v: number; text: string; p: number; fill?: boolean; color?: string; x?: number; w?: number; dy?: number}> = ({s, v, text, p, fill, color, x, w = 150, dy = 0}) => {
  const t = useTheme();
  const col = color ?? t.c.accent, X = x ?? s.box.x + s.box.w + 14, y = s.y(v) + dy;
  if (y + 25 > 1250) return null;            // text never leaves the safe zone: callers repeat the value in the text band
  return <g opacity={p} transform={`translate(${(1 - p) * 24},0)`}>
    <rect x={X} y={y - 25} width={w} height={50} rx={10} fill={fill ? col : t.c.bg} stroke={col} strokeWidth={3} />
    <text x={X + w / 2} y={y + 10} textAnchor="middle" fontSize={text.length > 7 ? 25 : 28} fontWeight={700} fill={fill ? t.c.onAccent : col} fontFamily={ff(t, "mono")}>{text}</text>
  </g>;
};

/** Pin + speech chip on a candle ("your entry"). */
export const Pin: React.FC<{s: Scale; i: number; v: number; p: number; text: string; color?: string; above?: boolean; dx?: number}> = ({s, i, v, p, text, color, above = true, dx = 0}) => {
  const t = useTheme();
  const cx = s.x(i), cy = s.y(v), col = color ?? t.c.accent, dir = above ? -1 : 1;
  const w = text.length * 21 + 44, by = cy + dir * 92;
  return <g opacity={Math.min(1, p * 2)}>
    <line x1={cx} y1={cy + dir * 12} x2={cx} y2={by - dir * 30 * p} stroke={col} strokeWidth={4} />
    <circle cx={cx} cy={cy} r={10 * p + 2} fill={col} />
    <g transform={`translate(${cx + dx},${by}) scale(${0.7 + 0.3 * p})`}>
      <rect x={-w / 2} y={-32} width={w} height={64} rx={32} fill={col} />
      <text y={12} textAnchor="middle" fontSize={34} fontWeight={800} fill={t.c.onAccent} fontFamily={ff(t, "display")}>{text}</text>
    </g>
  </g>;
};

/**
 * Glossy-floor reflection: re-renders `children` mirrored under the chart baseline, fading out.
 * Fills the lower half of the Reel (under Instagram's caption UI) with picture, never with text.
 */
export const Reflection: React.FC<{s: Scale; gap?: number; depth?: number; strength?: number; children: React.ReactNode}> = ({s, gap = 18, depth = 520, strength = 0.32, children}) => {
  const id = useId().replace(/:/g, "");
  const base = s.box.y + s.box.h + gap;
  return <g>
    <defs>
      <linearGradient id={`rf${id}`} x1="0" x2="0" y1={base} y2={base + depth} gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#fff" stopOpacity={strength} /><stop offset="1" stopColor="#fff" stopOpacity={0} />
      </linearGradient>
      <mask id={`rm${id}`} maskUnits="userSpaceOnUse"><rect x={0} y={base} width={1080} height={depth} fill={`url(#rf${id})`} /></mask>
    </defs>
    <g mask={`url(#rm${id})`}><g transform={`translate(0,${2 * base}) scale(1,-1)`}>{children}</g></g>
  </g>;
};

/** Collision pass for right-edge tags: returns y offsets so tags (height h) never overlap. */
export const stackTags = (ys: number[], h = 56): number[] => {
  const order = ys.map((y, i) => ({y, i})).sort((a, b) => a.y - b.y);
  const out = new Array(ys.length).fill(0);
  let prev = -Infinity;
  for (const o of order) { const y = Math.max(o.y, prev + h); out[o.i] = y - o.y; prev = y; }
  return out;
};
