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
COMMON = {"card": "rgba(255,255,255,.06)", "cardb": "rgba(255,255,255,.13)", "onacc": "#0B1220"}


def css_vars(p):
    v = dict(COMMON); v.update(p)
    return ";".join(f"--{k}:{val}" for k, val in v.items() if k != "name")


def _mod(name, bg0, bg1, bg2, a, a2, txt, mut, p, blob):
    return {"name": name, "bg": f"linear-gradient(175deg,{bg0} 0%,{bg1} 55%,{bg2} 100%)", "a": a, "a2": a2,
            "txt": txt, "mut": mut, "p": p, "em": a2, "blob1": blob[0], "blob2": blob[1], "blob3": blob[2],
            "pt": a2, "onacc": bg1}


# one fixed colour per module (season) so the profile grid reads like a course library
MODULE = {
 1: _mod("m1-amber", "#2A1B10", "#1A110A", "#100A06", "#F4B64A", "#FFD98A", "#FBF3E6", "#B9A68A", "#EFE3D0",
         ("rgba(244,182,74,.22)", "rgba(242,112,95,.12)", "rgba(255,217,138,.10)")),
 2: _mod("m2-teal", "#0C2A2E", "#071A1D", "#041012", "#2FD4B0", "#A6F7E4", "#EFFAF8", "#8FB3AE", "#D7EEEA",
         ("rgba(47,212,176,.22)", "rgba(80,170,255,.12)", "rgba(166,247,228,.08)")),
 3: _mod("m3-coral", "#2E1214", "#1D0B0C", "#120607", "#FF7A6B", "#FFC2B8", "#FCEFEE", "#C9A19C", "#F3DEDB",
         ("rgba(255,122,107,.22)", "rgba(255,190,120,.10)", "rgba(255,194,184,.08)")),
 4: _mod("m4-blue", "#0B1834", "#07101F", "#050A15", "#5B9BFF", "#9CC2FF", "#F2F6FC", "#93A3C4", "#DDE6F5",
         ("rgba(70,120,255,.26)", "rgba(90,220,240,.12)", "rgba(120,90,255,.10)")),
 5: _mod("m5-green", "#0E2A1B", "#081A10", "#040F09", "#3DDC97", "#A8F0CB", "#EEFAF3", "#95B8A4", "#D8EFE2",
         ("rgba(61,220,151,.20)", "rgba(80,170,255,.10)", "rgba(168,240,203,.08)")),
 6: _mod("m6-violet", "#1B1830", "#110F20", "#0A0914", "#9B8CFF", "#D4CCFF", "#F4F2FF", "#A19CC0", "#E2DFF5",
         ("rgba(155,140,255,.24)", "rgba(255,120,200,.10)", "rgba(100,160,255,.10)")),
 7: _mod("m7-magenta", "#2A1027", "#1A0A18", "#10060F", "#E86BD6", "#F6B8EE", "#FCF0FA", "#C29BBB", "#F1DDEE",
         ("rgba(232,107,214,.22)", "rgba(140,120,255,.10)", "rgba(246,184,238,.08)")),
 8: _mod("m8-orange", "#2B180B", "#1B0F06", "#110903", "#FF9F43", "#FFD2A6", "#FDF3EA", "#C7A88C", "#F2E2D3",
         ("rgba(255,159,67,.22)", "rgba(255,110,110,.10)", "rgba(255,210,166,.08)")),
 9: _mod("m9-cyan", "#08202A", "#05141B", "#030C10", "#3CC8F0", "#A9E9FA", "#EEF9FD", "#92B3BE", "#D6EEF5",
         ("rgba(60,200,240,.22)", "rgba(80,120,255,.10)", "rgba(169,233,250,.08)")),
 10: _mod("m10-lime", "#1B230B", "#111707", "#0A0E04", "#B6E34A", "#E1F5A8", "#F7FBEC", "#AEB894", "#E7EFD2",
          ("rgba(182,227,74,.20)", "rgba(61,220,151,.10)", "rgba(225,245,168,.08)")),
 11: _mod("m11-gold", "#16301F", "#0D1D14", "#08120C", "#E8C766", "#F6E3A1", "#F2F7EE", "#A7B8A0", "#E3EDDD",
          ("rgba(232,199,102,.18)", "rgba(110,200,140,.12)", "rgba(246,227,161,.08)")),
}
