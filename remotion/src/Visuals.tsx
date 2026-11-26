// Topic visuals for the short lesson Reels. Every chart visual is drawn from REAL candles passed in by
// reels/shorts.py (different asset + window each time), so no two Reels share a picture.
// Visual area: x 90–990, y 830–1450 (decorative below the text band; key labels stay above ~1250 when possible).
import React from "react";
import {Img, staticFile, useCurrentFrame} from "remotion";
import {useTheme, ff, pr} from "./lib/core";
import {Candles, Level, Zone, Pin, PathArrow, makeScale, Grid, OHLC} from "./lib/Chart";

export type VisualSpec = {
  kind: "chart" | "level" | "stop" | "fomo" | "rr" | "split" | "multiplier" | "grid" | "image" | "glyph";
  cs?: OHLC[]; cs2?: OHLC[]; symbol?: string; tf?: string;
  entry?: number; stop?: number; target?: number; peak?: number; zone?: [number, number]; image?: string;
  labels?: Record<string, string>;
};

const BOX = {x: 90, y: 860, w: 900, h: 520};
const Tag: React.FC<{x: number; y: number; text: string; color: string; p: number; fill?: boolean}> = ({x, y, text, color, p, fill = true}) => {
  const t = useTheme();
  const w = text.length * 19 + 40;
  return <g opacity={p} transform={`translate(${x},${y}) scale(${0.85 + 0.15 * p})`}>
    <rect x={0} y={-24} width={w} height={48} rx={24} fill={fill ? color : "none"} stroke={color} strokeWidth={3} />
    <text x={w / 2} y={10} textAnchor="middle" fontSize={27} fontWeight={800} letterSpacing="0.06em" fill={fill ? t.c.onAccent : color} fontFamily={ff(t, "body")}>{text}</text>
  </g>;
};

const Caption: React.FC<{text?: string}> = ({text}) => {
  const t = useTheme();
  if (!text) return null;
  return <text x={BOX.x} y={BOX.y - 22} fontSize={28} fontWeight={600} letterSpacing="0.14em" fill={t.c.muted} fontFamily={ff(t, "body")}>{text}</text>;
};

export const Visual: React.FC<{v: VisualSpec; starts: number[]; body: number}> = ({v, starts, body}) => {
  const f = useCurrentFrame();
  const t = useTheme();
  const loss = t.c.warn, acc = t.c.accent;
  const s1 = starts[1] ?? 60, s2 = starts[2] ?? s1 + 60, s3 = starts[3] ?? s2 + 60;
  const cam = 1 + 0.05 * pr(f, 0, body, (x) => x);                       // slow, constant push: the frame never freezes
  const L = v.labels ?? {};

  if (v.kind === "glyph") {
    // calm line icon for non-chart topics (P2P, scams, security, law): soft amber glow that melts into the dark
    const G: Record<string, string> = {
      shield: "M0,-200 L170,-130 L170,10 C170,120 90,190 0,230 C-90,190 -170,120 -170,10 L-170,-130 Z M-70,10 L-15,65 L85,-45",
      lock: "M-150,-20 L150,-20 L150,210 L-150,210 Z M-95,-20 L-95,-95 C-95,-150 -50,-190 0,-190 C50,-190 95,-150 95,-95 L95,-20 M0,70 L0,130",
      key: "M-60,-60 m-90,0 a90,90 0 1,0 180,0 a90,90 0 1,0 -180,0 M3,3 L190,190 M120,120 L165,75 M160,160 L205,115",
      chat: "M-190,-150 L190,-150 L190,90 L-40,90 L-120,170 L-120,90 L-190,90 Z M-110,-60 L110,-60 M-110,10 L40,10",
      phone: "M-120,-220 L120,-220 L120,220 L-120,220 Z M-40,-180 L40,-180 M-25,175 L25,175 M-60,-40 L-10,10 L70,-80",
      warning: "M0,-210 L210,170 L-210,170 Z M0,-70 L0,60 M0,105 L0,115",
      bank: "M-210,-60 L0,-190 L210,-60 Z M-170,-30 L-170,150 M-85,-30 L-85,150 M0,-30 L0,150 M85,-30 L85,150 M170,-30 L170,150 M-220,185 L220,185",
      law: "M0,-200 L0,170 M-150,190 L150,190 M-190,-130 L190,-130 M-190,-130 L-260,30 L-120,30 Z M190,-130 L120,30 L260,30 Z",
      wallet: "M-200,-120 L170,-120 L170,180 L-200,180 Z M-200,-120 L110,-200 L140,-120 M70,10 L230,10 L230,90 L70,90 Z M120,50 L130,50",
    };
    const d = G[v.image ?? "shield"] ?? G.shield;
    const draw = pr(f, 4, s1 > 30 ? s1 : 40);
    const bob = 6 * Math.sin(f / 30);
    return <svg width={1080} height={1920} style={{position: "absolute", inset: 0, scale: String(cam), transformOrigin: "50% 62%"}}>
      <defs><radialGradient id="gglow"><stop offset="0" stopColor={acc} stopOpacity="0.22" /><stop offset="1" stopColor={acc} stopOpacity="0" /></radialGradient></defs>
      <circle cx={540} cy={1200} r={430} fill="url(#gglow)" />
      <g transform={`translate(540,${1200 + bob}) scale(0.9)`} fill="none" strokeLinecap="round" strokeLinejoin="round">
        {[[44, 0.08], [24, 0.16]].map(([w, o]) => <path key={w} d={d} stroke={acc} strokeWidth={w} strokeOpacity={o} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} />)}
        <path d={d} stroke={acc} strokeWidth={11} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} />
      </g>
    </svg>;
  }

  if (v.kind === "image") {
    const bob = Math.sin(f / 24);
    return <div style={{position: "absolute", inset: 0, scale: String(1.02 + 0.03 * pr(f, 0, body, (x) => x) + 0.01 * bob), transformOrigin: "50% 80%"}}>
      <Img src={staticFile(`hero/${v.image}.png`)} style={{position: "absolute", left: 0, top: 160, width: 1080, height: 1920, filter: t.name.startsWith("ti") ? "sepia(0.25) saturate(1.45) hue-rotate(-12deg)" : undefined}} />
    </div>;
  }

  if (v.kind === "multiplier") {
    const a = pr(f, s1, s1 + 24), b = pr(f, s2, s2 + 40);
    const H = 520, base = 1430;
    return <svg width={1080} height={1920} style={{position: "absolute", inset: 0, scale: String(cam), transformOrigin: "50% 75%"}}>
      <Caption text={L.caption ?? "LEVERAGE × 10"} />
      {[{x: 210, p: a, h: H * 0.1, lab: L.a ?? "−10%", sub: L.sa ?? "PRICE"}, {x: 600, p: b, h: H, lab: L.b ?? "−100%", sub: L.sb ?? "× 10"}].map((c, i) =>
        <g key={i}>
          <rect x={c.x} y={base - H} width={270} height={H} rx={18} fill="none" stroke={t.c.grid} strokeWidth={2} />
          <rect x={c.x} y={base - c.h * c.p} width={270} height={c.h * c.p} rx={18} fill={loss} opacity={0.9} />
          <text x={c.x + 135} y={base - Math.max(c.h * c.p, 0) - 26} textAnchor="middle" fontSize={64} fontWeight={800} fill={loss} opacity={c.p} fontFamily={ff(t, "display")}>{c.lab}</text>
          <text x={c.x + 135} y={base + 52} textAnchor="middle" fontSize={30} fontWeight={700} letterSpacing="0.14em" fill={t.c.muted} fontFamily={ff(t, "body")}>{c.sub}</text>
        </g>)}
      <text x={540} y={base - H / 2} textAnchor="middle" fontSize={120} fontWeight={900} fill={acc} opacity={pr(f, s2 - 10, s2 + 6) * (1 - pr(f, s2 + 30, s2 + 44))} fontFamily={ff(t, "display")}>{L.mult ?? "×10"}</text>
    </svg>;
  }

  if (v.kind === "grid") {
    const n = 20, cols = 5, sz = 150, gap = 26, x0 = 540 - (cols * sz + (cols - 1) * gap) / 2, y0 = 880;
    return <svg width={1080} height={1920} style={{position: "absolute", inset: 0, scale: String(cam), transformOrigin: "50% 70%"}}>
      <Caption text={L.caption ?? "20 TRADES / DAY"} />
      {Array.from({length: n}, (_, i) => {
        const a = pr(f, s1 - 20 + i * 3, s1 - 10 + i * 3);
        const bad = [2, 5, 7, 8, 11, 13, 14, 16, 17, 19].includes(i);
        const flip = pr(f, s2 + i * 2, s2 + 8 + i * 2);
        const x = x0 + (i % cols) * (sz + gap), y = y0 + Math.floor(i / cols) * (sz * 0.62 + gap);
        return <g key={i} opacity={a}>
          <rect x={x} y={y} width={sz} height={sz * 0.62} rx={14} fill={flip > 0.5 ? (bad ? loss : acc) : t.c.surface} stroke={t.c.grid} strokeWidth={2} />
          <text x={x + sz / 2} y={y + sz * 0.42} textAnchor="middle" fontSize={34} fontWeight={800} fill={flip > 0.5 ? t.c.onAccent : t.c.muted} fontFamily={ff(t, "body")}>{flip > 0.5 ? (bad ? "−" : "+") : i + 1}</text>
        </g>;
      })}
    </svg>;
  }

  if (v.kind === "split" && v.cs && v.cs2) {
    const A = makeScale(v.cs, {x: 90, y: 920, w: 420, h: 420}), B = makeScale(v.cs2, {x: 570, y: 920, w: 420, h: 420});
    const rev = 8 + (v.cs.length - 8) * pr(f, 0, s1);
    const closed = pr(f, s1 + 6, s1 + 20), adds = pr(f, s2 + 6, s2 + 40);
    const nB = v.cs2.length;
    return <svg width={1080} height={1920} style={{position: "absolute", inset: 0, scale: String(cam), transformOrigin: "50% 70%"}}>
      <text x={90} y={890} fontSize={30} fontWeight={800} letterSpacing="0.14em" fill={t.c.fg} fontFamily={ff(t, "body")}>TRADER A</text>
      <text x={570} y={890} fontSize={30} fontWeight={800} letterSpacing="0.14em" fill={t.c.fg} fontFamily={ff(t, "body")}>TRADER B</text>
      <line x1={540} x2={540} y1={870} y2={1360} stroke={t.c.grid} strokeWidth={2} />
      <Candles cs={v.cs} s={A} reveal={rev} focus={() => 1 - 0.55 * closed} />
      <Candles cs={v.cs2} s={B} reveal={8 + (nB - 8) * pr(f, 0, s2 + 40)} />
      <Tag x={150} y={1130} text={L.a ?? "CLOSED"} color={acc} p={closed} />
      {[0.35, 0.6, 0.85].map((q, k) => {const i = Math.floor(nB * q); return <Pin key={k} s={B} i={i} v={v.cs2![i].c} p={pr(f, s2 + 8 + k * 10, s2 + 18 + k * 10)} text="BUY" color={loss} above={false} />;})}
    </svg>;
  }

  // ---- chart family (chart / level / stop / fomo / rr)
  const cs = v.cs ?? [];
  if (!cs.length) return null;
  const inc = [v.entry, v.stop, v.target].filter((x): x is number => typeof x === "number");
  const slots = v.kind === "rr" ? cs.length + 8 : cs.length;
  const S = makeScale(cs, BOX, {include: inc, slots});
  const reveal = 6 + (cs.length - 6) * pr(f, 0, v.kind === "fomo" ? s2 + 20 : s1, (x) => x);
  const n = cs.length;
  return <svg width={1080} height={1920} style={{position: "absolute", inset: 0, scale: String(cam), transformOrigin: "50% 70%"}}>
    <Caption text={[v.symbol, v.tf].filter(Boolean).join(" · ")} />
    <Grid s={S} opacity={0.6} />
    {v.kind === "level" && v.zone && <Zone s={S} lo={v.zone[0]} hi={v.zone[1]} p={pr(f, s1, s1 + 20)} />}
    <Candles cs={cs} s={S} reveal={reveal} />
    {v.kind === "level" && v.zone && <Tag x={BOX.x + 10} y={S.y(v.zone[1]) - 44} text={L.zone ?? "SUPPORT"} color={acc} p={pr(f, s1 + 10, s1 + 24)} />}
    {v.kind === "stop" && v.entry !== undefined && v.stop !== undefined && <>
      <Level s={S} v={v.entry} p={pr(f, s1, s1 + 16)} color={t.c.fg} dashed from={Math.floor(n * 0.45)} />
      <Level s={S} v={v.stop} p={pr(f, s1 + 8, s1 + 24)} color={loss} from={Math.floor(n * 0.45)} />
      <Tag x={BOX.x + BOX.w - 200} y={S.y(v.entry) - 40} text={L.entry ?? "ENTRY"} color={t.c.fg} p={pr(f, s1 + 4, s1 + 16)} fill={false} />
      <Tag x={BOX.x + BOX.w - 260} y={S.y(v.stop) + 44} text={L.stop ?? "STOP-LOSS"} color={loss} p={pr(f, s1 + 12, s1 + 26)} />
    </>}
    {v.kind === "fomo" && v.peak !== undefined && <Pin s={S} i={v.peak} v={cs[v.peak].h} p={pr(f, s1, s1 + 14)} text={L.entry ?? "BUY"} color={loss} />}
    {v.kind === "rr" && v.entry !== undefined && v.stop !== undefined && v.target !== undefined && (() => {
      const x0 = S.x(n - 1) + S.cw, w = S.cw * 7;
      const ra = pr(f, s1, s1 + 18), rb = pr(f, s2, s2 + 24);
      return <g>
        <rect x={x0} y={S.y(v.entry)} width={w} height={(S.y(v.stop) - S.y(v.entry)) * ra} fill={loss} opacity={0.55} rx={6} />
        <rect x={x0} y={S.y(v.entry) - (S.y(v.entry) - S.y(v.target)) * rb} width={w} height={(S.y(v.entry) - S.y(v.target)) * rb} fill={acc} opacity={0.5} rx={6} />
        <line x1={x0 - 10} x2={x0 + w} y1={S.y(v.entry)} y2={S.y(v.entry)} stroke={t.c.fg} strokeWidth={3} />
        <Tag x={x0 - 230} y={S.y(v.stop) - 4} text={L.risk ?? "RISK 1"} color={loss} p={ra} />
        <Tag x={x0 - 260} y={S.y(v.target) + 30} text={L.reward ?? "REWARD 3"} color={acc} p={rb} />
      </g>;
    })()}
    {v.kind === "chart" && <PathArrow s={S} pts={[[n - 6, cs[n - 6].c], [n - 3, cs[n - 3].h], [n - 1, cs[n - 1].c]]} p={pr(f, s2, s2 + 30)} />}
  </svg>;
};
