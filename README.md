# TradeInvest - Instagram Reels bot

Automatic Armenian crypto Reels for @armtradeinvest.

- `reels/` - the whole system: lessons, news (Gemini), design, music, rendering
- `reels/lessons.json` - lesson bank
- `reels/assets/music/news`, `reels/assets/music/lesson` - background music
- `delivery/` - Instagram and Telegram publishing
- `.github/workflows/reels.yml` - schedule (5 lessons + 3 news per day)
- `.github/workflows/refresh-token.yml` - keeps the Instagram token alive
