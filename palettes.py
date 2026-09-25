"""Three rotating colour palettes per content type. Layout, fonts and
animation never change -- only colour -- so the brand stays recognisable."""

NEWS = [
    {"name": "midnight", "bg": "linear-gradient(170deg,#0B1834 0%,#07101F 55%,#050A15 100%)",
     "a": "#5B9BFF", "a2": "#7FE3F0", "txt": "#F2F6FC", "mut": "#93A3C4", "p": "#DDE6F5", "em": "#FFFFFF",
     "blob1": "rgba(70,120,255,.30)", "blob2": "rgba(90,220,240,.16)", "blob3": "rgba(120,90,255,.14)",
     "pt": "#9CC2FF", "grid": "rgba(140,170,255,.045)"},
    {"name": "teal", "bg": "linear-gradient(170deg,#0C2A2E 0%,#071A1D 55%,#041012 100%)",
     "a": "#2FD4B0", "a2": "#A6F7E4", "txt": "#EFFAF8", "mut": "#8FB3AE", "p": "#D7EEEA", "em": "#FFFFFF",
     "blob1": "rgba(47,212,176,.24)", "blob2": "rgba(80,170,255,.14)", "blob3": "rgba(155,245,224,.10)",
     "pt": "#9BF5E0", "grid": "rgba(150,245,225,.04)"},
    {"name": "graphite", "bg": "linear-gradient(170deg,#1B1830 0%,#110F20 55%,#0A0914 100%)",
     "a": "#9B8CFF", "a2": "#D4CCFF", "txt": "#F4F2FF", "mut": "#A19CC0", "p": "#E2DFF5", "em": "#FFFFFF",
     "blob1": "rgba(155,140,255,.26)", "blob2": "rgba(255,120,200,.10)", "blob3": "rgba(100,160,255,.12)",
     "pt": "#CFC6FF", "grid": "rgba(200,190,255,.04)"},
]
LESSON = [
    {"name": "amber", "bg": "linear-gradient(175deg,#2A1B10 0%,#1A110A 55%,#100A06 100%)",
     "a": "#F4B64A", "a2": "#FFD98A", "txt": "#FBF3E6", "mut": "#B9A68A", "p": "#EFE3D0", "em": "#FFD98A",
     "blob1": "rgba(244,182,74,.22)", "blob2": "rgba(242,112,95,.12)", "blob3": "rgba(255,217,138,.10)",
     "pt": "#FFD98A", "onacc": "#1A110A"},
    {"name": "forest", "bg": "linear-gradient(175deg,#16301F 0%,#0D1D14 55%,#08120C 100%)",
     "a": "#E8C766", "a2": "#F6E3A1", "txt": "#F2F7EE", "mut": "#A7B8A0", "p": "#E3EDDD", "em": "#F6E3A1",
     "blob1": "rgba(232,199,102,.18)", "blob2": "rgba(110,200,140,.14)", "blob3": "rgba(246,227,161,.08)",
     "pt": "#F6E3A1", "onacc": "#0D1D14"},
    {"name": "wine", "bg": "linear-gradient(175deg,#34131C 0%,#200B11 55%,#13060A 100%)",
     "a": "#FFB38A", "a2": "#FFD9C4", "txt": "#FCEFEA", "mut": "#C4A29A", "p": "#F3DFD8", "em": "#FFD9C4",
     "blob1": "rgba(255,179,138,.20)", "blob2": "rgba(255,110,140,.12)", "blob3": "rgba(255,214,191,.08)",
     "pt": "#FFD9C4", "onacc": "#200B11"},
]
COMMON = {"card": "rgba(255,255,255,.06)", "cardb": "rgba(255,255,255,.13)"}


def css_vars(p):
    v = dict(COMMON); v.update(p)
    return ";".join(f"--{k}:{val}" for k, val in v.items() if k != "name")
