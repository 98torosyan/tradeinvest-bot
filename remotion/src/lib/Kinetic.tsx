// Kinetic Armenian typography. Words are the animation unit (never split Armenian words into letters:
// ligature-free but splitting breaks kerning and reading rhythm).
// Inline markup in copy strings:  |  = line break,  *word* = accent colour,  _word_ = marker highlight,  ~word~ = strike.
import React from "react";
import {interpolate, useCurrentFrame, useVideoConfig, Easing} from "remotion";
import {useTheme, ff, pr, spr, fmtNum} from "./core";

type Tok = {w: string; acc?: boolean; mark?: boolean; strike?: boolean; br?: boolean};
export const tokenize = (s: string): Tok[] => {
  const out: Tok[] = [];
  s.split("|").forEach((line, li) => {
    if (li > 0) out.push({w: "", br: true});
    for (const raw of line.trim().split(/\s+/).filter(Boolean)) {
      let w = raw, acc = false, mark = false, strike = false;
      const m = (ch: string) => {
        const e = ch === "*" ? "\\*" : ch;               // only * needs escaping; _ and ~ are literal
        const re = new RegExp(`^([^\\p{L}\\p{N}*_~]*)${e}(.+)${e}([^\\p{L}\\p{N}*_~]*)$`, "u");
        const r = w.match(re); if (r) {w = r[1] + r[2] + r[3]; return true;} return false;
      };
      if (m("*")) acc = true; if (m("_")) mark = true; if (m("~")) strike = true;
      out.push({w, acc, mark, strike});
    }
  });
  return out;
};

export type WordsMode = "settle" | "rise" | "pop" | "slam" | "mask";
/**
 * Word-by-word text. mode:
 *  settle – fully legible from `start` (use for hooks at frame 0), words just settle into place;
 *  rise   – each word slides up + fades in, staggered;
 *  pop    – spring scale per word;
 *  slam   – whole line drops from 1.35x (one big beat);
 *  mask   – each word slides up out of its own baseline mask, slow expo (premium themes remap rise/pop/slam to this).
 * `out` = frame where the block exits (fade + lift).
 */
export const Words: React.FC<{
  text: string; start?: number; mode?: WordsMode; stagger?: number; size?: number; weight?: number; color?: string;
  font?: "display" | "body" | "mono"; align?: "left" | "center"; lh?: number; out?: number; style?: React.CSSProperties; markAt?: number;
}> = ({text, start = 0, mode: mode0 = "rise", stagger, size, weight, color, font = "display", align = "left", lh, out, style, markAt}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = useTheme();
  const premium = t.motion.style === "premium";
  const mode: WordsMode = premium && mode0 === "rise" ? "mask" : mode0;
  const slow = Easing.bezier(...t.motion.ease);
  const st = stagger ?? t.motion.stagger;
  const toks = tokenize(text);
  let k = 0;
  const exit = out === undefined ? 0 : pr(f, out, out + (premium ? 12 : 8), Easing.in(Easing.cubic));
  const lastWord = toks.filter(x => !x.br).length - 1;
  const markStart = markAt ?? start + st * lastWord + 6;
  return (
    <div style={{fontFamily: ff(t, font), fontSize: size ?? t.type.title, fontWeight: weight ?? t.type.hookWeight, lineHeight: lh ?? t.type.lh,
      letterSpacing: font === "display" ? (t.type.displayTrack ?? t.type.track) : t.type.track, fontStretch: font === "display" ? t.type.displayStretch : undefined,
      fontVariationSettings: font === "display" ? t.type.displayVar : font === "body" ? t.type.bodyVar : undefined, wordSpacing: font === "display" && t.type.displayVar ? "0.16em" : undefined, color: color ?? t.c.fg, textAlign: align, opacity: 1 - exit, translate: `0px ${-exit * 30}px`, ...style}}>
      {toks.map((tk, i) => {
        if (tk.br) return <br key={i} />;
        const d = start + st * k++;
        let o = 1, ty = 0, sc = 1;
        if (mode === "settle") {const a = pr(f, d, d + 10); sc = 1.04 - 0.04 * a; ty = 8 * (1 - a);}
        if (mode === "rise") {const a = pr(f, d, d + 9); o = a; ty = 34 * (1 - a);}
        if (mode === "pop") {const a = spr(f, fps, d, 12); o = Math.min(1, a * 2); sc = 0.6 + 0.4 * a;}
        if (mode === "mask") {const a = pr(f, d, d + 20, slow); ty = 1.15 * (1 - a);}
        if (mode === "slam") {const a = spr(f, fps, start, 11); o = Math.min(1, (f - start + 1) / 3); sc = 1.35 - 0.35 * a;}
        const col = tk.acc ? (t.c.accentText ?? t.c.accent) : undefined;
        const mp = tk.mark ? pr(f, markStart, markStart + 10) : 0;
        const sp = tk.strike ? pr(f, markStart, markStart + 10) : 0;
        return (
          <React.Fragment key={i}><span style={mode === "mask" ? {display: "inline-block", overflow: "hidden", verticalAlign: "top", padding: "0.06em 0.04em 0.24em", margin: "-0.06em -0.04em -0.24em"} : {display: "contents"}}><span style={{display: "inline-block", whiteSpace: "pre", opacity: o, translate: mode === "mask" ? `0px ${ty * 100}%` : `0px ${ty}px`, scale: String(sc), transformOrigin: "50% 80%", color: tk.mark && mp > 0.5 ? t.c.onAccent : col, position: "relative"}}>
            {tk.mark && <span style={{position: "absolute", left: "-0.08em", right: "-0.08em", top: "0.08em", bottom: "0.02em", background: t.c.accent, borderRadius: t.r.sm,
              transformOrigin: "0% 50%", scale: `${mp} 1`, zIndex: -1}} />}
            {tk.w}
            {tk.strike && <span style={{position: "absolute", left: "-0.04em", top: "52%", height: "0.09em", width: `${sp * 108}%`, background: t.c.warn, borderRadius: 4}} />}
          </span></span>{" "}</React.Fragment>
        );
      })}
    </div>
  );
};

/** Odometer-style number roll (digits scroll like a mechanical counter). */
export const CounterRoll: React.FC<{from: number; to: number; start: number; dur: number; dec?: number; prefix?: string; suffix?: string; size?: number; color?: string; weight?: number; display?: boolean}> =
  ({from, to, start, dur, dec = 0, prefix = "", suffix = "", size = 120, color, weight = 800, display}) => {
    const f = useCurrentFrame();
    const t = useTheme();
    const val = interpolate(f, [start, start + dur], [from, to], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic)});
    const units = Math.abs(val) * 10 ** dec;
    const tmpl = fmtNum(to, dec).replace("−", "");
    let k = 0;
    const cells = tmpl.split("").reverse().map((ch, idx) => {
      if (!/\d/.test(ch)) return <span key={idx} style={{fontFamily: ff(t, "display"), margin: "0 -0.06em"}}>{ch}</span>;
      const pos = k++;
      const q = units / 10 ** pos;
      const d = Math.floor(q) % 10;
      const lower = units % 10 ** pos;
      const off = pos === 0 ? (units % 10) : d + Math.max(0, Math.min(1, (lower / 10 ** pos - 0.9) / 0.1));
      const lead = pos > 0 && q < 1 && pos >= dec + 1 ? Math.max(0, q * 1.2 - 0.2) : 1;
      return (
        <span key={idx} style={{display: "inline-block", height: "1em", overflow: "hidden", verticalAlign: "top", opacity: lead}}>
          <span style={{display: "block", translate: `0px ${-off}em`}}>
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0].map((n, j) => <span key={j} style={{display: "block", height: "1em", lineHeight: "1em"}}>{n}</span>)}
          </span>
        </span>
      );
    }).reverse();
    return (
      <div style={{fontFamily: ff(t, display ? "display" : "mono"), fontVariationSettings: display ? t.type.displayVar : undefined, fontSize: size, fontWeight: weight, lineHeight: "1em", color: color ?? t.c.fg, display: "flex", fontVariantNumeric: "tabular-nums", letterSpacing: "-0.03em"}}>
        <span>{(to < 0 ? "−" : "") + prefix}</span>{cells}<span>{suffix}</span>
      </div>
    );
  };

/** Small mono label (ticker, timeframe, date range) – the "data credibility" line. */
export const DataLine: React.FC<{text: string; start?: number; color?: string; size?: number}> = ({text, start = -10, color, size}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const a = pr(f, start, start + 10);
  return <div style={{fontFamily: ff(t, "mono"), fontSize: size ?? t.type.small, fontWeight: 700, color: color ?? t.c.muted, letterSpacing: "0.04em", opacity: a, whiteSpace: "nowrap"}}>{text}</div>;
};
