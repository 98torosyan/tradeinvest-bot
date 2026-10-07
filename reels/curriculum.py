"""Course curriculum: loading, validation (prerequisites, schema) and ordering."""
import json
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "curriculum.json")
BEAT_KINDS = {"hero", "broll", "card", "compare", "checklist", "chart", "math"}


HITS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "hits.json")


def load():
    """The active content: standalone trading Reels (hits) or the old module course."""
    from . import settings
    path = HITS_PATH if getattr(settings, "CONTENT_MODE", "course") == "hits" else PATH
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def module_title(cur, m):
    return next(x["title"] for x in cur["modules"] if x["n"] == m)


def module_size(cur, m):
    return sum(1 for l in cur["lessons"] if l["module"] == m)


def words(lesson):
    n = 0
    for b in lesson.get("beats", []):
        for k in ("text", "title"):
            n += len(str(b.get(k, "")).split())
        for side in ("a", "b"):
            if side in b:
                n += len(" ".join(b[side]).split())
        n += len(" ".join(b.get("items", [])).split())
    n += len(lesson.get("hook", "").replace("|", " ").split()) + len(lesson.get("recap", "").replace("|", " ").split())
    return n


def validate(cur, max_words=90):
    """Returns a list of problems. Prerequisite rule: every term a scripted lesson
    uses must be introduced by an earlier lesson in course order."""
    errs, seen_ids, introduced = [], set(), set()
    for l in cur["lessons"]:
        lid = l.get("id")
        if lid in seen_ids:
            errs.append(f"{lid}: duplicate id")
        seen_ids.add(lid)
        if l.get("status") == "script":
            for u in l.get("uses", []):
                if u not in introduced:
                    errs.append(f"{lid}: uses '{u}' before it is introduced")
            if not l.get("hook") or not l.get("recap") or not l.get("beats"):
                errs.append(f"{lid}: hook/recap/beats missing")
            for b in l.get("beats", []):
                if b.get("kind") not in BEAT_KINDS:
                    errs.append(f"{lid}: unknown beat kind {b.get('kind')}")
            if words(l) > max_words:
                errs.append(f"{lid}: {words(l)} words (max {max_words})")
            q = l.get("quiz") or {}
            if len(q.get("options", [])) != 3 or q.get("a") not in (0, 1, 2):
                errs.append(f"{lid}: quiz must have 3 options")
        introduced.update(l.get("introduces", []))
    return errs


def next_lesson(cur, index):
    """(lesson, next_lesson_or_None) at course position `index`, or (None, None)."""
    ls = cur["lessons"]
    if index >= len(ls):
        return None, None
    return ls[index], (ls[index + 1] if index + 1 < len(ls) else None)


def scripted_left(cur, index):
    n = 0
    for l in cur["lessons"][index:]:
        if l.get("status") != "script":
            break
        n += 1
    return n
