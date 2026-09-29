"""All tunable numbers of TradeInvest v1.0 in one place."""
TZ = "Asia/Yerevan"
KEEP_DAYS = 3                    # media kept on the history-less `media` branch
MEDIA_BRANCH = "media"
TEASER_HOURS = {12, 21}          # lessons published at these hours also get a Story teaser
YOUTUBE_ENABLED = False          # ready, switched off (Instagram only)
VOICE_ENABLED = False            # Gemini TTS ready, switched off
MAX_HASHTAGS = 5
LESSON_MAX_WORDS = 90
DURATION = {"concept": (20, 55), "explain": (30, 70), "calc": (45, 90)}   # seconds, incl. outro
WORD_SEC = 0.62                  # silent reading pace (long Armenian words, read on a phone)
CHUNK_MIN = 1.3                  # every caption chunk stays on screen at least this long
COURSE_LOW_WARNING = 10          # warn in Telegram when fewer scripted lessons are left
COMMENT_REPLIES_PER_RUN = 10
AI_SIGNATURE = "🤖 TradeInvest AI"
MUSIC_GROUPS = {1: "basics", 2: "basics", 3: "risk", 4: "risk", 5: "charts", 6: "charts", 7: "charts",
                8: "risk", 9: "charts", 10: "charts", 11: "charts"}
