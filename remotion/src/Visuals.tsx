// Topic visuals for the short lesson Reels. Every chart visual is drawn from REAL candles passed in by
// reels/shorts.py (different asset + window each time), so no two Reels share a picture.
// Visual area: x 90–990, y 830–1450 (decorative below the text band; key labels stay above ~1250 when possible).
import React from "react";
import {Img, staticFile, useCurrentFrame} from "remotion";
import {useTheme, ff, pr} from "./lib/core";
import {Candles, Level, Zone, Pin, PathArrow, makeScale, Grid, OHLC} from "./lib/Chart";

export type VisualSpec = {
  kind: "chart" | "level" | "stop" | "fomo" | "rr" | "split" | "multiplier" | "grid" | "image";
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
      <text x={540} y={base - H / 2} textAnchor="middle" fontSize={120} fontWeight={900} fill={acc} opacity={pr(f, s2 - 10, s2 + 6) * (1 - pr(f, s2 + 30, s2 + 44))} fontFamily={ff(t, "display")}>×10</text>
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
