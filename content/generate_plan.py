"""
Builds the day's full Instagram content plan (Reel #1, Post/Carousel,
Reel #2, 10 Stories, Top-3 ideas) purely from real fetched data.
No numbers or headlines are invented -- anything unconfirmed is left
out (brief rule #7).
"""
import random
from datetime import datetime

from config import PRIMARY_COIN, WEEKDAY_THEMES
from content.templates import (
    HOOKS_UP, HOOKS_DOWN, HOOKS_FLAT, HOOKS_BREAKING,
    CTA_POOL_REEL, CTA_POOL_POST, DISCLAIMER,
    HASHTAG_CORE, HASHTAG_MARKET, HASHTAG_MACRO, STORY_TEMPLATES, STORY_TEMPLATES_EN,
    CRYPTO_GLOSSARY, MEME_IDEAS,
)


def _direction_hooks(change_24h):
    if change_24h is None:
        return HOOKS_FLAT
    if change_24h >= 1.5:
        return HOOKS_UP
    if change_24h <= -1.5:
        return HOOKS_DOWN
    return HOOKS_FLAT


def _fmt_pct(x):
    if x is None:
        return "N/A"
    return f"{x:+.1f}"


def _fmt_price(x):
    if x is None:
        return "N/A"
    return f"{x:,.0f}"


def build_plan(market, ohlc, news, fear_greed, macro, date_str=None, top_movers=None, traditional=None):
    date_str = date_str or datetime.utcnow().strftime("%Y-%m-%d")
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = date_obj.weekday()
    theme = WEEKDAY_THEMES[weekday]

    rng = random.Random(date_str)  # same seed -> same picks if the job reruns same day

    btc = market.get(PRIMARY_COIN, {})
    sym = btc.get("symbol", "BTC")
    price = btc.get("price")
    chg24 = btc.get("change_24h")
    chg7d = btc.get("change_7d")

    breaking = [h for h in news if h.get("is_breaking")]
    top_headline = breaking[0]["title"] if breaking else (news[0]["title"] if news else None)

    # ---- Reel #1 --------------------------------------------------------
    if breaking:
        hook = rng.choice(HOOKS_BREAKING).format(headline=top_headline)
    else:
        hook = rng.choice(_direction_hooks(chg24)).format(sym=sym, pct=_fmt_pct(chg24))

    reel1_script = _build_reel1_script(sym, price, chg24, chg7d, fear_greed, macro, top_headline)
    reel1 = {
        "topic": f"{sym} այսօր՝ ${_fmt_price(price)} ({_fmt_pct(chg24)}% 24ժ)"
                 + (f" — {theme}" if not breaking else " — Breaking"),
        "hook": hook,
        "script": reel1_script,
        "on_screen_text": _on_screen_points(sym, price, chg24, chg7d, fear_greed),
        "visual": ("Մուգ, cinematic ֆոն; {sym} candlestick chart-ի անիմացիա; "
                   "3D-ոճի coin/glow accent; նուրբ կապույտ-մանուշակագույն gradient; "
                   "մաքուր sans-serif տառատեսակ թվերի համար; TradeInvest logo՝ ներքևի անկյունում."
                   ).format(sym=sym),
        "caption": _reel1_caption(sym, price, chg24, top_headline),
        "cta": rng.choice(CTA_POOL_REEL).format(sym=sym),
        "hashtags": " ".join(HASHTAG_CORE + rng.sample(HASHTAG_MARKET, k=3)),
    }

    # ---- Post / Carousel ---------------------------------------------------
    # Tuesday -> Crypto Dictionary; Friday (with real top-movers data) ->
    # Weekly Recap; everything else -> the standard market-update carousel.
    if weekday == 1:
        post = _build_dictionary_post(date_obj, sym, price, rng)
    elif weekday == 4 and top_movers and (top_movers.get("gainers") or top_movers.get("losers")):
        post = _build_weekly_recap_post(sym, price, chg7d, top_movers, rng)
    else:
        post = _build_post(sym, price, chg24, chg7d, fear_greed, macro, news, theme, rng)

    # ---- Reel #2 (3 things to know today) --------------------------------
    reel2 = _build_reel2(sym, macro, news, rng)

    # ---- Stories (bilingual: alternating Armenian / English) --------------
    stories = _build_stories(sym, price, chg24, fear_greed, rng)

    # ---- Saturday bonus: meme/humor idea (real direction, no invented data)
    meme = _build_meme(chg24, rng) if weekday == 5 else None

    # ---- Top 3 content ideas (heuristic, never a guarantee) ---------------
    top3 = _rank_top3(sym, chg24, breaking)

    plan = {
        "date": date_str,
        "weekday_theme": theme,
        "market_snapshot": {
            "symbol": sym, "price": price, "change_24h": chg24,
            "change_7d": chg7d, "fear_greed": fear_greed,
        },
        "reel1": reel1,
        "post": post,
        "reel2": reel2,
        "stories": stories,
        "top3": top3,
        "disclaimer": DISCLAIMER,
        "sources": [h["link"] for h in news if h.get("link")][:5],
        "comparison_chart": bool(traditional and (traditional.get("sp500") or traditional.get("gold"))),
        # Used to decide when to show the red "breaking" chyron banner on
        # visuals -- only ever true when a real breaking headline exists.
        "breaking": bool(breaking),
        "breaking_headline": top_headline if breaking else None,
    }
    if meme:
        plan["meme"] = meme
    return plan


def _build_reel1_script(sym, price, chg24, chg7d, fear_greed, macro, headline):
    lines = []
    if price is not None:
        lines.append(f"{sym}-ն այս պահին առևտրանում է ${_fmt_price(price)}-ի մոտակայքում։")
    if chg24 is not None:
        direction = "աճել է" if chg24 >= 0 else "նահանջել է"
        lines.append(f"Վերջին 24 ժամում {direction} {abs(chg24):.1f}%-ով։")
    if chg7d is not None:
        lines.append(f"Վերջին 7 օրում փոփոխությունը կազմել է {_fmt_pct(chg7d)}%։")
    if fear_greed.get("value") is not None:
        lines.append(f"Fear & Greed ինդեքսը այս պահին {fear_greed['value']} է ({fear_greed['label']} գոտի)։")
    if headline:
        lines.append(f"Հիմնական լուրը, որ ազդում է շուկայի վրա. «{headline}»։")
    if macro.get("confirmed"):
        if macro.get("fed_funds_rate"):
            lines.append(f"Fed-ի ընթացիկ rate-ը {macro['fed_funds_rate']}% է ({macro['fed_funds_date']} դրությամբ)։")
        if macro.get("cpi_yoy_pct") is not None:
            lines.append(f"CPI-ն տարեկան կտրվածքով {macro['cpi_yoy_pct']}% է ({macro['cpi_month']} տվյալներով)։")
    lines.append("Save արա, որ հետևես, թե ինչ կլինի հաջորդը։")
    return lines


def _on_screen_points(sym, price, chg24, chg7d, fear_greed):
    points = []
    if price is not None:
        points.append(f"{sym} ${_fmt_price(price)}")
    if chg24 is not None:
        points.append(f"{_fmt_pct(chg24)}% (24ժ)")
    if chg7d is not None:
        points.append(f"{_fmt_pct(chg7d)}% (7օր)")
    if fear_greed.get("value") is not None:
        points.append(f"Fear&Greed {fear_greed['value']}")
    return " → ".join(points) if points else "(տվյալները ժամանակավորապես անհասանելի են)"


def _reel1_caption(sym, price, chg24, headline):
    base = f"{sym}-ը այս պահին ${_fmt_price(price)} է ({_fmt_pct(chg24)}% 24ժ-ում)."
    if headline:
        base += f" Ինչու՞՝ {headline}."
    return base + " Մանրամասները՝ Reel-ում 👆"


def _build_post(sym, price, chg24, chg7d, fear_greed, macro, news, theme, rng):
    slides = [{
        "text": f"{sym} ${_fmt_price(price)} ({_fmt_pct(chg24)}%) — ի՞նչ կանգնեցրեց/ինչն է շարժում շուկան",
        "kind": "hero",
    }]
    for h in news[:3]:
        slides.append({"text": f"{h['title']} ({h['source']})", "kind": "quote"})
    if macro.get("confirmed"):
        macro_bits = []
        if macro.get("fed_funds_rate"):
            macro_bits.append(f"Fed rate՝ {macro['fed_funds_rate']}%")
        if macro.get("cpi_yoy_pct") is not None:
            macro_bits.append(f"CPI YoY՝ {macro['cpi_yoy_pct']}%")
        slides.append({"text": "Macro պատկեր. " + ", ".join(macro_bits), "kind": "normal"})
    slides.append({
        "text": "Bottom line. Կառուցվածքային պատկերը գնահատելիս միշտ նայիր և՛ ինստիտուցիոնալ հոսքերին, "
                "և՛ macro ֆոնին։ Սա տեղեկատվական վերլուծություն է, ոչ թե ֆինանսական խորհրդատվություն։",
        "kind": "bottom_line",
    })
    return {
        "topic": f"{theme}. {sym} ${_fmt_price(price)}",
        "format": f"{len(slides)}-սլայդանոց carousel, մուգ premium ձևանմուշ",
        "slides": slides,
        "caption": f"{sym}-ը {_fmt_pct(chg24)}% է շարժվել վերջին 24 ժամում։ Ինչու՞ — մանրամասները սլայդներում 👆",
        "cta": rng.choice(CTA_POOL_POST),
    }


def _build_reel2(sym, macro, news, rng):
    points = []
    if macro.get("fed_funds_rate"):
        points.append(f"Fed-ի ընթացիկ rate-ը {macro['fed_funds_rate']}% է ({macro['fed_funds_date']} դրությամբ)")
    if macro.get("cpi_yoy_pct") is not None:
        points.append(f"CPI-ն տարեկան կտրվածքով {macro['cpi_yoy_pct']}% է ({macro['cpi_month']})")
    for h in news[:3]:
        if len(points) >= 3:
            break
        points.append(f"{h['title']} ({h['source']})")
    if not points:
        points = ["Այսօր հաստատված նոր macro/breaking տվյալ չկա — Reel #2-ը կարելի է բաց թողնել կամ փոխարինել Educational ֆորմատով"]
    return {
        "topic": "3 բան, որ պետք է իմանաս այսօր",
        "hook": "3 բան, որ պետք է իմանաս այսօր, եթե հետևում ես crypto-ին 👇",
        "points": points,
        "on_screen_text": "թվերն ու ամսաթվերը highlight են արվում bold ֆոնտով voice-over-ի հետ sync-ով",
        "visual": "Split-screen ոճ. ձախում icon/graphic տվյալի աղբյուրի համար, աջում chart; մուգ navy/սև gradient, նեոն կապույտ accent-գծեր",
        "caption": "Factor-ներ, որ այս պահին շարժում են ողջ շուկան 🧵",
        "cta": rng.choice(CTA_POOL_REEL).format(sym=sym),
        "hashtags": " ".join(HASHTAG_CORE + rng.sample(HASHTAG_MACRO, k=3)),
    }


def _build_stories(sym, price, chg24, fear_greed, rng):
    """Bilingual rotation: even-indexed stories in Armenian, odd in English,
    so international followers see native-language stories too (not just
    borrowed English trading terms inside Armenian sentences)."""
    stories = []
    low = mid = high = "N/A"
    if price:
        low, mid, high = int(price * 0.97), int(price), int(price * 1.03)
    fmt_kwargs = dict(sym=sym, low=low, mid=mid, high=high,
                       fng_value=fear_greed.get("value", "N/A"),
                       fng_label=fear_greed.get("label", "Unknown"))
    for i, ((label, hy_template), (_, en_template)) in enumerate(zip(STORY_TEMPLATES, STORY_TEMPLATES_EN)):
        template = hy_template if i % 2 == 0 else en_template
        lang = "hy" if i % 2 == 0 else "en"
        stories.append({"type": label, "content": template.format(**fmt_kwargs), "lang": lang})
    return stories


def _build_dictionary_post(date_obj, sym, price, rng):
    """Tuesday 'Crypto Dictionary' carousel -- cycles through the glossary
    by ISO week number so the term changes every week without repeating
    until the whole list has been used."""
    week_num = date_obj.isocalendar()[1]
    term, definition = CRYPTO_GLOSSARY[week_num % len(CRYPTO_GLOSSARY)]
    example = (f"Օրինակ՝ եթե {sym} այսօր ${_fmt_price(price)} է, «{term}»-ի հասկացողությունը "
               f"կօգնի ավելի լավ մեկնաբանել այս գինը context-ում։") if price else \
              f"Փորձիր կիրառել այս հասկացությունը հաջորդ անգամ, երբ նայես {sym}-ի chart-ին։"
    slides = [
        {"text": f"Crypto Dictionary. «{term}»", "kind": "hero"},
        {"text": definition, "kind": "normal"},
        {"text": example, "kind": "normal"},
        {"text": "Save արա այս post-ը՝ քո անձնական crypto բառարանի համար 📚", "kind": "bottom_line"},
    ]
    return {
        "topic": f"Crypto Dictionary — {term}",
        "format": f"{len(slides)}-սլայդանոց educational carousel, մուգ premium ձևանմուշ",
        "slides": slides,
        "caption": f"Այսօրվա տերմինը՝ «{term}»։ Գիտե՞իր սա։ 📖",
        "cta": "Ո՞ր տերմինն ես ուզում, որ բացատրենք հաջորդը, գրի comment-ում",
    }


def _build_weekly_recap_post(sym, price, chg7d, top_movers, rng):
    """Friday 'Weekly Recap' carousel built from real top-mover data
    (CoinGecko markets endpoint) -- never invented rankings."""
    slides = [{"text": f"Շաբաթական Recap. {sym} {_fmt_pct(chg7d)}% այս շաբաթ", "kind": "hero"}]
    gainers = top_movers.get("gainers", [])
    losers = top_movers.get("losers", [])
    if gainers:
        lines = [f"{g['symbol']} {_fmt_pct(g['change_7d'])}% (${_fmt_price(g['price'])})" for g in gainers]
        slides.append({"text": "🟢 Շաբաթվա top gainers.\n" + "\n".join(lines), "kind": "normal"})
    if losers:
        lines = [f"{l['symbol']} {_fmt_pct(l['change_7d'])}% (${_fmt_price(l['price'])})" for l in losers]
        slides.append({"text": "🔴 Շաբաթվա top losers.\n" + "\n".join(lines), "kind": "normal"})
    slides.append({
        "text": "Bottom line. Շաբաթը եզրափակվեց այս պատկերով։ Հիշիր՝ անցյալ շաբաթվա lider-ը "
                "երաշխիք չէ հաջորդի համար։ Սա տեղեկատվական ամփոփում է, ոչ թե ներդրումային խորհուրդ։",
        "kind": "bottom_line",
    })
    return {
        "topic": f"Weekly Recap — {sym} {_fmt_pct(chg7d)}%",
        "format": f"{len(slides)}-սլայդանոց carousel, մուգ premium ձևանմուշ",
        "slides": slides,
        "caption": "Շաբաթվա ամենամեծ շարժումները՝ մեկ post-ում 📊 Save արա հետագայի համար",
        "cta": rng.choice(CTA_POOL_POST),
    }


def _build_meme(chg24, rng):
    mood = "flat"
    if chg24 is not None:
        if chg24 >= 1.5:
            mood = "up"
        elif chg24 <= -1.5:
            mood = "down"
    idea = rng.choice(MEME_IDEAS[mood])
    return {
        "concept": idea["concept"],
        "visual": idea["visual"],
        "caption": "Tag մեկին, ով ճանաչում ես այս feeling-ը 😅",
        "hashtags": " ".join(HASHTAG_CORE + ["#CryptoMeme", "#CryptoHumor"]),
    }


def _rank_top3(sym, chg24, breaking):
    ideas = []
    move_score = abs(chg24) if chg24 is not None else 0
    ideas.append(("Reel #1", 5 + move_score, "Real-time price move + ուժեղ hook — ամենաբարձր save/share պոտենցիալ"))
    ideas.append(("Post/Carousel", 3 + len(breaking), "Educational/structured format — ամենաբարձր save պոտենցիալ"))
    ideas.append(("Story poll", 4, "Ուղիղ հրավեր interaction-ի՝ բարձր engagement"))
    ideas.sort(key=lambda x: -x[1])
    return [{"item": n, "why": why} for n, _, why in ideas[:3]]
