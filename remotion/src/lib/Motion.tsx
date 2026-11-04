// Transitions, camera and loop devices.
import React from "react";
import {Easing, interpolate, useCurrentFrame} from "remotion";
import {useTheme, pr} from "./core";

/**
 * Loop by rewind: the last `tail` frames play the timeline backwards (eased) to frame 0,
 * so the final frame is pixel-identical to the first. Scenes compute everything from the returned frame.
 */
export const rewind = (f: number, total: number, tail: number) =>
  f < total - tail ? f : interpolate(f, [total - tail, total - 1], [total - tail, 0], {easing: Easing.inOut(Easing.cubic), extrapolateRight: "clamp"});

/**
 * Loop by end-state-first: frames [0, hold) show the finished state (frame `end`), then the timeline
 * snaps back and plays normally, ending on that same finished state.
 */
export const endFirst = (f: number, hold: number, end: number, back: number) => {
  if (f < hold) return end;
  if (f < hold + back) return interpolate(f, [hold, hold + back], [end, 0], {easing: Easing.inOut(Easing.cubic)});
  return Math.min(end, f - hold - back);
};

/** Enter/exit styles for a block. kind: rise | pop | wipe | slam. */
export const useEnter = (kind: "rise" | "pop" | "wipe" | "slam", start: number, dur = 10, out?: number): React.CSSProperties => {
  const f = useCurrentFrame();
  const a = pr(f, start, start + dur, kind === "slam" ? Easing.out(Easing.back(1.6)) : undefined);
  const x = out === undefined ? 0 : pr(f, out, out + 8, Easing.in(Easing.cubic));
  const base: React.CSSProperties = {opacity: Math.min(a * 1.5, 1) * (1 - x)};
  if (kind === "rise") return {...base, translate: `0px ${(1 - a) * 40 - x * 30}px`};
  if (kind === "pop") return {...base, scale: String(0.85 + 0.15 * a)};
  if (kind === "slam") return {...base, scale: String(1.3 - 0.3 * a)};
  return {...base, clipPath: `inset(0 ${(1 - a) * 100}% 0 0)`};
};

/** Full-frame accent bar that sweeps across – the brand's scene-change device (2 per Reel max). */
export const Sweep: React.FC<{at: number; dur?: number; color?: string; dir?: 1 | -1}> = ({at, dur = 12, color, dir = 1}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const p = interpolate(f, [at, at + dur], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic)});
  if (p <= 0 || p >= 1) return null;
  const x = dir * (-1200 + 2400 * p);
  if (t.motion.style === "premium")   // premium: a soft band of light passes instead of a solid bar
    return <div style={{position: "absolute", top: 0, bottom: 0, left: 0, width: 1080, translate: `${x}px 0px`,
      background: `linear-gradient(90deg, transparent, ${color ?? t.c.accent}55 40%, ${color ?? t.c.accent}aa 50%, ${color ?? t.c.accent}55 60%, transparent)`, mixBlendMode: "screen"}} />;
  return <div style={{position: "absolute", top: 0, bottom: 0, left: 0, width: 1080, background: color ?? t.c.accent, translate: `${x}px 0px`, skew: "-12deg 0deg"}} />;
};

/** Camera for an SVG group: zoom `z` around focal point (cx, cy). */
export const Camera: React.FC<{z: number; cx: number; cy: number; children: React.ReactNode}> = ({z, cx, cy, children}) =>
  <g transform={`translate(${cx},${cy}) scale(${z}) translate(${-cx},${-cy})`}>{children}</g>;

/** Thin segmented progress rail (one segment per beat). Shows structure, not remaining time. */
export const BeatRail: React.FC<{beats: number[]; total: number; f: number; y?: number}> = ({beats, total, f, y = 262}) => {
  const t = useTheme();
  const edges = [0, ...beats, total];
  const W = 950, gap = 10, x0 = 65;
  const segW = (k: number) => ((edges[k + 1] - edges[k]) / total) * (W - gap * (edges.length - 2));
  let x = x0;
  return <svg width={1080} height={20} style={{position: "absolute", top: y - 10, left: 0}}>
    {edges.slice(0, -1).map((e, k) => {
      const w = segW(k), fill = Math.max(0, Math.min(1, (f - e) / (edges[k + 1] - e)));
      const el = <g key={k}><rect x={x} y={7} width={w} height={6} rx={3} fill={t.c.grid} /><rect x={x} y={7} width={w * fill} height={6} rx={3} fill={t.c.fg} opacity={0.7} /></g>;
      x += w + gap;
      return el;
    })}
  </svg>;
};
