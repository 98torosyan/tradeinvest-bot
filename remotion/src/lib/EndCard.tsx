// Signature (3): end card ≤ 1 s, identical on every Reel – the Ա mark, «ARM TRADE INVEST», optional CTA pill, 2-note ident.
// Always on the deep ground (Sevan) even when the Reel itself is on Tuff, so the ending is recognisable.
import React from "react";
import {Img, staticFile, useCurrentFrame} from "remotion";
import {useTheme, pr, ThemeProvider, ff} from "./core";
import {Label, Viewfinder} from "./Atmosphere";
import {SEVAN, TI, Theme} from "../theme";

export const CTA_TEXT = {kw: "Գրիր «ԴԱՍ»", dm: "Գրիր DM «ԴԱՍ»"} as const;   // keyword stays exactly «ԴԱՍ» (community bot)
export const END_FRAMES = 30;

const Arrow: React.FC<{color: string}> = ({color}) =>
  <svg width={34} height={20} viewBox="0 0 34 20" style={{marginLeft: 14}}><path d="M2 10 H30 M22 3 L30 10 L22 17" stroke={color} strokeWidth={2.4} fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>;

const Card: React.FC<{cta: "kw" | "dm" | "none"; tagline?: string}> = ({cta, tagline}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const a = pr(f, 0, 10, (x) => 1 - Math.pow(1 - x, 4));
  return (
    <div style={{position: "absolute", inset: 0, background: t.c.bg}}>
      <div style={{position: "absolute", inset: 0, background: `radial-gradient(700px 900px at 50% 38%, ${t.c.accent}22, transparent 70%)`}} />
      <div style={{position: "absolute", left: 0, right: 0, top: 330, display: "flex", flexDirection: "column", alignItems: "center", gap: 30}}>
        <Img src={staticFile("brand/mark-on-ink.svg")} style={{width: 330, opacity: a, translate: `0px ${(1 - a) * 20}px`, scale: String(0.96 + 0.04 * a)}} />
        <div style={{fontFamily: ff(t, "body"), fontVariationSettings: "'wght' 800, 'wdth' 100", fontSize: 64, letterSpacing: "-0.01em"}}><span style={{color: t.c.fg}}>Trade</span><span style={{color: t.c.accent, fontVariationSettings: "'wght' 400, 'wdth' 100"}}>Invest</span></div>
        {tagline && <div style={{fontFamily: ff(t, "body"), fontVariationSettings: "'wght' 600, 'wdth' 100", fontSize: 30, letterSpacing: "0.42em", color: t.c.muted, opacity: a, marginTop: -6}}>{tagline}</div>}
        {cta !== "none" && <div style={{opacity: pr(f, 4, 12), marginTop: 18, border: `2px solid ${t.c.fg}`, borderRadius: 999, padding: "12px 36px",
          display: "flex", alignItems: "center", fontFamily: ff(t, "body"), fontVariationSettings: t.type.bodyVar, fontSize: 40, color: t.c.fg}}>
          {CTA_TEXT[cta]}<Arrow color={t.c.fg} /></div>}
      </div>
      <div style={{position: "absolute", left: 0, right: 0, top: (t.fx?.floorY ?? 1720) - 2, height: 4, background: t.c.accent, boxShadow: `0 0 18px ${t.c.accent}55`}} />
      <Viewfinder />
    </div>
  );
};

export const EndCard: React.FC<{cta?: "kw" | "dm" | "none"; tagline?: string; theme?: Theme}> = ({cta = "dm", tagline = "TRADING ACADEMY", theme}) => {
  const t = useTheme();
  const th = theme ?? (t.name === "tuff" ? SEVAN : t.name === "ti_paper" ? TI : t);
  return <ThemeProvider value={th}><Card cta={cta} tagline={tagline} /></ThemeProvider>;
};
