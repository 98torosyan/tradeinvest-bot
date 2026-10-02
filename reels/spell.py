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


def _known(w, wl):
    lw = w.lower()
    # whitelist entries are words or STEMS: Armenian inflects with suffixes (բլոկչեյն -> բլոկչեյնը, բլոկչեյնի)
    return lw in wl or any(len(x) >= 4 and lw.startswith(x) for x in wl)


def _dist1(a, b):
    """True if a and b differ by one edit (insert, delete or replace)."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b):
        a, b = b, a
    return any(a == b[:i] + b[i + 1:] for i in range(len(b)))


def check(text):
    """(typos, unknown): typos = words hunspell can correct with ONE edit (real misspellings like այսոր -> այսօր);
    unknown = other words missing from the dictionary (names, new terms) -- not treated as errors."""
    if not available():
        return [], []
    wl = _whitelist()
    ws = sorted({w for w in words(text) if len(w) > 1 and not _known(w, wl)})
    if not ws:
        return [], []
    r = subprocess.run(["hunspell", "-d", DICT, "-a"], input="\n".join(ws), capture_output=True, text=True)
    typos, unk = [], []
    for line in r.stdout.splitlines():
        if line.startswith("&"):                  # & word count offset: sugg1, sugg2, ...
            head, _, sugg = line.partition(":")
            word = head.split()[1]
            cands = [x.strip() for x in sugg.split(",")]
            (typos if any(_dist1(word.lower(), c.lower()) for c in cands) and not word[0].isupper() else unk).append(word)
        elif line.startswith("#"):                # no suggestion at all: a name or a new word
            unk.append(line.split()[1])
    return sorted(set(typos)), sorted(set(unk))


def unknown(text):
    """Likely misspellings only (kept for older callers)."""
    return check(text)[0]
