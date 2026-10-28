"""TradeInvest brand system v3 (design council, Oct 2026).
Ink / Paper grounds alternating in the grid, ONE accent (Signal amber), green/red only on chart data.
Logo «TI Rise»: T in the ground's text colour, the raised I in amber."""
import os
import re

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

INK, INK2, PAPER, PAPER2 = "#0B0B0C", "#16171A", "#F2EFE8", "#E6E1D6"
TXT_D, MUT_D = "#F4F2EE", "#A3A09A"          # on ink   (MUT 7.6:1)
TXT_L, MUT_L = "#0B0B0C", "#5C5850"          # on paper (MUT 6.4:1)
AMBER = "#FF8A00"                            # Signal amber: the only accent
UP, DOWN = "#22B573", "#E5484D"              # price data only
SERIES = {1: "ԳՐԱՖԻԿ", 2: "ՍԽԱԼՆԵՐ", 3: "ԻՆԴԻԿԱՏՈՐՆԵՐ", 4: "ՇՈՒԿԱ", 5: "ՌԻՍԿ"}


def ground(dark):
    """CSS custom properties for one ground."""
    if dark:
        return f"--bg:{INK};--bg2:{INK2};--txt:{TXT_D};--mut:{MUT_D};--rule:rgba(255,255,255,.14);--acc:{AMBER};--onacc:{INK}"
    return f"--bg:{PAPER};--bg2:{PAPER2};--txt:{TXT_L};--mut:{MUT_L};--rule:rgba(11,11,12,.16);--acc:{AMBER};--onacc:{INK}"


def logo(fg="currentColor", acc=AMBER, cls="ti"):
    """TI Rise mark (from the logo designer's SVG): T + a taller, raised I."""
    return (f'<svg class="{cls}" viewBox="0 -96 366 436" aria-hidden="true">'
            f'<rect x="0" y="0" width="252" height="78" rx="16" fill="{fg}"/>'
            f'<rect x="84" y="0" width="84" height="340" rx="16" fill="{fg}"/>'
            f'<rect x="282" y="-96" width="84" height="436" rx="16" fill="{acc}"/></svg>')


def font_css():
    """Variable Noto Sans Armenian (wdth 62.5-100, wght 100-900) + JetBrains Mono for digits/Latin terms only."""
    return (f"@font-face{{font-family:ArmV;src:url('file://{ASSETS}/ttf/NotoSansArmenian.ttf');font-weight:100 900;font-stretch:62.5% 100%}}"
            + "".join(f"@font-face{{font-family:Mono;font-weight:{w};src:url('file://{ASSETS}/fonts/jetbrains-mono-latin-{w}-normal.woff2')}}"
                      for w in (500, 700, 800)))


def nbsp(text):
    """Non-breaking spaces where Armenian lines must not break: inside 'stop loss', number+unit, before short last words."""
    t = re.sub(r"(?i)\bstop loss\b", "stop\u00a0loss", text)
    t = re.sub(r"(\d)\s+(%|R|x|մլն|մլրդ|\$)", "\\1\u00a0\\2", t)
    t = re.sub(r"\s+(\S{1,3})$", "\u00a0\\1", t)
    return t
