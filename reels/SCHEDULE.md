# TradeInvest content system (Nov 2026)

All times Yerevan (UTC+4). Nothing is published in quiet hours (00:00–09:00); GitHub cron runs that start more than 2 h late are skipped and the exact Cloudflare slots catch the day's missing items up.

| When | Kind | What | Content source |
|---|---|---|---|
| 10:07 daily | `challenge` | «30 օր, 30 կանոն» Story (+ economic calendar on Mondays / event days) | `content/challenge30.json`, `econ.py` |
| 12:37 daily (Cloudflare) | `lesson` → `do_chart_lesson` (35 s «Իրական chart դաս» on real candles; short script = fallback) + catch-up challenge/market Story/quiz | Short Reel 7–20 s + Story | `content/shorts.json` (42 scripts, hook formulas) |
| 15:07 Mon/Wed/Fri | `carousel` | Educational carousel with recap slide | `content/carousels.json` (19) |
| 15:07 Tue/Thu/Sat/Sun | `poster` | Typographic poster | `content/posters.json` (30) |
| 16:07 daily | `fact` | Did-you-know / glossary / live number Story | `content/daily_facts.json` |
| 17:37 (Cloudflare) | `analysis` → catch-up | carousel/poster + fact + 1st news Story if GitHub missed them | — |
| 19:07 daily (Cloudflare) | `lesson` → `do_analysis` | Analysis Reel on real candles + Story | `analysis.py` |
| 21:37 (Cloudflare) | `lesson` → «Կրիպտո Հայաստանում» short (series ARM) + catch-up | weekly (Sun) + 2nd news Story + digest | — |
| 21:53 daily | `digest` | Owner's Telegram summary | `last_run.md` |
| Sun 17:07 | `weekly` | «Շաբաթը մեկ հայացքով» Reel | Binance + Yahoo daily closes |
| Sun 22:00 | report (watchdog) | Weekly Telegram report, hook-formula leaderboard | Graph API insights |
| 1st 12:07 | `monthly` | BTC month infographic (feed image) | Binance daily candles |
| hourly :23 | `alert` | BTC/ETH ≥ 5 % / 24 h Story (pre-checked in bash, max 1 per asset per 12 h) | Binance ticker |

Every caption passes `caption_lint.py` (≤ 5 hashtags, no emoji/hashtag first, no URLs). Image Stories are rendered as 8 s videos with mood music (`assets/music/moods/<tense|inspire|tech|energy|calm>`). YouTube Shorts cross-post activates when `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` secrets exist.

Site (GitHub Pages, rebuilt on every Reel run): `/` hub, `/start/` mini course + PDF, `/tools/` calculators.


## News 2.0 (Nov 2026)
8 outlets (Cointelegraph, CoinDesk, Decrypt, The Block, CryptoSlate, Cryptonews, Bitcoinist, U.Today), items ≤18 h old, grouped into stories; only stories reported by ≥2 independent outlets; every number checked against the sources. Up to NEWS_PER_DAY=4 Stories, ≥2 h apart: catch-ups at 12:37, 17:37, 19:07, 21:37 plus the GitHub news crons.
