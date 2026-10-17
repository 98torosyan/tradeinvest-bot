"""Caption builder: hook, lesson marker, summary, search keywords, question, CTA, <=5 hashtags."""
from . import bandit, settings

CTA = {"send": "📩 Ուղարկիր սա նրան, ով նոր է սկսում crypto-ում",
       "question": "👇 Գրիր պատասխանդ comment-ում",
       "save": "🔖 Պահիր այս դասը, որ չկորցնես"}
MODULE_TAG = {1: "#bitcoin", 2: "#cryptosecurity", 3: "#riskmanagement", 4: "#futures", 5: "#technicalanalysis",
              6: "#smartmoney", 7: "#smartmoney", 8: "#tradingpsychology", 9: "#tradingstrategy", 10: "#backtesting",
              11: "#macro"}


def marker(lesson, module_size):
    return f"Մոդուլ {lesson['module']} · Դաս {lesson['n']}/{module_size}"


def lesson_caption(lesson, module_size, state):
    arm = bandit.choose(state, "cta", list(CTA), avoid=state.get("last_cta"))
    state["last_cta"] = arm
    tags = ["#crypto", "#trading", "#կրիպտո", "#հայերեն", MODULE_TAG.get(lesson["module"], "#crypto")][: settings.MAX_HASHTAGS]
    lines = [lesson["hook"].replace("|", " "), f"{marker(lesson, module_size)} · {lesson['title']}", "",
             lesson["summary"], ""]
    if lesson.get("keywords"):
        lines += ["🔑 " + " · ".join(lesson["keywords"]), ""]
    lines += [lesson.get("question", ""), CTA[arm], "📚 Սկսիր առաջին դասից՝ հղումը bio-ում", "", " ".join(tags)]
    text = "\n".join(l for l in lines if l is not None).strip()
    return text[:2150], arm


SERIES_POOL = {1: ["#technicalanalysis", "#chartpatterns", "#priceaction", "#candlestick"],
               2: ["#tradingpsychology", "#tradingmindset", "#tradingtips", "#tradinglife"],
               3: ["#indicators", "#technicalanalysis", "#tradingview", "#tradingtools"],
               4: ["#cryptomarket", "#bitcoin", "#cryptotrading", "#btc"],
               5: ["#riskmanagement", "#moneymanagement", "#tradingstrategy", "#tradingtips"]}
HIT_CTA = {"send": "📩 Ուղարկիր ընկերոջդ, ով սա պետք է իմանա",
           "question": "👇 Ո՞րն է քո պատասխանը։ Գրիր comment-ում",
           "save": "🔖 Պահիր, որ չկորցնես"}
# the same call to action is shown on the Reel's last screen (top line, big line)
OUTRO_CTA = {"send": ("Ուղարկիր ընկերոջդ,", "ով սա պետք է իմանա"),
             "question": ("Ո՞րն է քո պատասխանը", "Գրիր comment-ում"),
             "save": ("Պահիր այս դասը,", "որ չկորցնես")}


def topic_tags(lesson):
    """5 hashtags: 2 fixed + 1 from the series pool (rotated) + up to 2 from the lesson's own English keywords."""
    tags = ["#թրեյդինգ", "#trading"]
    pool = SERIES_POOL.get(lesson.get("module"), ["#crypto"])
    seed = sum(map(ord, lesson.get("id", "")))
    tags.append(pool[seed % len(pool)])
    for kw in lesson.get("keywords", []):
        if kw.isascii():
            t = "#" + "".join(ch for ch in kw.lower() if ch.isalnum())
            if 4 <= len(t) <= 26 and t not in tags:
                tags.append(t)
        if len(tags) >= 4:
            break
    for extra in pool + ["#crypto", "#հայերեն"]:
        if len(tags) >= settings.MAX_HASHTAGS:
            break
        if extra not in tags:
            tags.append(extra)
    return tags[: settings.MAX_HASHTAGS]


def choose_cta(state):
    arm = bandit.choose(state, "cta", list(HIT_CTA), avoid=state.get("last_cta"))
    state["last_cta"] = arm
    return arm


def hit_caption(lesson, title_line, state, arm=None):
    arm = arm or choose_cta(state)
    lines = [lesson["hook"].replace("|", " "), title_line, "", lesson["summary"], ""]
    if lesson.get("keywords"):
        lines += ["🔑 " + " · ".join(lesson["keywords"]), ""]
    lines += [lesson.get("question", ""), HIT_CTA[arm], "🔔 Ամեն օր՝ նոր թրեյդինգ դաս @armtradeinvest",
              "⚠️ Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ", "", " ".join(topic_tags(lesson))]
    return "\n".join(l for l in lines if l is not None).strip()[:2150], arm
