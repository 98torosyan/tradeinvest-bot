// Atmosphere + editorial layer: cinematic light, film grain, vignette, fine editorial marks,
// and Interlock (giant display word that a visual passes through). All driven by theme.fx / theme.type.
import React from "react";
import {useCurrentFrame} from "remotion";
import {useTheme, ff} from "./core";

/** Key light + rim light + vignette. The key light drifts a few px so static frames still breathe. */
export const Atmosphere: React.FC = () => {
  const t = useTheme();
  const f = useCurrentFrame();
  const fx = t.fx;
  if (!fx) return null;
  const L = fx.light;
  const dx = Math.sin(f / 70) * 18, dy = Math.cos(f / 90) * 12;
  const hex = (a: number) => Math.round(a * 255).toString(16).padStart(2, "0");
  return (
    <div style={{position: "absolute", inset: 0}}>
      {L && <div style={{position: "absolute", inset: 0, background:
        `radial-gradient(${L.r * 1080}px ${L.r * 1400}px at ${L.x * 1080 + dx}px ${L.y * 1920 + dy}px, ${L.color}${hex(L.alpha)}, ${L.color}00 70%)`}} />}
      {fx.rim && <div style={{position: "absolute", inset: 0, background:
        `radial-gradient(900px 1100px at ${-60 - dx}px ${1700 - dy}px, ${fx.rim.color}${hex(fx.rim.alpha)}, ${fx.rim.color}00 70%)`}} />}
      {fx.vignette > 0 && <div style={{position: "absolute", inset: 0, background:
        `radial-gradient(120% 90% at 50% 40%, rgba(0,0,0,0) 55%, rgba(0,0,0,${fx.vignette}) 100%)`}} />}
    </div>
  );
};

/** Animated film grain (new seed every 2 frames). Sits above everything, below the debug guides. */
export const Grain: React.FC = () => {
  const t = useTheme();
  const f = useCurrentFrame();
  const g = t.fx?.grain ?? 0;
  if (g <= 0) return null;
  const seed = Math.floor(f / 2) % 97;
  return (
    <svg width={1080} height={1920} style={{position: "absolute", inset: 0, opacity: g, mixBlendMode: t.fx?.grainBlend ?? "overlay", pointerEvents: "none"}}>
      <filter id={`grain${seed}`} x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={seed} stitchTiles="stitch" />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="1080" height="1920" filter={`url(#grain${seed})`} />
    </svg>
  );
};

/** Letter-spaced caps label (≥ 28 px). */
export const Label: React.FC<{text: string; color?: string; size?: number; style?: React.CSSProperties}> = ({text, color, size = 28, style}) => {
  const t = useTheme();
  const fam = t.type.labelFont === "body" ? `"${t.font.body.family}", sans-serif` : `"${t.font.mono.family}", "${t.font.body.family}", sans-serif`;
  return <div style={{fontFamily: fam, fontVariationSettings: t.type.labelVar, fontSize: size, fontWeight: 500, letterSpacing: t.type.labelTrack ?? "0.12em", textTransform: "uppercase",
    color: color ?? t.c.muted, whiteSpace: "nowrap", ...style}}>{text}</div>;
};

/**
 * Editorial frame: hairline rules, corner crosses, a section number and a figure caption.
 * Everything inside the Reel safe zone. `p` 0..1 draws the rules on.
 */
export const EditorialMarks: React.FC<{p?: number; index?: string; left?: string; right?: string; fig?: string; y0?: number; y1?: number}> =
  ({p = 1, index, left, right, fig, y0 = 286, y1 = 1238}) => {
    const t = useTheme();
    const W = 950, X = 65;
    const cross = (x: number, y: number) => <g key={`${x}-${y}`} stroke={t.c.muted} strokeWidth={2} opacity={p}><line x1={x - 9} x2={x + 9} y1={y} y2={y} /><line x1={x} x2={x} y1={y - 9} y2={y + 9} /></g>;
    return <>
      <svg width={1080} height={1920} style={{position: "absolute", inset: 0}}>
        <line x1={X} x2={X + W * p} y1={y0 + 44} y2={y0 + 44} stroke={t.c.muted} strokeOpacity={0.45} strokeWidth={1.5} />
        {fig && <line x1={X + W} x2={X + W - W * p} y1={y1 - 44} y2={y1 - 44} stroke={t.c.muted} strokeOpacity={0.45} strokeWidth={1.5} />}
        {[cross(X + 9, y0 + 44), cross(X + W - 9, y0 + 44)]}
      </svg>
      <div style={{position: "absolute", left: X, width: W, top: y0, display: "flex", justifyContent: "space-between", opacity: p}}>
        <Label text={[index, left].filter(Boolean).join("  ·  ")} />
        {right && <Label text={right} />}
      </div>
      {fig && <div style={{position: "absolute", left: X, width: W, top: y1 - 34, display: "flex", justifyContent: "flex-end", opacity: p}}><Label text={fig} /></div>}
    </>;
  };

/**
 * Interlock: a giant display word with a visual woven through it.
 * back layer = full word; `children` = the visual; front layer = the same word clipped to `front` (CSS clip-path),
 * so the visual reads as passing behind those parts of the letters. Decorative only — never the hook text.
 */
export const Interlock: React.FC<{word: string; top: number; size?: number; color?: string; front: string; opacity?: number; children: React.ReactNode}> =
  ({word, top, size, color, front, opacity = 1, children}) => {
    const t = useTheme();
    const style: React.CSSProperties = {position: "absolute", left: 60, right: 0, top, fontFamily: ff(t, "display"), fontSize: size ?? t.type.hero ?? 360,
      fontWeight: 700, fontVariationSettings: t.type.displayVar, lineHeight: 0.82, letterSpacing: t.type.displayTrack ?? "-0.03em", fontStretch: t.type.displayStretch ?? "100%",
      color: color ?? t.c.hero ?? t.c.surface, whiteSpace: "nowrap", opacity};
    return <>
      <div style={style}>{word}</div>
      {children}
      <div style={{...style, clipPath: front}}>{word}</div>
    </>;
  };

/** Viewfinder corner marks (theme.fx.corners) – part of the frame on every Reel. */
export const Viewfinder: React.FC<{x0?: number; x1?: number; y0?: number; y1?: number}> = ({x0 = 40, x1 = 1040, y0 = 236, y1 = 1764}) => {
  const t = useTheme();
  const c = t.fx?.corners;
  if (!c) return null;
  const L = c.len, st = {stroke: t.c.fg, strokeWidth: c.stroke, fill: "none", opacity: c.opacity};
  const k = (x: number, y: number, dx: number, dy: number) => <path key={`${x}-${y}`} d={`M${x},${y + dy * L} L${x},${y} L${x + dx * L},${y}`} {...st} />;
  return <svg width={1080} height={1920} style={{position: "absolute", inset: 0, pointerEvents: "none"}}>{[k(x0, y0, 1, 1), k(x1, y0, -1, 1), k(x0, y1, 1, -1), k(x1, y1, -1, -1)]}</svg>;
};

/** Brass object floor / Level line with glow (theme.fx.floorY). */
export const Floor: React.FC = () => {
  const t = useTheme();
  const y = t.fx?.floorY;
  if (!y) return null;
  return <div style={{position: "absolute", left: 0, right: 0, top: y - 2, height: 4, background: t.c.accent, boxShadow: `0 0 18px ${t.c.accent}55`}} />;
};

/** Signature (1): a soft key-light band sweeps left -> right over the first 0.4 s (text stays legible). */
export const OpeningSweep: React.FC<{dur?: number}> = ({dur = 12}) => {
  const t = useTheme();
  const f = useCurrentFrame();
  if (!t.fx?.sweep || f > dur) return null;
  const p = f / dur, x = -700 + 2200 * p;
  return <div style={{position: "absolute", top: 0, bottom: 0, left: x, width: 600, pointerEvents: "none", mixBlendMode: "screen",
    background: `linear-gradient(100deg, transparent, ${t.fx.light?.color ?? "#FFFFFF"}22 40%, ${t.fx.light?.color ?? "#FFFFFF"}40 50%, ${t.fx.light?.color ?? "#FFFFFF"}22 60%, transparent)`}} />;
};

/** Signature (2): the one transition – a light wipe running along the Level, 8 frames, left -> right.
 * Put it at the cut; the bright head hides the change underneath. */
export const LevelWipe: React.FC<{at: number; y: number; dur?: number}> = ({at, y, dur = 8}) => {
  const t = useTheme();
  const f = useCurrentFrame();
  const p = (f - at) / dur;
  if (p < 0 || p > 1.6) return null;
  const head = 65 + 950 * Math.min(1, p), fade = p > 1 ? 1 - (p - 1) / 0.6 : 1;
  return <div style={{position: "absolute", inset: 0, pointerEvents: "none", opacity: fade}}>
    <div style={{position: "absolute", left: 0, width: head, top: y - 3, height: 6, background: t.c.accent, boxShadow: `0 0 28px 6px ${t.c.accent}88`}} />
    <div style={{position: "absolute", left: head - 260, width: 520, top: 0, bottom: 0, mixBlendMode: "screen",
      background: `linear-gradient(90deg, transparent, ${t.c.accent}30 50%, transparent)`}} />
  </div>;
};
