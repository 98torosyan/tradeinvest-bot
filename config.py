"""
Central configuration for the TradeInvest daily content bot.
All secrets are read from environment variables (set as GitHub Actions
secrets in production, or a local .env file for testing).
"""
import os

# --- Branding -----------------------------------------------------------
BRAND_NAME = "TradeInvest"
BRAND_HANDLE = "@armtradeinvest"
BRAND_ACCENT_COLOR = "#3B82F6"   # premium blue accent
BRAND_BG_COLOR = "#0B0E14"       # near-black navy background
BRAND_BG_COLOR_2 = "#141B2D"     # gradient second stop
BRAND_TEXT_COLOR = "#F5F7FA"
BRAND_MUTED_COLOR = "#9AA5B1"
BRAND_GREEN = "#22C55E"
BRAND_RED = "#EF4444"
BRAND_ALERT_COLOR = "#EF4444"
DATA_SOURCE_LABEL = "Տվյալների աղբյուր՝ CoinGecko, alternative.me, FRED"

# --- Secrets / API keys (every one of these is optional) ----------------
# Telegram is a fully optional side-channel delivery -- if these two are
# left blank, delivery/telegram_sender.py just no-ops (see _check_configured
# there); nothing else in the pipeline depends on it. An Instagram-only
# setup (IG_USER_ID + IG_ACCESS_TOKEN below, no Telegram at all) works fine.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# FRED (Federal Reserve Economic Data) - free key from https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# --- Instagram Graph API (free, official Meta API) -------------------------
# Requires a one-time manual setup only the account owner can do -- see
# README.md "Instagram-ում ուղիղ auto-post" section for exact steps.
IG_USER_ID = os.environ.get("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION", "v21.0")

# Public base URL where this run's media becomes reachable (GitHub Pages).
# In GitHub Actions this is filled in automatically from GITHUB_REPOSITORY /
# GITHUB_REPOSITORY_OWNER; PAGES_BASE_URL overrides it (e.g. a custom domain).
_gh_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
_gh_repo_full = os.environ.get("GITHUB_REPOSITORY", "")
_gh_repo = _gh_repo_full.split("/")[-1] if _gh_repo_full else ""
PAGES_BASE_URL = os.environ.get(
    "PAGES_BASE_URL",
    f"https://{_gh_owner}.github.io/{_gh_repo}" if _gh_owner and _gh_repo else "",
)

# --- Coins tracked --------------------------------------------------------
COINGECKO_IDS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
}
PRIMARY_COIN = "bitcoin"

# --- News sources (free RSS, no API key needed) --------------------------
NEWS_RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
]
MAX_HEADLINES = 8

# --- Output ----------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# --- Weekly content rotation (rule #10 from the brief) ---------------------
WEEKDAY_THEMES = {
    0: "Market / Bitcoin",            # Monday
    1: "Education",                   # Tuesday
    2: "Breaking News",               # Wednesday
    3: "Trading Psychology",          # Thursday
    4: "Market Recap",                # Friday
    5: "Crypto Facts / Community",    # Saturday
    6: "Weekly Outlook / Education",  # Sunday
}
