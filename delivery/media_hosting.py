"""
Instagram's Graph API needs a *publicly reachable URL* for every
image/video it publishes -- it fetches the file itself, a local path
or a Telegram file isn't enough. This project hosts each day's media
for free on GitHub Pages: the workflow copies output/<date>/... into
docs/media/<date>/... and pushes it, GitHub serves it at a
predictable URL, and this module just builds that URL and waits for
it to actually be live before Instagram is asked to fetch it (Pages
deployments take anywhere from a few seconds to ~1-2 minutes).
"""
import os
import time
import requests

from config import PAGES_BASE_URL


def public_url_for(date_str, relative_path):
    if not PAGES_BASE_URL:
        raise RuntimeError(
            "PAGES_BASE_URL could not be determined -- set it explicitly "
            "(repo variable) or run inside GitHub Actions."
        )
    return f"{PAGES_BASE_URL}/media/{date_str}/{relative_path.lstrip('/')}"


def wait_until_reachable(url, timeout=180, interval=5):
    waited = 0
    while waited < timeout:
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(interval)
        waited += interval
    print(f"[media_hosting] {url} not reachable after {timeout}s")
    return False
