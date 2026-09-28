"""Pre-publish quality gate. Any error => the item is NOT published (Telegram alert).
Warnings are only logged."""
import os
import tempfile

from . import curriculum, settings

BANNED = ["երաշխավորված շահույթ", "երաշխավորում ենք", "100% շահույթ", "guaranteed", "risk-free", "անպայման կաճի",
          "անպայման կբարձրանա", "գնիր հիմա", "վաճառիր հիմա", "ֆինանսական խորհուրդ է"]
SAFE = {"x0": 40, "x1": 1040, "y0": 225, "y1": 1700}


def _text_of(lesson):
    parts = [lesson.get("hook", ""), lesson.get("recap", ""), lesson.get("summary", "")]
    for b in lesson.get("beats", []):
        parts += [str(b.get(k, "")) for k in ("text", "title")] + [" ".join(b.get("a", [])), " ".join(b.get("b", [])),
                                                                     " ".join(b.get("items", []))]
    return " ".join(parts).lower()


def pre_render(lesson, cur, published_ids):
    errs = []
    if lesson.get("status") != "script":
        errs.append(f"{lesson['id']}: script is not written yet")
        return errs
    if lesson["id"] in published_ids:
        errs.append(f"{lesson['id']}: already published")
    one = {"modules": cur["modules"], "lessons": [l for l in cur["lessons"] if l["id"] == lesson["id"]]}
    earlier = []
    for l in cur["lessons"]:
        if l["id"] == lesson["id"]:
            break
        earlier += l.get("introduces", [])
    for u in lesson.get("uses", []):
        if u not in earlier:
            errs.append(f"{lesson['id']}: prerequisite '{u}' is not taught earlier")
    errs += [e for e in curriculum.validate(one, settings.LESSON_MAX_WORDS) if "before it is introduced" not in e]
    t = _text_of(lesson)
    errs += [f"{lesson['id']}: banned phrase '{b}'" for b in BANNED if b.lower() in t]
    return errs


def layout(html, times):
    """Renders the overlay at the given times and checks that every visible text box stays in the safe area."""
    from playwright.sync_api import sync_playwright
    errs = []
    path = os.path.join(tempfile.mkdtemp(prefix="qa_"), "o.html")
    open(path, "w", encoding="utf-8").write(html)
    js = """(s)=>{const out=[];document.querySelectorAll('.hl,.chunk,.gcard,.cmp,.chk,.ptag,.nxt2').forEach(e=>{
      const st=getComputedStyle(e);let p=e,vis=true;while(p&&p!==document.body){const cs=getComputedStyle(p);
      if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity<0.05){vis=false;break}p=p.parentElement}
      if(!vis)return;const r=e.getBoundingClientRect();if(r.width<2)return;
      if(r.left<s.x0||r.right>s.x1||r.top<s.y0||r.bottom>s.y1||e.scrollWidth>e.clientWidth*1.08+6)
        out.push((e.className+': '+e.textContent).slice(0,60)+' @'+[r.left,r.top,r.right,r.bottom].map(Math.round))});return out}"""
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(f"file://{path}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        for t in times:
            pg.evaluate(f"seek({t})")
            for bad in pg.evaluate(js, SAFE):
                errs.append(f"layout t={t:.1f}s: {bad}")
        b.close()
    return errs


def post_render(lesson, result, caption):
    errs, warns = [], []
    lo, hi = settings.DURATION[lesson.get("type", "concept")]
    if not lo <= result["duration"] <= hi + 8:
        errs.append(f"duration {result['duration']:.1f}s outside {lo}-{hi}s")
    times = [a + d * 0.75 for _, a, d in result["beats"]]
    errs += layout(result["html"], times)
    if caption.count("#") > settings.MAX_HASHTAGS:
        errs.append("more than 5 hashtags")
    if len(caption) > 2200:
        errs.append("caption longer than 2200 characters")
    if result.get("graphic_share", 1) < 0.4:
        warns.append(f"motion-graphics share {result['graphic_share']:.0%} < 40%")
    return errs, warns
