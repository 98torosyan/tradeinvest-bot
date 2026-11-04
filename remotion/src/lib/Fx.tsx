// Motion effects adapted from reactvideoeditor/remotion-templates (MIT, https://github.com/reactvideoeditor/remotion-templates):
// whip-pan, zoom-through, push and iris transitions, camera shake, particle burst, grid-pulse / bokeh / gradient backgrounds.
// Re-written as small brand-aware wrappers so every short Reel can pick a different combination.
import React from "react";
import {interpolate, useCurrentFrame} from "remotion";
import {useTheme, pr} from "./core";

export type TransitionKind = "whip" | "zoom" | "push" | "iris" | "fade";
export const TRANSITIONS: TransitionKind[] = ["whip", "zoom", "push", "iris"];

/** Entrance style for a text block that starts at frame `at`. */
export const enterStyle = (kind: TransitionKind, f: number, at: number): React.CSSProperties => {
  const p = pr(f, at, at + 12);
  switch (kind) {
    case "whip": {
      const stretch = interpolate(f, [at, at + 6, at + 12], [1.5, 1.25, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
      return {translate: `${(1 - p) * 520}px 0px`, scale: `${stretch} 1`, transformOrigin: "0% 50%", opacity: Math.min(1, p * 3), filter: `blur(${(1 - p) * 6}px)`};
    }
    case "zoom":
      return {scale: String(1.45 - 0.45 * p), opacity: p, filter: `blur(${(1 - p) * 10}px)`, transformOrigin: "20% 50%"};
    case "push":
      return {translate: `0px ${(1 - p) * 140}px`, opacity: p};
    case "iris":
      return {clipPath: `circle(${p * 150}% at 10% 40%)`};
    default:
      return {opacity: p};
  }
};

/** Camera shake for `dur` frames from `at` (loss beats). Deterministic pseudo-noise. */
export const shake = (f: number, at: number, dur = 12, amp = 14): string => {
  if (f < at || f > at + dur) return "0px 0px";
  const k = 1 - (f - at) / dur;
  return `${Math.sin(f * 2.7) * amp * k}px ${Math.cos(f * 3.9) * amp * 0.6 * k}px`;
};

/** Burst of brand particles from (x, y) starting at `at`. */
export const Particles: React.FC<{at: number; x: number; y: number; n?: number}> = ({at, x, y, n = 26}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  if (f < at || f > at + 40) return null;
  const p = pr(f, at, at + 34, (v) => 1 - Math.pow(1 - v, 3));
  return <svg width={1080} height={1920} style={{position: "absolute", inset: 0, pointerEvents: "none"}}>
    {Array.from({length: n}, (_, i) => {
      const a = (i / n) * Math.PI * 2 + (i % 3) * 0.3, r = (120 + (i * 37) % 160) * p;
      return <rect key={i} x={x + Math.cos(a) * r} y={y + Math.sin(a) * r * 0.7} width={i % 2 ? 10 : 6} height={i % 2 ? 10 : 18} rx={2}
        fill={i % 4 ? t.c.accent : t.c.fg} opacity={1 - p} transform={`rotate(${i * 25 + p * 180} ${x + Math.cos(a) * r} ${y + Math.sin(a) * r * 0.7})`} />;
    })}
  </svg>;
};

/** Animated backgrounds behind the visual (kept subtle so text contrast stays ≥ 4.5:1). */
export const Backdrop: React.FC<{kind: number}> = ({kind}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  if (kind === 1) {                                          // grid pulse
    const pulse = 0.5 + 0.5 * Math.sin(f / 18);
    return <svg width={1080} height={1920} style={{position: "absolute", inset: 0}}>
      {Array.from({length: 13}, (_, i) => <line key={`v${i}`} x1={i * 90} x2={i * 90} y1={0} y2={1920} stroke={t.c.accent} strokeOpacity={0.04 + 0.03 * pulse} strokeWidth={1.5} />)}
      {Array.from({length: 22}, (_, i) => <line key={`h${i}`} x1={0} x2={1080} y1={i * 90} y2={i * 90} stroke={t.c.accent} strokeOpacity={0.04 + 0.03 * pulse} strokeWidth={1.5} />)}
    </svg>;
  }
  if (kind === 2) {                                          // bokeh
    return <div style={{position: "absolute", inset: 0, overflow: "hidden"}}>
      {Array.from({length: 9}, (_, i) => {
        const x = (i * 137) % 1080, y = 500 + ((i * 263) % 1300) - f * (0.4 + (i % 3) * 0.25), s = 90 + (i * 53) % 160;
        return <div key={i} style={{position: "absolute", left: x, top: y, width: s, height: s, borderRadius: "50%",
          background: `radial-gradient(circle, ${t.c.accent}26, transparent 70%)`, filter: "blur(6px)"}} />;
      })}
    </div>;
  }
  if (kind === 3) {                                          // slow gradient shift
    const a = 30 + 40 * Math.sin(f / 60);
    return <div style={{position: "absolute", inset: 0, background: `linear-gradient(${a}deg, ${t.c.accent}14, transparent 45%, ${t.c.accent}0D)`}} />;
  }
  return null;
};
