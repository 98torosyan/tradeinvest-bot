"""Last check on every caption before it goes to Instagram (rules from instagram-agent-skill/ig-caption, MIT):
- at most 5 hashtags (Instagram's limit since Dec 2025), kept on the last line;
- the first visible line never starts with an emoji or a hashtag;
- no URLs in the caption (not clickable) — the bio link is the way;
- 2 200 characters at most."""
import re

MAX_TAGS = 5
_EMOJI = re.compile("^[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍\\s]+")
_TAG = re.compile(r"#[^\s#]+")


def lint(caption):
    text = caption or ""
    tags = []
    for t in _TAG.findall(text):
        if t.lower() not in (x.lower() for x in tags):
            tags.append(t)
    body = _TAG.sub("", text)
    body = re.sub(r"https?://\S+", "", body)
    lines = [l.rstrip() for l in body.split("\n")]
    while lines and not lines[-1].strip():
        lines.pop()
    out, blank = [], False
    for l in lines:                                # collapse runs of empty lines left by removed hashtags
        if not l.strip():
            if not blank and out:
                out.append("")
            blank = True
        else:
            out.append(l); blank = False
    if out:
        out[0] = _EMOJI.sub("", out[0]).strip()
    res = "\n".join(out).strip()
    if tags:
        res += "\n\n" + " ".join(tags[:MAX_TAGS])
    return res[:2200]
