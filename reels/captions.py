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
# a branded tag per series: tapping it opens every lesson of that series (binge-watching from one Reel)
SERIES_HUB = {1: "#armtrade_charts", 2: "#armtrade_mistakes", 3: "#armtrade_indicators",
              4: "#armtrade_market", 5: "#armtrade_risk"}
HIT_CTA = {"send": "📩 Ուղարկիր ընկերոջդ, ով սա պետք է իմանա",
           "question": "👇 Ո՞րն է քո պատասխանը։ Գրիր comment-ում",
           "save": "🔖 Պահիր, որ չկորցնես"}
# the same call to action is shown on the Reel's last screen (top line, big line)
OUTRO_CTA = {"send": ("Ուղարկիր ընկերոջդ,", "ով սա պետք է իմանա"),
             "question": ("Ո՞րն է քո պատասխանը", "Գրիր comment-ում"),
             "save": ("Պահիր այս դասը,", "որ չկորցնես")}


def topic_tags(lesson):
    """5 hashtags: 2 fixed + 1 from the series pool (rotated) + up to 2 from the lesson's own English keywords."""
    tags = ["#թրեյդինգ"]
    pool = SERIES_POOL.get(lesson.get("module"), ["#crypto"])
    seed = sum(map(ord, lesson.get("id", "")))
    tags.append(pool[seed % len(pool)])
    for kw in lesson.get("keywords", []):
        if kw.isascii():
            t = "#" + "".join(ch for ch in kw.lower() if ch.isalnum())
            if 4 <= len(t) <= 26 and t not in tags:
                tags.append(t)
        if len(tags) >= 3:
            break
    limit = settings.MAX_HASHTAGS - (1 if lesson.get("module") in SERIES_HUB else 0)   # the series tag is the 5th
    for extra in pool + ["#trading", "#crypto"]:
        if len(tags) >= limit:
            break
        if extra not in tags:
            tags.append(extra)
    return tags[:limit]


def content_cta(lesson):
    """Some lessons ask for one action by their nature: a checklist is worth saving, a quiz asks for an answer."""
    kinds = {b.get("kind") for b in (lesson or {}).get("beats", [])}
    if kinds & {"checklist", "steps"}:
        return "save"
    if "quiz" in kinds:
        return "question"
    return None


def choose_cta(state, lesson=None):
    arm = content_cta(lesson) or bandit.choose(state, "cta", list(HIT_CTA), avoid=state.get("last_cta"))
    state["last_cta"] = arm
    return arm


def hit_caption(lesson, title_line, state, arm=None):
    arm = arm or choose_cta(state, lesson)
    lines = [lesson["hook"].replace("|", " "), title_line, "", lesson["summary"], ""]
    if lesson.get("keywords"):
        lines += ["🔑 " + " · ".join(lesson["keywords"]), ""]
    hub = SERIES_HUB.get(lesson.get("module"))
    lines += [lesson.get("question", ""), HIT_CTA[arm]]
    if hub:
        lines.append(f"📚 Այս շարքի բոլոր դասերը՝ {hub}")
    lines += ["🔔 Ամեն օր՝ նոր թրեյդինգ դաս @armtradeinvest",
              "⚠️ Կրթական բովանդակություն է, ոչ թե ֆինանսական խորհուրդ", "", " ".join(topic_tags(lesson))]
    return "\n".join(l for l in lines if l is not None).strip()[:2150], arm
