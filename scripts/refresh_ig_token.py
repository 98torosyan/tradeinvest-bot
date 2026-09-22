"""
Refreshes the long-lived Instagram/Facebook access token before it
expires (long-lived tokens last ~60 days). Meant to run on its own
monthly schedule (see .github/workflows/refresh-token.yml) so the
daily content workflow never silently starts failing because the
token went stale.

Two ways this can end, depending on what secrets are set:
  1. If GH_PAT (a GitHub Personal Access Token with the "repo" scope,
     specifically permission to manage Actions secrets) is set, the
     new token is written directly into the IG_ACCESS_TOKEN repo
     secret -- fully automatic, nothing for you to do. This is the
     recommended setup for a hands-off, Instagram-only pipeline with
     zero manual steps ever.
  2. Otherwise, the new token is written to this run's GitHub Actions
     summary page (Actions tab -> the run -> top of the page) so you
     can paste it into the IG_ACCESS_TOKEN secret by hand. It is also
     sent on Telegram as a bonus, if Telegram is configured -- but
     Telegram is entirely optional, this never depends on it.

Requires FB_APP_ID and FB_APP_SECRET (from the same Meta app used to
create IG_ACCESS_TOKEN in the first place) -- see README.md.
"""
import base64
import os
import sys

import requests
from nacl import encoding, public

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import IG_ACCESS_TOKEN, GRAPH_API_VERSION
from delivery import telegram_sender

FB_APP_ID = os.environ.get("FB_APP_ID", "")
FB_APP_SECRET = os.environ.get("FB_APP_SECRET", "")
GH_PAT = os.environ.get("GH_PAT", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")  # "owner/repo", set by Actions

GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def refresh_token():
    resp = requests.get(f"{GRAPH_BASE}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": FB_APP_ID,
        "client_secret": FB_APP_SECRET,
        "fb_exchange_token": IG_ACCESS_TOKEN,
    }, timeout=30)
    data = resp.json()
    if not resp.ok or "access_token" not in data:
        raise RuntimeError(f"token refresh failed: {data}")
    return data["access_token"], data.get("expires_in")


def _write_step_summary(text):
    """Writes to the GitHub Actions run summary page (visible in the
    Actions tab for that run, no extra setup needed) -- the fallback
    place to find the new token when Telegram isn't configured, so it
    is never silently dropped just because telegram_sender no-ops."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    try:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    except OSError:
        pass


def update_github_secret(name, value):
    owner_repo = GITHUB_REPOSITORY
    pub_key_resp = requests.get(
        f"https://api.github.com/repos/{owner_repo}/actions/secrets/public-key",
        headers={"Authorization": f"Bearer {GH_PAT}", "Accept": "application/vnd.github+json"},
        timeout=20,
    )
    pub_key_resp.raise_for_status()
    key_data = pub_key_resp.json()

    public_key = public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(value.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

    put_resp = requests.put(
        f"https://api.github.com/repos/{owner_repo}/actions/secrets/{name}",
        headers={"Authorization": f"Bearer {GH_PAT}", "Accept": "application/vnd.github+json"},
        json={"encrypted_value": encrypted_b64, "key_id": key_data["key_id"]},
        timeout=20,
    )
    put_resp.raise_for_status()


def main():
    if not (FB_APP_ID and FB_APP_SECRET and IG_ACCESS_TOKEN):
        print("[refresh_ig_token] FB_APP_ID / FB_APP_SECRET / IG_ACCESS_TOKEN not all set -- nothing to do")
        return

    new_token, expires_in = refresh_token()
    days = round((expires_in or 0) / 86400, 1)

    if GH_PAT and GITHUB_REPOSITORY:
        update_github_secret("IG_ACCESS_TOKEN", new_token)
        telegram_sender.send_text(
            f"🔑 Instagram access token թարմացվեց ինքնաշխատ (նոր token-ը վավեր է ~{days} օր)։"
        )
        _write_step_summary(f"✅ IG_ACCESS_TOKEN refreshed automatically -- valid ~{days} more days.")
        print(f"[refresh_ig_token] IG_ACCESS_TOKEN secret updated, valid ~{days} days")
    else:
        # GH_PAT not set -- can't write the secret automatically. Telegram is
        # only a bonus notification here (it no-ops quietly if not
        # configured), so the token ALWAYS also goes to the Actions run
        # summary -- that's reachable with just a GitHub login, no Telegram
        # bot required, which matters for an Instagram-only setup.
        telegram_sender.send_text(
            "🔑 Instagram access token-ը մոտենում է ժամկետին։ Նոր token (պահի՛ր և տեղադրիր "
            f"IG_ACCESS_TOKEN secret-ում, վավեր է ~{days} օր).\n\n{new_token}"
        )
        _write_step_summary(
            "### 🔑 New Instagram access token needed\n\n"
            f"Valid ~{days} more days. Copy it into the `IG_ACCESS_TOKEN` repo secret "
            "(Settings → Secrets and variables → Actions):\n\n"
            f"```\n{new_token}\n```\n\n"
            "(Set a `GH_PAT` secret to skip this manual step next time -- see README.md.)"
        )
        print("[refresh_ig_token] GH_PAT not set -- new token written to the Actions run summary "
              "(and sent via Telegram if configured) for manual update")


if __name__ == "__main__":
    main()
