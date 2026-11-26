"""Giveaway («Follow + like + նշիր 2 ընկեր → 1 անվճար անհատական դաս»): announce Reel, then a fair random draw.

Instagram rules for promotions: official rules in the caption, Instagram is released from responsibility and the
promotion is not sponsored by Instagram; no tagging of content that is not the user's. The API cannot see who follows
the page, so the draw picks a winner + 2 reserves and the OWNER checks the follow before announcing."""
import datetime as dt
import json
import os
import random
import re

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "giveaway.json")
MENTION = re.compile(r"@([A-Za-z0-9._]{2,30})")


def load():
    try:
        return json.load(open(SRC, encoding="utf-8"))
    except FileNotFoundError:
        return {}


def caption(g):
    end = (dt.date.fromisoformat(g["start"]) + dt.timedelta(days=g["days"])).strftime("%d.%m.%Y")
    return "\n".join([
        f"🎁 GIVEAWAY՝ {g['prize']}",
        "",
        "Ինչպես մասնակցել՝",
        "1️⃣ Հետևիր @armtradeinvest էջին",
        "2️⃣ Like արա այս Reel-ին",
        "3️⃣ Comment-ում նշիր 2 ընկերոջ (յուրաքանչյուր նոր comment՝ ևս մեկ հնարավորություն)",
        "",
        f"⏳ Ավարտ՝ {end}, 21:00։ Հաղթողին կընտրենք պատահականորեն և կհայտարարենք Story-ում։",
        "",
        "Կանոններ՝ մասնակցել կարող են 18 տարին լրացած անձինք։ Հաղթողը պետք է հետևի էջին։ "
        "Եթե հաղթողը 48 ժամում չպատասխանի, կընտրվի պահեստայինը։ Մրցանակը չի փոխանակվում գումարով։",
        "Այս մրցույթը որևէ կերպ կապված չէ Instagram-ի հետ, չի հովանավորվում և չի կառավարվում Instagram-ի կողմից։",
        "",
        "#giveaway #թրեյդինգ #trading #crypto #հայերեն #armtradeinvest",
    ])


def entries(comments, own, max_per_user=5):
    """One entry per comment that tags ≥2 other accounts (not ourselves, not the commenter), max 5 per user."""
    per, out = {}, []
    for c in comments:
        user = (c.get("username") or "").lower()
        if not user or user == own.lower():
            continue
        tags = {m.lower() for m in MENTION.findall(c.get("text") or "")} - {user, own.lower()}
        if len(tags) < 2 or per.get(user, 0) >= max_per_user:
            continue
        per[user] = per.get(user, 0) + 1
        out.append(user)
    return out


def draw(pool, seed):
    """Winner + 2 reserves (distinct users); the seed is logged so the draw can be repeated and checked."""
    rnd = random.Random(seed)
    order, seen = [], set()
    for u in rnd.sample(pool, len(pool)):
        if u not in seen:
            seen.add(u); order.append(u)
        if len(order) == 3:
            break
    return order
