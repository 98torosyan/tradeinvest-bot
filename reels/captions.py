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
