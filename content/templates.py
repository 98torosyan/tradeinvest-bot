"""
Template pools for the daily content generator.
Nothing here invents facts -- every {placeholder} is filled from real,
fetched data in generate_plan.py. Rotating multiple variants per slot
is what keeps the page from feeling repetitive (brief rule #6/#10).
"""

HOOKS_UP = [
    "{sym}-ը հիմա ինչ-որ բան է ցույց տալիս... 👇",
    "{sym}-ը թռավ +{pct}%. Ահա ինչու 👇",
    "Եթե {sym} ունես, սա տես ☝️",
    "3 բան, որ պետք է իմանաս այսօր {sym}-ի մասին 👇",
    "Այս chart-ը շատ բան է ասում 📈",
]

HOOKS_DOWN = [
    "{sym}-ը նահանջեց {pct}%. Panic թե normal correction? 👇",
    "Ինչո՞ւ է {sym}-ը շարժվում հենց հիմա 👇",
    "Այս լուրը կարող է կարևոր լինել Crypto շուկայի համար",
    "{sym}-ը կարմիր է այսօր. ահա փաստերը, ոչ paniка 👇",
]

HOOKS_FLAT = [
    "{sym}-ը հանգիստ է այսօր... բայց ոչ ամեն ինչ 👇",
    "Շուկան սպասման մեջ է. ահա ինչու 👇",
    "3 բան, որ պետք է իմանաս այսօր 👇",
]

HOOKS_BREAKING = [
    "🚨 Breaking. {headline}",
    "Այս լուրը կարող է կարևոր լինել Crypto շուկայի համար 👇",
    "Հենց նոր. {headline}",
]

CTA_POOL_REEL = [
    "Save արա, որ հետևես, թե ինչ կլինի հաջորդը",
    "Save արա այս Reel-ը և share արա նրա հետ, ով հետևում է {sym}-ին",
    "Comment արա՝ ի՞նչ ես կարծում այս շարժման մասին",
]

CTA_POOL_POST = [
    "Comment արա՝ ի՞նչ ես կարծում, սա consolidation է, թե՞ նոր տենդենցի սկիզբ",
    "Save արա հետագայի համար և share արա ընկերոջդ հետ",
    "Ո՞ր գործոնն է քեզ ամենաշատը զարմացրել, գրի comment-ում",
]

DISCLAIMER = (
    "⚠️ Այս կոնտենտը կրում է տեղեկատվական բնույթ և հիմնված է իրական, "
    "հրապարակային տվյալների վրա։ Այն չի հանդիսանում ֆինանսական խորհրդատվություն "
    "կամ շահույթի երաշխիք։ Crypto-ն բարձր ռիսկային ակտիվ է — միշտ արեք "
    "սեփական հետազոտությունը (DYOR)։"
)

HASHTAG_CORE = ["#TradeInvest", "#Crypto", "#CryptoNews", "#Bitcoin", "#Blockchain"]
HASHTAG_MARKET = ["#CryptoMarket", "#BitcoinETF", "#CryptoAnalysis", "#TradingView", "#DigitalAssets"]
HASHTAG_MACRO = ["#FederalReserve", "#Inflation", "#CPI", "#Macro", "#FinancialMarkets", "#InterestRates"]

# --- Crypto Dictionary (Tuesday "Education" format) ------------------------
# One term per Tuesday, cycling through this list in order (deterministic by
# ISO week number), never repeating until the list wraps around.
CRYPTO_GLOSSARY = [
    ("RSI (Relative Strength Index)",
     "0-ից 100 ցուցանիշ, որ չափում է՝ գինը վերջին շրջանում ինչքան արագ ու ուժեղ է շարժվել։ >70 հաճախ կոչվում է «overbought», <30՝ «oversold»։"),
    ("MACD", "Երկու moving average-ի տարբերությունը ցույց տվող ինդիկատոր, որ օգտագործվում է trend-ի ուժն ու շրջադարձերը գնահատելու համար։"),
    ("Liquidity (իրացվելիություն)", "Որքան հեշտ կարող ես ակտիվը գնել/վաճառել՝ առանց գինը մեծապես շարժելու։ Բարձր liquidity = նեղ spread, կայուն գին։"),
    ("Support / Resistance", "Գնային մակարդակներ, որտեղ պատմականորեն գինը հաճախ կանգ է առել կամ շրջվել՝ Support-ը ներքևից, Resistance-ը վերևից։"),
    ("Market Cap", "Coin-ի ընթացիկ գնի և շրջանառության մեջ եղած ամբողջ քանակի արտադրյալը. ցույց է տալիս ընդհանուր «չափը», ոչ միայն գինը։"),
    ("Volume", "Որոշակի ժամանակահատվածում առևտրանված ընդհանուր քանակը։ Բարձր volume-ով շարժումները սովորաբար ավելի «հավաստի» են համարվում։"),
    ("Volatility (անկայունություն)", "Գնի տատանումների չափը ժամանակի ընթացքում։ Crypto-ն ավանդական ակտիվների համեմատ սովորաբար շատ ավելի volatile է։"),
    ("Bull / Bear Market", "Bull market՝ երկարաժամկետ աճի միտում, Bear market՝ երկարաժամկետ նվազման միտում։"),
    ("Stablecoin", "Crypto, որի արժեքը կապված է ֆիքսված ակտիվի (սովորաբար՝ USD) հետ՝ գնային կայունություն ապահովելու համար։"),
    ("DCA (Dollar-Cost Averaging)", "Ֆիքսված գումար ներդնել կանոնավոր ինտերվալներով՝ անկախ գնից, ռիսկը ժամանակի մեջ բաշխելու համար։"),
    ("Leverage", "Փոխառու կապիտալով պոզիցիայի չափը մեծացնել, ինչը մեծացնում է և՛ potential շահույթը, և՛ potential վնասը։"),
    ("Liquidation", "Երբ leveraged պոզիցիան ակամա փակվում է, քանի որ market-ը շարժվել է trader-ի դեմ և margin-ը սպառվել է։"),
]

# --- Meme / humor (Saturday format) -----------------------------------------
# Text-based meme concepts: {mood} filled with "up"/"down"/"flat" so the
# concept always matches today's real price direction.
MEME_IDEAS = {
    "up": [
        {"concept": "«Ես երբ վաճառել էի BTC-ն երեկ, հիմա նայում եմ chart-ին» — reaction-meme ֆորմատ",
         "visual": "Split panel meme. ձախում՝ տխուր stick-figure, աջում՝ կանաչ candlestick chart աճող"},
        {"concept": "«POV. դու HODL էիր անում, մինչդեռ բոլորը panic-sell էին անում» — հպարտության meme",
         "visual": "Confident character pose overlay կանաչ chart-ի ֆոնի վրա"},
    ],
    "down": [
        {"concept": "«Ես vs իմ պորտֆելը այսօր» — կատակային self-deprecating ֆորմատ",
         "visual": "Split panel. ձախում հանգիստ դեմք, աջում կարմիր candlestick chart նվազող"},
        {"concept": "«red day-ի ամենամեծ ստրատեգիան. close the app» — relatable հումոր",
         "visual": "Phone screen-ի mockup, կարմիր chart, character փակում է app-ը"},
    ],
    "flat": [
        {"concept": "«Երբ շուկան անում է ոչինչ, բայց դու refresh ես անում ամեն 5 վայրկյան» — relatable meme",
         "visual": "Character անվերջ refresh անող ձեռքով, հարթ/flat chart ֆոնին"},
    ],
}

STORY_TEMPLATES = [
    ("Teaser", "«Այսօրվա market recap-ը էջում 👀 սահիր վերև»"),
    ("Poll", "«{sym}-ի այսօրվա շարժումը՝ 🔴 Correction ա միայն, թե 🟡 Trend-ի փոփոխություն?»"),
    ("Quiz", "«Ինչքա՞ն է {sym}-ի գինը հիմա. A) ${low}  B) ${mid}  C) ${high}» (ճիշտ պատասխանը՝ հաջորդ story-ում)"),
    ("Chart", "{sym} 24-ժամյա candle-ի սքրինշոթ, տեքստ՝ «{sym} 24ժ movement 📊»"),
    ("Did you know?", "«Fear & Greed ինդեքսը այսօր {fng_value} է ({fng_label} գոտի)»"),
    ("This or that", "«Trading ոճ՝ 📈 Long-term hold, թե 📉 Short-term trade?»"),
    ("Question", "«Ի՞նչ թեմայի մասին ուզում ես, որ խոսենք վաղը?»"),
    ("Behind the scenes", "«TradeInvest-ի team-ը հենց հիմա վերլուծում է վաղվա market calendar-ը 👨‍💻»"),
    ("Prediction", "«Կանխատեսիր՝ {sym} մինչև շաբաթվա վերջ կլինի ավելի բարձր, թե ավելի ցածր ներկայիս գնից?»"),
    ("CTA", "«Ամբողջ վերլուծությունը արդեն feed-ում 👆 Գնա post/reel-ին»"),
]

# English versions of the same 10 Story slots, used for bilingual rotation
# (alternate Armenian/English) so international followers aren't left out.
STORY_TEMPLATES_EN = [
    ("Teaser", "\"Today's market recap is up 👀 swipe up\""),
    ("Poll", "\"{sym}'s move today: 🔴 Just a correction, or 🟡 a trend shift?\""),
    ("Quiz", "\"What's {sym}'s price right now? A) ${low}  B) ${mid}  C) ${high}\" (answer in the next story)"),
    ("Chart", "{sym} 24h candle screenshot, text: \"{sym} 24h movement 📊\""),
    ("Did you know?", "\"The Fear & Greed Index is at {fng_value} today ({fng_label} zone)\""),
    ("This or that", "\"Trading style: 📈 Long-term hold, or 📉 Short-term trade?\""),
    ("Question", "\"What topic do you want us to cover tomorrow?\""),
    ("Behind the scenes", "\"The TradeInvest team is analyzing tomorrow's market calendar right now 👨‍💻\""),
    ("Prediction", "\"Predict: will {sym} be higher or lower than now by the end of the week?\""),
    ("CTA", "\"Full breakdown is already in the feed 👆 check the post/reel\""),
]
