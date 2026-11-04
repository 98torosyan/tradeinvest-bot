// Theme = the ONLY place where colours, fonts, radii and motion constants live.
// Every component reads from a Theme object, so a re-skin is: add one object to THEMES, pass `theme: "<name>"`.
// PLACEHOLDER is deliberately neutral (greys + one temporary accent) until brand/BRAND.md is final.

export type FontFace = {weight: number | string; file: string; unicodeRange?: string; stretch?: string}; // variable fonts: weight "100 900", stretch "62.5% 100%"
export type FontSpec = {family: string; faces: FontFace[]; fallback: string};

export type Theme = {
  name: string;
  c: {
    bg: string; surface: string; fg: string; muted: string; grid: string;
    accent: string; onAccent: string;       // accent fill + the text colour that sits on it
    up: string; down: string;               // candle bodies
    a: string; b: string;                   // scenario 1 / scenario 2 (two-scenario Reels)
    warn: string;                           // stop loss, loss counters
    zone: string;                           // translucent fill for zones
    accentText?: string;                    // accent used for TEXT when it differs from the fill accent (e.g. brass ink on Tuff)
    hero?: string;                          // solid ink of the giant interlocking word (a deep tone, so the chart stays the hero)
  };
  font: {display: FontSpec; body: FontSpec; mono: FontSpec};
  type: {hook: number; title: number; body: number; small: number; hookWeight: number; bodyWeight: number; lh: number; track: string;
    hero?: number; displayStretch?: string; displayTrack?: string; labelTrack?: string;
    displayVar?: string; bodyVar?: string; labelVar?: string; labelFont?: "mono" | "body"};   // font-variation-settings per role      // hero = giant interlocking word
  fx?: {                                     // atmosphere: everything that makes a frame feel lit and tactile
    grain: number;                           // film grain opacity 0..0.2 (animated, SVG turbulence)
    grainBlend?: "overlay" | "multiply";
    corners?: {len: number; stroke: number; opacity: number};   // viewfinder corner marks
    floorY?: number;                         // brass Level / object floor line (under the IG UI)
    sweep?: boolean;                         // signature light sweep over the first 0.4 s
    light?: {color: string; x: number; y: number; r: number; alpha: number}; // cinematic key light (drifts slowly)
    rim?: {color: string; alpha: number};    // second, cooler light from the opposite corner
    vignette: number;                        // 0..1
    candle: "flat" | "sculpt";               // sculpt = gradient-lit bodies with soft shadow
    sculpt?: {upTop: string; upBot: string; dnTop: string; dnBot: string; glow: string; dnStroke?: string};
  };
  r: {sm: number; md: number; lg: number};
  motion: {ease: [number, number, number, number]; damping: number; stagger: number; style?: "snappy" | "premium"}; // premium = slow expo, masked line reveals, no springs
  sfx: Record<string, string>;            // named event -> file in public/sfx (see SFX cue sheet in PROPOSAL.md)
};

const ARM = "U+0308,U+0530-058F,U+2010,U+2024,U+25CC,U+FB13-FB17";
const LAT = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD";
const noto = (w: number): FontFace[] => [
  {weight: w, file: `fonts/noto-sans-armenian-armenian-${w}-normal.woff2`, unicodeRange: ARM},
  {weight: w, file: `fonts/noto-sans-armenian-latin-${w}-normal.woff2`, unicodeRange: LAT},
];
const NOTO: FontSpec = {family: "TI Sans", faces: [500, 600, 700, 800].flatMap(noto), fallback: "sans-serif"};
const MONO: FontSpec = {family: "TI Mono", faces: [500, 700, 800].map(w => ({weight: w, file: `fonts/jetbrains-mono-latin-${w}-normal.woff2`})), fallback: "monospace"};

const SFX = {
  hook: "sfx/impact.mp3",     // frame 0 hit under the hook
  word: "sfx/tick.mp3",       // a key word lands / counter step
  draw: "sfx/whoosh2.mp3",    // a line, zone or path starts drawing
  swap: "sfx/whoosh.mp3",     // scene change / camera move
  reveal: "sfx/pop.mp3",      // a tag, chip or marker pops in
  build: "sfx/riser.mp3",     // tension before the payoff
  resolve: "sfx/chime.mp3",   // payoff / rule lands
  hit: "sfx/impact.mp3",      // low drop: price hits the level / a loss lands
  ident: "sfx/logo.mp3",      // end-card ident (brand v2 should replace with a 2-note ident)
  // second kit: UI SFX by Yuki Capital (CC0, github.com/romainsimon/uisfx), used on alternate days
  swap2: "sfx/uisfx/cinematic_swipe.mp3",
  hit2: "sfx/uisfx/cinematic_warning.mp3",
  resolve2: "sfx/uisfx/cinematic_success.mp3",
  hook2: "sfx/uisfx/cinematic_snap.mp3",
  tap: "sfx/uisfx/studio_press.mp3",
};

export const PLACEHOLDER: Theme = {
  name: "placeholder",
  c: {
    bg: "#0F1012", surface: "#1A1B1F", fg: "#F3F3F1", muted: "#A3A3A8", grid: "rgba(255,255,255,0.06)",
    accent: "#E8FF5A", onAccent: "#0F1012",
    up: "#F3F3F1", down: "#6B6B72",
    a: "#7FB2FF", b: "#C6A2FF", warn: "#FF7A6B",
    zone: "rgba(232,255,90,0.14)",
  },
  font: {display: NOTO, body: NOTO, mono: MONO},
  type: {hook: 104, title: 72, body: 46, small: 30, hookWeight: 800, bodyWeight: 600, lh: 1.08, track: "-0.01em"},
  r: {sm: 8, md: 16, lg: 28},
  motion: {ease: [0.2, 0.8, 0.2, 1], damping: 16, stagger: 3},
  sfx: SFX,
};

// DEMO ONLY (not a brand proposal): proves the components carry the owner's reference level —
// warm cinematic light, grain, sculpted chart, giant high-contrast serif display, letter-spaced labels, slow easing.
const SERIF: FontSpec = {family: "TI Serif", fallback: "serif", faces: [
  {weight: "100 900", stretch: "62.5% 100%", file: "fonts/noto-serif-armenian-armenian-wdth-normal.woff2", unicodeRange: ARM},
  {weight: "100 900", stretch: "62.5% 100%", file: "fonts/noto-serif-armenian-latin-wdth-normal.woff2", unicodeRange: LAT}]};
const SANSV: FontSpec = {family: "TI SansV", fallback: "sans-serif", faces: [
  {weight: "100 900", stretch: "62.5% 100%", file: "fonts/noto-sans-armenian-armenian-wdth-normal.woff2", unicodeRange: ARM},
  {weight: "100 900", stretch: "62.5% 100%", file: "fonts/noto-sans-armenian-latin-wdth-normal.woff2", unicodeRange: LAT}]};
export const EDITORIAL_DEMO: Theme = {
  name: "editorial-demo",
  c: {
    bg: "#12100E", surface: "#1C1916", fg: "#EFE8DC", muted: "#B3A897", grid: "rgba(239,232,220,0.07)",
    accent: "#D8B26A", onAccent: "#12100E", up: "#EFE8DC", down: "#7D7366",
    a: "#EFE8DC", b: "#D8B26A", warn: "#E0805F", zone: "rgba(216,178,106,0.13)", hero: "#3B2F1E",
  },
  font: {display: SERIF, body: SANSV, mono: MONO},
  type: {hook: 112, title: 80, body: 46, small: 30, hookWeight: 600, bodyWeight: 500, lh: 1.02, track: "-0.025em",
    hero: 400, displayStretch: "100%", displayTrack: "-0.04em", labelTrack: "0.22em"},
  r: {sm: 2, md: 4, lg: 8},
  motion: {ease: [0.16, 1, 0.3, 1], damping: 200, stagger: 4, style: "premium"},
  sfx: SFX,
  fx: {grain: 0.11, light: {color: "#FFB766", x: 0.82, y: 0.18, r: 0.9, alpha: 0.30}, rim: {color: "#6E8BFF", alpha: 0.10}, vignette: 0.65,
    candle: "sculpt", sculpt: {upTop: "#FFF6E6", upBot: "#B9A27C", dnTop: "#6E655A", dnBot: "#2B2621", glow: "rgba(255,190,110,0.35)"}},
};

// DEMO ONLY: light "paper" variant (cream / ink / one red-orange) for suspense + collage Reels.
export const PAPER_DEMO: Theme = {
  ...EDITORIAL_DEMO,
  name: "paper-demo",
  c: {
    bg: "#EFE9DE", surface: "#E4DCCD", fg: "#15130F", muted: "#5F584D", grid: "rgba(21,19,15,0.08)",
    accent: "#E2522B", onAccent: "#FBF7F0", up: "#B9AE9B", down: "#15130F",
    a: "#15130F", b: "#E2522B", warn: "#E2522B", zone: "rgba(226,82,43,0.16)", hero: "#E4DCCD",
  },
  fx: {grain: 0.07, light: {color: "#FFFFFF", x: 0.7, y: 0.25, r: 1.0, alpha: 0.55}, vignette: 0.12, candle: "sculpt",
    sculpt: {upTop: "#C9BFAD", upBot: "#A39883", dnTop: "#3A352E", dnBot: "#0E0C0A", glow: "rgba(0,0,0,0.18)"}},
};

// ---------------------------------------------------------------- BRAND v2 «Գիշերային Սևան» (D1)
// tokens: brand/v2/tokens.json. Sevan = deep ground (analysis, numbers, suspense), Tuff = light ground (psychology/contrast).
const ARMV: FontSpec = {family: "ATI Sevan", fallback: "sans-serif", faces: SANSV.faces};
const SFX_V2 = {...SFX, ident: "sfx/ident2.mp3", hit: "sfx/impact.mp3"};
export const SEVAN: Theme = {
  name: "sevan",
  c: {
    bg: "#0F1E22", surface: "#18282C", fg: "#EDE4D3", muted: "#9FB0AE", grid: "rgba(237,228,211,0.07)",
    accent: "#D6AE66", onAccent: "#0F1E22", up: "#D6AE66", down: "#8C7A55",
    a: "#7FA6C9", b: "#E0674F", warn: "#E0674F", zone: "rgba(214,174,102,0.14)", hero: "#18282C",
  },
  font: {display: ARMV, body: ARMV, mono: ARMV},
  type: {hook: 150, title: 120, body: 40, small: 28, hookWeight: 900, bodyWeight: 450, lh: 0.84, track: "-0.02em",
    hero: 330, displayTrack: "-0.02em", labelTrack: "0.16em",
    displayVar: "'wght' 900, 'wdth' 62.5", bodyVar: "'wght' 450, 'wdth' 100", labelVar: "'wght' 600, 'wdth' 87.5", labelFont: "body"},
  r: {sm: 6, md: 12, lg: 999},
  motion: {ease: [0.16, 1, 0.3, 1], damping: 200, stagger: 3, style: "premium"},
  sfx: SFX_V2,
  fx: {grain: 0.2, grainBlend: "overlay", corners: {len: 34, stroke: 2, opacity: 0.55}, floorY: 1720, sweep: true,
    light: {color: "#FFE2B0", x: 0.15, y: 0.2, r: 0.95, alpha: 0.16}, rim: {color: "#FFB36B", alpha: 0.07}, vignette: 0.55, candle: "sculpt",
    sculpt: {upTop: "#F2D79C", upBot: "#9C7634", dnTop: "#2B3F43", dnBot: "#0A1517", glow: "rgba(214,174,102,0.30)", dnStroke: "#B8955A"}},
};
export const TUFF: Theme = {
  ...SEVAN,
  name: "tuff",
  c: {
    bg: "#EDE4D3", surface: "#E2D7C2", fg: "#0F1E22", muted: "#5E5A52", grid: "rgba(15,30,34,0.08)",
    accent: "#D6AE66", accentText: "#7A5A22", onAccent: "#0F1E22", up: "#D6AE66", down: "#18282C",
    a: "#2F4E78", b: "#B23A26", warn: "#B23A26", zone: "rgba(214,174,102,0.22)", hero: "#E2D7C2",
  },
  fx: {...SEVAN.fx!, grain: 0.16, grainBlend: "multiply", light: {color: "#FFFFFF", x: 0.2, y: 0.18, r: 1, alpha: 0.45}, rim: undefined, vignette: 0.1,
    sculpt: {upTop: "#E9C987", upBot: "#A07A38", dnTop: "#2B3F43", dnBot: "#0A1517", glow: "rgba(15,30,34,0.18)", dnStroke: "#18282C"}},
};


// ---------------------------------------------------------------- «TI Rise» (owner's logo: ink + white + orange) — Nov 2026 production theme
export const TI: Theme = {
  ...SEVAN,
  name: "ti",
  c: {
    bg: "#0B0B0C", surface: "#1B1C1F", fg: "#F2EFE8", muted: "#A3A09A", grid: "rgba(242,239,232,0.06)",
    accent: "#FF8A00", onAccent: "#0B0B0C", up: "#FF8A00", down: "#5C5A56",
    a: "#7FA6C9", b: "#E25B4B", warn: "#E25B4B", zone: "rgba(255,138,0,0.14)", hero: "#1B1C1F",
  },
  fx: {...SEVAN.fx!, light: {color: "#FFD3A0", x: 0.15, y: 0.2, r: 0.95, alpha: 0.14}, rim: {color: "#FF9A3C", alpha: 0.06},
    sculpt: {upTop: "#FFC27A", upBot: "#B5651A", dnTop: "#2A2B2F", dnBot: "#0B0B0C", glow: "rgba(255,138,0,0.30)", dnStroke: "#8A5A2A"}},
};
export const TI_PAPER: Theme = {
  ...TUFF,
  name: "ti_paper",
  c: {
    bg: "#F2EFE8", surface: "#E7E2D8", fg: "#0B0B0C", muted: "#5C5850", grid: "rgba(17,18,20,0.07)",
    accent: "#FF8A00", accentText: "#C25E00", onAccent: "#0B0B0C", up: "#FF8A00", down: "#1B1C1F",
    a: "#2F4E78", b: "#C03A2B", warn: "#C03A2B", zone: "rgba(255,138,0,0.2)", hero: "#E7E2D8",
  },
};

// The outgoing "v3" brand, kept only to prove a re-skin is one object.
export const V3: Theme = {
  ...PLACEHOLDER,
  name: "v3",
  c: {
    bg: "#0B0B0C", surface: "#17171A", fg: "#F2EFE8", muted: "#8E8A83", grid: "rgba(255,255,255,0.05)",
    accent: "#FF8A00", onAccent: "#0B0B0C", up: "#F2EFE8", down: "#5A5650",
    a: "#F2EFE8", b: "#FF8A00", warn: "#FF8A00", zone: "rgba(255,138,0,0.17)",
  },
};

export const THEMES: Record<string, Theme> = {placeholder: PLACEHOLDER, v3: V3, "editorial-demo": EDITORIAL_DEMO, "paper-demo": PAPER_DEMO, sevan: SEVAN, tuff: TUFF, ti: TI, ti_paper: TI_PAPER};
export const getTheme = (t?: string | Theme): Theme => (typeof t === "object" ? t : THEMES[t ?? "placeholder"] ?? PLACEHOLDER);

// Instagram Reel safe zone (1080x1920). All text must sit inside it.
export const SAFE = {x0: 65, x1: 1015, y0: 270, y1: 1250};
