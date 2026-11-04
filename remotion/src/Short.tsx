// Short lesson Reel (7–20 s) in brand TI Rise. Content comes from reels/content/shorts.json via props.
// Structure: hook (legible at frame 0) → 2–4 beats (big number or a line) → rule (marker on the key word) → 1 s end card.
// Timing follows the executive rule: ≥ 0.5 s per word + 0.5 s per card, minimum 1.6 s per card.
import React from "react";
import {Img, Sequence, staticFile, useCurrentFrame} from "remotion";
import {ThemeRoot, useTheme, Cue, pr, ff} from "./lib/core";
import {Words} from "./lib/Kinetic";
import {EditorialMarks, LevelWipe} from "./lib/Atmosphere";
import {EndCard, END_FRAMES} from "./lib/EndCard";
import {getTheme} from "./theme";
import {Visual, VisualSpec} from "./Visuals";
import {enterStyle, shake, Particles, Backdrop, TRANSITIONS} from "./lib/Fx";

export type Beat = {big?: string; text?: string; loss?: boolean};
export type ShortProps = {
  variant?: number; theme?: string; index: string; series: string; tag?: string;
  hook: string; beats: Beat[]; rule: string; hero?: string; visual?: VisualSpec; cta?: "kw" | "dm" | "none";
};

const FPS = 30;
const words = (s = "") => s.replace(/[|*_~]/g, " ").split(/\s+/).filter(Boolean).length;
const cardLen = (n: number) => Math.round(Math.max(1.6, 0.5 * n + 0.5) * FPS);

export const timeline = (P: ShortProps) => {
  const cards = [P.hook, ...P.beats.map(b => [b.big, b.text].filter(Boolean).join(" ")), P.rule];
  const starts: number[] = []; let t = 0;
  cards.forEach((c, i) => {starts.push(t); t += cardLen(words(c));});
  t += 12;                                    // let the rule breathe
  return {starts, body: t, total: t + END_FRAMES};
};

// Four camera moves so consecutive days never feel the same; the hero never stops moving.
const Hero: React.FC<{src: string; body: number; v: number; orange?: boolean}> = ({src, body, v, orange}) => {
  const f = useCurrentFrame();
  const lin = pr(f, 0, body, (x) => x);
  const bob = Math.sin(f / 22);
  let scale = 1, x = 0, y = 0, rot = 0;
  if (v === 0) {scale = 1 + 0.08 * lin; y = -24 * lin;}                       // slow push-in
  if (v === 1) {scale = 1.1 - 0.08 * lin; x = 30 - 60 * lin;}                 // pull-back + lateral pan
  if (v === 2) {scale = 1.04 + 0.02 * bob; y = 14 * bob; rot = 0.8 * Math.sin(f / 35);}   // floating object
  if (v === 3) {scale = 1 + 0.12 * Math.pow(lin, 1.6); x = -20 * lin; rot = -1.2 * lin;}  // accelerating dolly
  const beat = Math.max(0, 1 - Math.abs((f % 90) - 45) / 12);                  // a light pulse every 3 s
  return <div style={{position: "absolute", inset: 0, scale: String(scale), translate: `${x}px ${y}px`, rotate: `${rot}deg`, transformOrigin: "50% 78%"}}>
    <Img src={staticFile(`hero/${src}.png`)} style={{position: "absolute", left: 0, top: 160, width: 1080, height: 1920, filter: `brightness(${1 + 0.12 * beat})${orange ? " sepia(0.25) saturate(1.45) hue-rotate(-12deg)" : ""}`}} />
  </div>;
};

const Big: React.FC<{text: string; color: string; at: number}> = ({text, color, at}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const a = pr(f, at, at + 14);
  return <div style={{fontFamily: ff(t, "display"), fontVariationSettings: t.type.displayVar, fontSize: text.length > 5 ? 230 : 300, lineHeight: 0.9,
    letterSpacing: "-0.02em", color, opacity: a, translate: `0px ${(1 - a) * 40}px`}}>{text}</div>;
};

const MODES = ["rise", "pop", "mask", "pop"] as const;
const Scene: React.FC<ShortProps & {starts: number[]; body: number}> = (P) => {
  const f = useCurrentFrame();
  const mode = MODES[Math.floor((P.variant ?? 0) / 4) % 4];
  const t = useTheme();
  const n = P.beats.length;
  const ruleAt = P.starts[n + 1];
  const v = P.variant ?? 0;
  const trans = TRANSITIONS[(v + 1) % TRANSITIONS.length];
  const block = (i: number, child: React.ReactNode) => {
    const a = P.starts[i], b = i + 1 < P.starts.length ? P.starts[i + 1] : P.body + 99;
    if (f < a - 2 || f > b + 10) return null;
    const fadeOut = i + 1 < P.starts.length ? 1 - pr(f, b - 6, b + 4) : 1;
    const enter = i === 0 ? {} : enterStyle(trans, f, a);       // hook stays legible at frame 0
    const hitLoss = i > 0 && i <= n && P.beats[i - 1]?.loss;
    return <div key={i} style={{position: "absolute", left: 65, right: 65, top: 372, opacity: fadeOut}}>
      <div style={{...enter, translate: hitLoss ? shake(f, a + 2) : enter.translate}}>{child}</div></div>;
  };
  return <>
    <Backdrop kind={v % 4} />
    {P.visual ? <Visual v={P.visual} starts={P.starts} body={P.body} /> : <Hero src={P.hero ?? "coins2"} body={P.body} v={(P.variant ?? 0) % 4} orange={(P.theme ?? "ti").startsWith("ti")} />}
    <EditorialMarks index={P.index} left={P.series} right={P.tag} y0={276} />
    {block(0, <Words text={P.hook} mode="settle" size={124} lh={1.02} />)}
    {P.beats.map((b, k) => block(k + 1, <>
      {b.big && <Big text={b.big} at={P.starts[k + 1] + 2} color={b.loss ? t.c.warn : (t.c.accentText ?? t.c.accent)} />}
      {b.text && <div style={{marginTop: b.big ? 26 : 0}}><Words text={b.text} start={P.starts[k + 1] + (b.big ? 10 : 2)} mode={mode} size={b.big ? 76 : 100} lh={1.04} /></div>}
    </>))}
    {block(n + 1, <Words text={P.rule} start={ruleAt + 2} mode={mode} size={116} lh={1.04} markAt={ruleAt + 26} />)}
    {v % 2 === 0 && <Particles at={ruleAt + 26} x={300} y={640} />}
  </>;
};

// Retention: the Level line doubles as a progress bar (bright fill + glowing head), so viewers see the Reel is short.
const Progress: React.FC<{body: number}> = ({body}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const y = t.fx?.floorY ?? 1720;
  const w = 1080 * Math.min(1, f / body);
  return <>
    <div style={{position: "absolute", left: 0, top: y - 3, width: w, height: 6, background: t.c.fg, opacity: 0.9}} />
    <div style={{position: "absolute", left: w - 7, top: y - 7, width: 14, height: 14, borderRadius: 7, background: t.c.fg, boxShadow: `0 0 16px ${t.c.accent}`}} />
  </>;
};

export const Short: React.FC<ShortProps> = (P) => {
  const theme = getTheme(P.theme ?? "ti");
  const {starts, body} = timeline(P);
  const k2 = (P.variant ?? 0) % 2 ? "2" : "";      // alternate sound kit on odd variants
  return (
    <ThemeRoot theme={theme}>
      <Sequence durationInFrames={body} layout="none"><Scene {...P} starts={starts} body={body} />
        {starts.slice(1).map((s, i) => <LevelWipe key={i} at={s - 4} y={1720} />)}
        <Progress body={body} />
      </Sequence>
      <Sequence from={body} layout="none"><EndCard cta={P.cta ?? "none"} /></Sequence>
      <Cue at={0} name={`hook${k2}`} volume={0.45} />
      {starts.slice(1, -1).map((s, i) => <Cue key={i} at={s} name={(P.beats[i]?.loss || P.beats[i]?.big ? "hit" : "swap") + k2} volume={0.5} />)}
      <Cue at={starts[starts.length - 1] + 26} name={`resolve${k2}`} volume={0.45} />
      <Cue at={body} name="ident" volume={0.7} />
    </ThemeRoot>
  );
};
