# TradeInvest — ամենօրյա Instagram content bot

Ամեն առավոտ ինքնաշխատ՝

1. հավաքում է իրական crypto/macro տվյալներ (գներ, 7-օրյա chart, crypto լուրեր, Fear & Greed, Fed rate/CPI),
2. կառուցում է օրվա ամբողջ Instagram content plan-ը (Reel #1, Post/Carousel, Reel #2, 10 Story, Top-3 idea) հայերենով,
3. սարքում է իրական visual-ներ՝ dark/premium candlestick chart, carousel սլայդներ, 10 Story-նկար, և 2 վերտիկալ (1080×1920) Reel video՝ chart animation + text overlay + ձայնային narration-ով,
4. **ուղիղ ավտոմատ post է անում Instagram-ում** (feed Post/Carousel, 2 Reel, 10 Story, +Saturday meme) — ձեռքով ոչինչ սեղմել պետք չէ, ամեն օր ինքնաշխատ։ Telegram-ը լրիվ **ոչ պարտադիր** կողքի ալիք է. եթե Telegram-ի secrets-ը դատարկ ես թողնում, այն պարզապես բաց է թողնվում, pipeline-ը դրանից ոչնչով կախված չէ։

Ոչինչ չի հորինվում. ամեն թիվ/լուր, որ երևում է plan-ում, գալիս է իրական API-ից/RSS-ից. եթե տվյալը հասանելի չէ, այն պարզապես բաց է թողնվում։

## Ինչպես է աշխատում (pipeline)

```
main.py
 ├─ data/fetch_market.py   → CoinGecko (գներ, OHLC chart, no key)
 ├─ data/fetch_news.py     → CoinDesk/Cointelegraph RSS (no key)
 ├─ data/fetch_macro.py    → FRED API (Fed rate, CPI — ազատ key)
 ├─ content/generate_plan.py → օրվա ամբողջ plan-ը (template-based, real data-ով)
 ├─ visuals/charts.py + cards.py → chart PNG + carousel slide PNG-ներ
 ├─ video/frames.py        → 10 Story PNG-ներ
 ├─ video/reel_video.py    → 2 Reel .mp4 (chart animation + text + TTS ձայն)
 ├─ delivery/telegram_sender.py → ոչ պարտադիր. ուղարկում է ամեն ինչ Telegram bot-ով, եթե կարգավորված է
 └─ manifest.json          → ցուցակ, թե ինչ պիտի հրապարակվի Instagram-ում ինչ caption-ով

scripts/publish_to_instagram.py
 ├─ delivery/media_hosting.py       → GitHub Pages-ի public URL-ները (chart/slides/reels/stories)
 └─ delivery/instagram_publisher.py → Meta Graph API. Carousel post + 2 Reel + 10 Story

scripts/refresh_ig_token.py → ամեն 2 շաբաթը մեկ թարմացնում է access token-ը՝ որ երբեք չլրանա ժամկետը
```

GitHub Actions-ը (`.github/workflows/daily-content.yml`) այս ամբողջ pipeline-ը վազացնում է ամեն օր ինքնաշխատ՝ անվճար runner-ի վրա. **generate → GitHub Pages → Instagram** (Telegram-ը՝ եթե կարգավորած է, ոչ պարտադիր)։

## Շաբաթական rotation / bonus content

Ստանդարտ օրվա plan-ից բացի, պլանավորողն ինքն է որոշում՝ ամեն օր ինչ ֆորմատ սարքել (weekday-ի հիման վրա, deterministic, առանց կրկնության).

- **Երեքշաբթի** → **Crypto Dictionary** post. carousel՝ մեկ եզրույթ (`content/templates.py`-ի `CRYPTO_GLOSSARY`-ից, ISO week number-ով rotate), սահմանում, օրինակ, ու «save it» CTA։
- **Ուրբաթ** → **Weekly Recap** post (եթե CoinGecko-ից իրական top-mover տվյալ ստացվել է). շաբաթվա top 3 gainers/losers (իրական տոկոսներով), **+ BTC vs S&P 500 vs Gold** համեմատական chart (`visuals/charts.py`-ի `render_comparison_chart`, Stooq-ից free CSV, `data/fetch_traditional.py`)՝ որպես լրացուցիչ carousel-սլայդ։ Եթե ուրբաթ traditional-market տվյալը հասանելի չէ, pipeline-ը պարզապես վերադառնում է սովորական post-ին (ոչինչ չի հորինում)։
- **Շաբաթ** → **Meme/humor** bonus feed post՝ իրական օրվա ուղղությանը (up/down/flat) համապատասխան concept-ով (`MEME_IDEAS`), Telegram-ով ուղարկվում է և, եթե IG-ը կարգավորված է, հրապարակվում որպես առանձին feed image (`manifest["meme"]`)։
- **Բոլոր օրերին** → Story-ները **երկլեզու** են (Հայերեն/English փոփոխվող, index-ով)՝ որ միջազգային followers-ը նույնպես native-language story-ներ տեսնի, ոչ միայն փոխառված trading տերմիններ հայերեն նախադասությունների մեջ։

Bonus, դեռ չիրականացված (կարելի է հաջորդ քայլով ավելացնել). **performance feedback loop** (Instagram Graph API insights-ից իրական engagement-ը կարդալ ու օգտագործել հաջորդ օրերի ֆորմատն ընտրելիս) և **լավագույն post-ելու ժամի ինքնաշխատ որոշում** (`online_followers` lifetime insight metric-ից)։ Երկուսն էլ պահանջում են, որ IG account-ը արդեն մի քանի շաբաթ ակտիվ լինի, որ insights-ը իմաստալից տվյալ ունենա։

## Վիզուալ համակարգ ("premium terminal" ոճ)

Բոլոր visual-ները (carousel սլայդներ, Story-ներ, chart-երը, Reel-ի frame-երը) հիմա կիսում են մեկ ընդհանուր դիզայն-լեզու (`visuals/branding.py`), որ ամեն ինչ նույն "product"-ի տպավորություն է թողնում.

- **Custom logomark** (շրջան + 3 candlestick-bar)՝ պարզ brand-տեքստի փոխարեն, ամեն visual-ի վրա։
- **Ambient glow + fine grid texture** ֆոն, flat gradient-ի փոխարեն։
- **Glass-panel «hero» card** հիմնական թվի/տերմինի համար (առաջին carousel-սլայդում, Crypto Dictionary/Weekly Recap-ի վերնագրում)։
- **Bullish/Bearish chip** (▲/▼)՝ chart-երի, carousel-ի առաջին սլայդի ու Reel-ի hook-քարտի վրա, երբ 24ժ %-ը հայտնի է։
- **Live ticker strip** chart-երի ներքևում (BTC/ETH/SOL/XRP իրական 24ժ %-ով)։
- **Editorial "quote" սլայդներ** իրական headline-ների համար (մեջբերման նշան + աղբյուր)։
- **Breaking-news կարմիր chyron** միայն այն օրերին, երբ plan-ը իրապես breaking է (news feed-ից իրական headline-ով, երբեք սպեկուլյատիվ)։
- **Carousel swipe-progress indicator** (dash-երով, թե որքան մնաց)։
- **«Data source» watermark** ամեն visual-ի վրա (CoinGecko/alternative.me/FRED)՝ credibility-ի համար։
- **Reel-ի ենթագրերի sync** (`video/tts.py` + `video/reel_video.py`)՝ edge-tts-ի word-timing event-երով, եթե հասանելի են. ամեն script-տողի քարտը մնում է էկրանին ուղիղ այնքան, որքան այն իրականում ասվում է narration-ում, ոչ թե պարզապես հավասարաչափ բաժանված ընդհանուր տևողության վրա։ Սա (ինչպես TTS-ի ինքը) **չի ստուգվել ուղիղ** այս sandbox-ի network-սահմանափակման պատճառով, ուստի ունի ապահով fallback՝ եթե timing-ը հասանելի չէ կամ script-ի բառաքանակին չի համընկնում, pipeline-ը վերադառնում է հին, հավասարաչափ բաժանման timing-ին (նույն ինչ նախկինում)։

Երկու բան, որ իրապես **չի կարող ամբողջությամբ ավտոմատացվել** (Instagram-ի platform-ի սահմանափակում, ոչ այս կոդի).

- **Comment-ի pin անելը։** `scripts/publish_to_instagram.py`-ն ինքնաշխատ post է անում իրական տվյալների աղբյուրների comment ամեն carousel post-ի ու Reel #1-ի տակ (`delivery/instagram_publisher.py`-ի `post_sources_comment`), բայց public Graph API-ն pin անելու endpoint չունի։ Comment-ը երևում է, պարզապես pin արած չէ. եթե ուզես pin արած, դա 1 հպում է Instagram app-ում։
- **Highlight cover-ները։** Graph API-ն Profile Highlight-ներ ստեղծելու/կառավարելու endpoint ընդհանրապես չունի։ `python scripts/generate_highlight_covers.py`-ն սարքում է 5 պատրաստի, brand-ած cover-նկար (📊 Daily/📖 Learn/😄 Fun/❓ FAQ/📩 Contact) — մնում է միայն ամեն մեկը ձեռքով վերբեռնել (Highlight → Edit cover → choose from library), ~30 վայրկյան ընդհանուր։

## Կարևոր սահմանափակումներ (ազնվորեն ասված)

- **Video-ն «cinematic AI footage» չէ։** Ազատ/անվճար tool-երով հնարավոր է chart animation + brand-ած text card-եր + synthesized ձայն — մասնագիտական, բայց տվյալահեն ֆորմատ, ոչ թե Runway/HeyGen-ի տիպի AI-ստեղծված footage։ Եթե հետագայում ուզես cinematic broll, դա կպահանջի վճարովի AI video API և առանձին ինտեգրում։
- **Երաժշտությունը** (`video/music.py`) ամբողջովին սինթեզված է numpy-ով՝ ոչ մի ներբեռնված ֆայլ, ուստի copyright ռիսկ բացարձակապես չկա։ Narration-ի հետ միասին խաղում է ցածր ձայնով (duck), իսկ եթե TTS-ը ձախողվի, երաժշտությունը մենակ մնում է ավելի բարձր ձայնով, որ Reel-ը երբեք լիովին լուռ չլինի։
- **Ձայնային narration-ը հայերենով (TTS)՝ Microsoft Edge-ի անվճար voice-երով (`hy-AM-AnahitNeural`/`hy-AM-HaykNeural`)։** Այս project-ը կառուցվել է sandbox միջավայրում, որտեղ ինտերնետային access-ը սահմանափակված էր, ուստի այս կոնկրետ voice-երի աշխատանքը **չհաջողվեց ուղիղ ստուգել**։ Կոդը ունի ապահով fallback. եթե narration-ը ձախողվի (ցանկացած պատճառով), Reel-ը դեռ ամբողջությամբ սարքվում է առանց ձայնի (միայն chart + text overlay) փոխարենը crash անելու։ Առաջին իրական run-ից հետո (GitHub Actions-ում) կտեսնես՝ ձայնը եղավ, թե ոչ։
- **Macro տվյալները (Fed rate, CPI) պահանջում են անվճար FRED API key։** Առանց key-ի՝ pipeline-ը դրանք պարզապես բաց է թողնում (ոչինչ չի հորինում)։
- **Story-ների interactive stickers-ը (poll/quiz/question) ինքնաշխատ չեն ավելանում։** Սա Instagram-ի public API-ի սահմանափակումն է (ոչ այս կոդի)՝ auto-post-ը կարող է հրապարակել միայն plain նկար/video Story, առանց սեղմվող sticker-ի։ Sticker-ի տեքստը դեռ կա plan-ում, եթե ուզես ձեռքով ավելացնել։
- Crypto գները/լուրերը ազատ public API-ներից են (CoinGecko, RSS) — rate limit-երը ցածր trafiic-ի համար բավարար են, բայց very high frequency-ի դեպքում կարող են պահանջել վճարովի tier։
- Instagram-ի Content Publishing API-ն թույլ է տալիս մինչև ~25 հրապարակում/օր մեկ account-ի համար — մեր ծավալը (1 post + 2 reel + 10 story = 13/օր) հեշտությամբ տեղավորվում է սրա մեջ։

## Տեղական թեստավորում (առանց GitHub-ի)

```bash
cd tradeinvest-bot
pip install -r requirements.txt
python tests/test_pipeline_offline.py   # sample տվյալներով, առանց ցանցի պահանջի, ստուգում է ամբողջ pipeline-ը
```

Իրական տվյալներով լոկալ փորձարկելու համար՝

```bash
cp .env.example .env      # լրացրու IG_USER_ID/IG_ACCESS_TOKEN (Telegram-ը ոչ պարտադիր է)
export $(cat .env | xargs)
python main.py
```

## GitHub-ում տեղադրելը (Instagram-only, լրիվ ավտոմատ — ոչ մի ձեռքով post)

Ստորև՝ ուղիղ ամենակարճ ճանապարհը դեպի **ամեն ինչ ինքնաշխատ Instagram-ում**, առանց Telegram-ի։

1. Սարքիր նոր GitHub repo և push արա այս ամբողջ folder-ը։ **Repo-ն պարտադիր պիտի լինի public** (առանց այս՝ GitHub Pages-ը չի կարող media-ն հրապարակել, որ Instagram-ը fetch անի)։
2. Կատարիր ներքևի **«Instagram-ում ուղիղ auto-post»** բաժնի բոլոր 7 քայլերը (Business account, Meta app, access token, IG_USER_ID)։ Սա մեկ անգամյա setup է, միայն դու ես կարող անել (Meta-ի սեփական հաշիվդ է)։
3. Repo-ի **Settings → Secrets and variables → Actions → New repository secret** բաժնում ավելացրու **միայն** ինստագրամի համար պետք եղածները.
   - `IG_USER_ID`, `IG_ACCESS_TOKEN` — ստորև Քայլ 4-5-ից
   - `FB_APP_ID`, `FB_APP_SECRET`, `GH_PAT` — որ token-ի թարմացումն էլ ինքնաշխատ լինի, ձեռքով ոչինչ երբեք պետք չգա անել (`scripts/refresh_ig_token.py`-ի բացատրությունը ներքևում)
   - `FRED_API_KEY` — ոչ պարտադիր, բայց առանց դրա macro slide-երը կլինեն ավելի քիչ
   - **`TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — բաց թող, պետք չեն։** Կոդը ինքն ստուգում է, եթե դատարկ են, պարզապես բաց է թողնում Telegram-ի քայլերը, ոչինչ չի կոտրվում։
4. Repo Settings → **Pages** → Source՝ "Deploy from a branch" → Branch՝ `main`, folder՝ `/docs` → Save։ (Առաջին push-ից հետո՝ `docs/` folder-ը ինքնաշխատ ստեղծվում է pipeline-ի կողմից)։
5. **Actions** tab-ում հաստատիր, որ workflow-ները միացված են (default-ով միացված են)։
6. Ամեն օր ժամը 08:00 Երևանի ժամանակով (04:00 UTC) pipeline-ը ինքնաշխատ կաշխատի ու ուղիղ post կանի Instagram-ում (Post/Carousel, 2 Reel, 10 Story, ուրբաթ՝ +comparison chart, շաբաթ՝ +meme)։ Ցանկացած պահի կարող ես ձեռքով trigger անել՝ Actions → "TradeInvest daily content" → **Run workflow**։
7. Յուրաքանչյուր run-ի արդյունքները (նկարներ, video, plan.md) նաև պահվում են որպես **workflow artifact** 14 օր, backup-ի համար։

Սա ամբողջությամբ ավտոմատացնում է իրական **post**-երը (carousel, 2 reel, 10 story, meme)։ Ինստագրամի API-ի 2 շատ մանր, զուտ կոսմետիկ բան կա, որ Meta-ն ընդհանրապես չի թողնում API-ով անել (ոչ մի կոդ սա շրջանցել չի կարող). comment-ը **pin** անելը (comment-ն ինքը արդեն ինքնաշխատ գրվում է) և Highlight cover-ների վերբեռնումը (նկարներն ինքնաշխատ սարքվում են, պարզապես վերբեռնումը՝ ոչ)։ Սրանք **post չեն**, ուղղակի պրոֆիլի դեկորացիա են — ցանկության դեպքում 1 անգամ ձեռքով, տես ներքևի բաժինը։

Telegram-ը ուզածիդ դեպքում **լրացուցիչ** կարող ես միացնել (ոչ պարտադիր) — ուղղակի ավելացրու `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` secrets-ը, ոչինչ այլ փոփոխել պետք չէ։

## Instagram-ում ուղիղ auto-post (լրիվ ավտոմատ, մեկ անգամյա setup)

**Քայլ 1 — Instagram-ը դարձրու Business/Creator account**
Instagram app → Settings → Account type → Switch to Professional Account → Business (կամ Creator)։

**Քայլ 2 — կապիր Facebook Page-ի հետ**
Business/Creator account-ը պիտի կապված լինի Facebook Page-ի հետ (եթե չունես, ստեղծիր մեկը՝ անվճար է, 2 րոպե)։ Instagram Settings → Account → Linked accounts → Facebook։

**Քայլ 3 — Meta Developer App սարքիր**
Գնա [developers.facebook.com](https://developers.facebook.com) → My Apps → Create App → "Other" → "Business"։ App-ի Dashboard-ում ավելացրու **Instagram Graph API** և **Facebook Login for Business** product-երը։

**Քայլ 4 — access token ստացիր**
Meta-ի [Graph API Explorer](https://developers.facebook.com/tools/explorer/)-ում ընտրիր քո App-ը, User Token-ի փոխարեն ընտրիր "Get Page Access Token" (քո Page-ը), թույլտվություններից նշիր՝ `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`։ Ստացված token-ը երկարաձգիր (long-lived, ~60 օր)՝ [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)-ում "Extend Access Token" կոճակով, կամ այս հրամանով.
```bash
curl -s "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=<APP_ID>&client_secret=<APP_SECRET>&fb_exchange_token=<SHORT_LIVED_TOKEN>"
```

**Քայլ 5 — գտիր քո Instagram User ID-ն**
```bash
curl -s "https://graph.facebook.com/v21.0/me/accounts?access_token=<PAGE_TOKEN>"
# պատասխանից վերցրու page id-ն, հետո.
curl -s "https://graph.facebook.com/v21.0/<PAGE_ID>?fields=instagram_business_account&access_token=<PAGE_TOKEN>"
# սա կտա instagram_business_account.id -ը == IG_USER_ID
```

**Քայլ 6 — ավելացրու secrets-ը GitHub-ում**
- `IG_USER_ID` — Քայլ 5-ից
- `IG_ACCESS_TOKEN` — Քայլ 4-ից (long-lived token)
- `FB_APP_ID`, `FB_APP_SECRET` — token-ի ավտոմատ թարմացման համար (`scripts/refresh_ig_token.py`)
- `GH_PAT` — (ուժեղ խորհուրդ, ոչ պարտադիր) GitHub Personal Access Token՝ "repo" scope-ով, որ token-ի թարմացումը ինքն իրեն գրվի secrets-ում, զրո ձեռքով քայլ ընդմիշտ։ Առանց սրա՝ ամեն ~2 ամիսը մեկ նոր token-ը գրվում է այդ run-ի GitHub Actions summary-ում (Actions tab → այդ run-ը), + Telegram-ով եթե կարգավորած է, և դու մեկ անգամ ձեռքով տեղադրում ես secrets-ում։

**Քայլ 7 — միացրու GitHub Pages**
Repo Settings → Pages → Source՝ "Deploy from a branch" → Branch՝ `main`, folder՝ `/docs` → Save։ (Առաջին push-ից հետո՝ `docs/` folder-ը ինքնաշխատ ստեղծվում է pipeline-ի կողմից)։

Այսքանը։ Հաջորդ օրվա run-ից սկսած՝ pipeline-ը ինքնաշխատ push կանի media-ն Pages-ին և հրապարակի Instagram-ում՝ Post/Carousel, 2 Reel, 10 Story (Story-երը՝ առանց interactive sticker-ի, տես սահմանափակումների բաժինը)։ Telegram-ով նաև կստանաս publish-ի արդյունքի report (ինչը հաջողվեց, ինչը՝ ոչ)։

## Ինչպես կարգավորել/փոփոխել

- `config.py` — brand գույներ, հետևվող coin-երը, շաբաթվա rotation թեմաները
- `content/templates.py` — hook/CTA/hashtag pool-երը (ավելացրու ավելի շատ տարբերակներ՝ էլ ավելի քիչ կրկնվող դարձնելու համար)
- `visuals/cards.py` / `video/frames.py` — visual style-ը (գույներ, layout)

## Հաջորդ հնարավոր քայլեր

- Ուղիղ auto-post Instagram-ում (Meta Graph API-ով)
- LLM-ով ավելի «կենդանի»/տարբերվող տեքստեր (template-ների փոխարեն), եթե ցանկանաս միացնել Claude/OpenAI API key
- Cinematic AI video (Runway/HeyGen) fallback-ի փոխարեն, եթե բյուջե հատկացվի
