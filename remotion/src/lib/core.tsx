// Core helpers: theme context, font loading (blocks rendering until every face is ready),
// easing/progress helpers, SFX cues and a safe-zone guide.
import React, {createContext, useContext, useEffect, useState} from "react";
import {AbsoluteFill, Audio, Easing, Sequence, continueRender, delayRender, interpolate, spring, staticFile} from "remotion";
import {SAFE, Theme, PLACEHOLDER} from "../theme";
import {Atmosphere, Grain, Viewfinder, Floor, OpeningSweep} from "./Atmosphere";

const Ctx = createContext<Theme>(PLACEHOLDER);
export const useTheme = () => useContext(Ctx);
export const ThemeProvider = Ctx.Provider;

const loaded = new Set<string>();
const useFonts = (t: Theme) => {
  const [handle] = useState(() => delayRender(`fonts:${t.name}`));
  useEffect(() => {
    const specs = [t.font.display, t.font.body, t.font.mono];
    const jobs: Promise<unknown>[] = [];
    for (const s of specs) for (const f of s.faces) {
      const key = `${s.family}|${f.weight}|${f.file}`;
      if (loaded.has(key)) continue;
      loaded.add(key);
      const face = new FontFace(s.family, `url(${staticFile(f.file)})`, {weight: String(f.weight), unicodeRange: f.unicodeRange, stretch: f.stretch});
      document.fonts.add(face);
      jobs.push(face.load());
    }
    Promise.all(jobs).then(() => continueRender(handle)).catch((e) => {console.error(e); continueRender(handle);});
  }, [t, handle]);
};

export const ThemeRoot: React.FC<{theme: Theme; guides?: boolean; children: React.ReactNode}> = ({theme, guides, children}) => {
  useFonts(theme);
  return (
    <Ctx.Provider value={theme}>
      <AbsoluteFill style={{background: theme.c.bg, color: theme.c.fg, fontFamily: ff(theme, "body"), overflow: "hidden"}}>
        <Atmosphere />
        <Floor />
        {children}
        <Viewfinder />
        <OpeningSweep />
        <Grain />
        {guides && <SafeGuide />}
      </AbsoluteFill>
    </Ctx.Provider>
  );
};

export const ff = (t: Theme, k: "display" | "body" | "mono") => `"${t.font[k].family}", ${t.font[k].fallback}`;

// ---- timing
export const ease = (t: Theme) => Easing.bezier(...t.motion.ease);
/** 0..1 progress between frames a and b, clamped, eased. */
export const pr = (f: number, a: number, b: number, e: (x: number) => number = Easing.bezier(0.2, 0.8, 0.2, 1)) =>
  interpolate(f, [a, b], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e});
export const spr = (f: number, fps: number, delay = 0, damping = 16) => spring({frame: f - delay, fps, config: {damping}});
export const sec = (s: number, fps: number) => Math.round(s * fps);

// ---- sound: named cues, files resolved through the theme
export const Cue: React.FC<{at: number; name: string; volume?: number}> = ({at, name, volume = 0.6}) => {
  const t = useTheme();
  const file = t.sfx[name];
  if (!file) return null;
  return (
    <Sequence from={at} durationInFrames={90} name={`sfx:${name}`} layout="none">
      <Audio src={staticFile(file)} volume={volume} />
    </Sequence>
  );
};

// ---- safe zone guide (debug only)
export const SafeGuide: React.FC = () => (
  <svg width={1080} height={1920} style={{position: "absolute", inset: 0, pointerEvents: "none"}}>
    <rect x={SAFE.x0} y={SAFE.y0} width={SAFE.x1 - SAFE.x0} height={SAFE.y1 - SAFE.y0} fill="none" stroke="#00FFFF" strokeWidth={3} strokeDasharray="14 10" />
  </svg>
);

export const fmtNum = (v: number, dec = 0) => {
  const s = Math.abs(v).toFixed(dec);
  const [i, d] = s.split(".");
  const ii = i.replace(/\B(?=(\d{3})+(?!\d))/g, " "); // no-break space as thousands separator
  return (v < 0 ? "−" : "") + ii + (d ? "," + d : "");    // Armenian decimal comma
};
