"""Visual styles for trading Reels. Every Reel gets one style, rotated so that two Reels in a row
never look the same. A style changes colours, typography, how the hook appears, how captions animate,
how scenes change, how cards look, the backgrounds and the sound accents."""

STYLES = {
    # monospace labels, typewriter text, green-on-black, horizontal wipes
    "terminal": {"hero": "type", "cap": "type", "trans": "wipe", "card": "terminal",
                 "bg": ["tape", "candles", "depth"], "label": "TERMINAL",
                 "pal": {"name": "terminal", "bg": "linear-gradient(175deg,#06110B 0%,#040B07 60%,#020604 100%)",
                         "a": "#1FD67A", "a2": "#7CFFB2", "txt": "#E9FFF2", "mut": "#7FA893", "p": "#CFF5DF",
                         "em": "#7CFFB2", "blob1": "rgba(31,214,122,.18)", "blob2": "rgba(124,255,178,.08)",
                         "blob3": "rgba(31,214,122,.06)", "pt": "#7CFFB2", "onacc": "#03140A"}},
    # big serif headlines that rise out of a mask line by line, calm push transitions
    "editorial": {"hero": "mask", "cap": "rise", "trans": "push", "card": "editorial",
                  "bg": ["line", "candles", "plain"], "label": "EDITORIAL",
                  "pal": {"name": "editorial", "bg": "linear-gradient(175deg,#1C1610 0%,#120E0A 60%,#0A0806 100%)",
                          "a": "#E9B44C", "a2": "#FFD98A", "txt": "#FBF5EA", "mut": "#B8A88E", "p": "#EFE5D3",
                          "em": "#FFD98A", "blob1": "rgba(233,180,76,.18)", "blob2": "rgba(255,217,138,.08)",
                          "blob3": "rgba(233,180,76,.06)", "pt": "#FFD98A", "onacc": "#1A1208"}},
    # condensed glowing type, flickering neon, zoom transitions
    "neon": {"hero": "glow", "cap": "blur", "trans": "zoom", "card": "neon",
             "bg": ["candles", "depth", "line"], "label": "NEON",
             "pal": {"name": "neon", "bg": "linear-gradient(175deg,#12061F 0%,#0A0414 60%,#05020B 100%)",
                     "a": "#FF3CAC", "a2": "#4FE3FF", "txt": "#FBF0FF", "mut": "#B49BC8", "p": "#EADCF5",
                     "em": "#4FE3FF", "blob1": "rgba(255,60,172,.20)", "blob2": "rgba(79,227,255,.14)",
                     "blob3": "rgba(255,60,172,.08)", "pt": "#4FE3FF", "onacc": "#12061F"}},
    # frosted glass cards that tilt in, letters rising one by one, circular iris transitions
    "glass": {"hero": "chars", "cap": "pop", "trans": "iris", "card": "glass",
              "bg": ["heat", "line", "candles"], "label": "GLASS",
              "pal": {"name": "glass", "bg": "linear-gradient(175deg,#0B1030 0%,#070A1F 60%,#040612 100%)",
                      "a": "#7C6CFF", "a2": "#8FD3FF", "txt": "#F2F4FF", "mut": "#9AA3D1", "p": "#DDE3FF",
                      "em": "#8FD3FF", "blob1": "rgba(124,108,255,.30)", "blob2": "rgba(143,211,255,.18)",
                      "blob3": "rgba(255,120,200,.10)", "pt": "#8FD3FF", "onacc": "#070A1F"}},
    # paper cards, yellow highlighter on the active word, punchy slam headlines
    "marker": {"hero": "slam", "cap": "mark", "trans": "slide", "card": "paper",
               "bg": ["candles", "tape", "line"], "label": "MARKER",
               "pal": {"name": "marker", "bg": "linear-gradient(175deg,#141414 0%,#0C0C0C 60%,#060606 100%)",
                       "a": "#FFD400", "a2": "#FFE45C", "txt": "#FFFFFF", "mut": "#B5B5B5", "p": "#EDEDED",
                       "em": "#FFE45C", "blob1": "rgba(255,212,0,.16)", "blob2": "rgba(255,228,92,.08)",
                       "blob3": "rgba(255,212,0,.05)", "pt": "#FFE45C", "onacc": "#141100"}},
}
ORDER = ["neon", "editorial", "terminal", "glass", "marker"]


def pick(index):
    """Style for the n-th Reel of the catalog (rotation, so neighbours always differ)."""
    return ORDER[index % len(ORDER)]


def get(name):
    return STYLES.get(name) or STYLES["neon"]
