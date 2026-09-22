"""
Renders the plan dict into the exact text layout the brief asked for
(DATE / REEL #1 / POST / REEL #2 / STORIES / TOP 3 CONTENT IDEAS),
so the human-readable output matches what was originally requested.
"""


def render(plan):
    p = plan
    lines = [f"DATE: {p['date']}  ({p['weekday_theme']})", ""]

    r1 = p["reel1"]
    lines += [
        "REEL #1", f"Topic: {r1['topic']}", f"Hook: {r1['hook']}",
        "Script:",
    ] + [f"  {i+1}. {s}" for i, s in enumerate(r1["script"])] + [
        f"On-screen text: {r1['on_screen_text']}",
        f"Visual: {r1['visual']}",
        f"Caption: {r1['caption']}",
        f"CTA: {r1['cta']}",
        f"Hashtags: {r1['hashtags']}",
        "",
    ]

    post = p["post"]
    lines += ["POST", f"Topic: {post['topic']}", f"Format: {post['format']}"]
    for i, slide in enumerate(post["slides"], start=1):
        text = slide["text"] if isinstance(slide, dict) else slide
        lines.append(f"Slide {i}: {text}")
    if p.get("comparison_chart"):
        lines.append("Extra slide: BTC vs S&P 500 vs Gold — weekly comparison chart (real data)")
    lines += [f"Caption: {post['caption']}", f"CTA: {post['cta']}", ""]

    r2 = p["reel2"]
    lines += ["REEL #2", f"Topic: {r2['topic']}", f"Hook: {r2['hook']}"]
    for i, pt in enumerate(r2["points"], start=1):
        lines.append(f"  {i}. {pt}")
    lines += [
        f"On-screen text: {r2['on_screen_text']}",
        f"Visual: {r2['visual']}",
        f"Caption: {r2['caption']}",
        f"CTA: {r2['cta']}",
        f"Hashtags: {r2['hashtags']}",
        "",
    ]

    lines.append("STORIES")
    for i, st in enumerate(p["stories"], start=1):
        lang_tag = st.get("lang", "hy").upper()
        lines.append(f"Story {i} ({st['type']}, {lang_tag}): {st['content']}")
    lines.append("")

    if p.get("meme"):
        m = p["meme"]
        lines += [
            "MEME OF THE DAY",
            f"Concept: {m['concept']}",
            f"Visual: {m['visual']}",
            f"Caption: {m['caption']}",
            f"Hashtags: {m['hashtags']}",
            "",
        ]

    lines.append("TOP 3 CONTENT IDEAS")
    for i, idea in enumerate(p["top3"], start=1):
        lines.append(f"{i}. {idea['item']} — {idea['why']}")
    lines.append("")

    lines.append(p["disclaimer"])
    if p.get("sources"):
        lines.append("")
        lines.append("Sources:")
        lines += [f"- {s}" for s in p["sources"]]

    return "\n".join(lines)
