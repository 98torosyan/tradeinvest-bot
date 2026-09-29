"""Armenian spell-check (hunspell + martakert/hyspell dictionary, CC0 + our whitelist).
Suffixes glued to Latin terms (Bitcoin-ը, ETF-ների) are not checked."""
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DICT = os.path.join(HERE, "assets", "dict", "hy")
WL = os.path.join(HERE, "content", "whitelist_hy.txt")
SPLIT = re.compile(r"[\s,.;:!?«»()\"'—–|/…\u0589\u055D]+")
ARM = re.compile(r"^[\u0531-\u0587]+$")


def available():
    return bool(shutil.which("hunspell")) and os.path.exists(DICT + ".dic")


def _whitelist():
    try:
        with open(WL, encoding="utf-8") as f:
            return {l.strip().lower() for l in f if l.strip() and not l.startswith("#")}
    except OSError:
        return set()


def words(text):
    out = []
    for tok in SPLIT.split(text or ""):
        if re.search(r"[A-Za-z0-9$%&@#]", tok):
            continue                      # Latin term with an Armenian suffix (Bitcoin-ը) or a number
        for part in tok.split("-"):       # ԱՄՆ-ի, ինչ-որ: check the parts
            part = re.sub(r"[\u055B\u055C\u055E\u055A]", "", part)
            if ARM.match(part):
                out.append(part)
    return out


def unknown(text):
    """Returns the list of unknown Armenian words (empty if all fine or checker unavailable)."""
    if not available():
        return []
    ws = sorted({w for w in words(text) if len(w) > 1})
    if not ws:
        return []
    r = subprocess.run(["hunspell", "-d", DICT, "-l"], input="\n".join(ws), capture_output=True, text=True)
    wl = _whitelist()
    return sorted({w for w in r.stdout.split() if w.lower() not in wl})
