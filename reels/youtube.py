"""Optional YouTube Shorts cross-post (YouTube Data API v3, resumable upload). Does nothing until three secrets exist:
YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (OAuth "installed app", scope youtube.upload).
Every Reel that goes to Instagram can also go to YouTube as a Short (vertical, < 60 s, #Shorts in the title)."""
import json
import os
import re

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"


def configured():
    return all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def _access_token():
    r = requests.post(TOKEN_URL, data={"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                       "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def _title(text):
    t = re.sub(r"[*_|]", "", text).strip()
    t = re.sub(r"\s+", " ", t)
    t = t[:88].rstrip(" ,.։")
    return f"{t} #Shorts"


def upload(mp4, title, description, tags=None):
    """Returns the YouTube video id, or None when not configured."""
    if not configured():
        return None
    tok = _access_token()
    meta = {"snippet": {"title": _title(title), "description": description[:4900], "tags": (tags or [])[:15],
                        "categoryId": "27", "defaultLanguage": "hy", "defaultAudioLanguage": "hy"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    size = os.path.getsize(mp4)
    init = requests.post(UPLOAD_URL, headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                                              "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"},
                         data=json.dumps(meta), timeout=60)
    init.raise_for_status()
    with open(mp4, "rb") as fh:
        up = requests.put(init.headers["Location"], headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"},
                          data=fh, timeout=600)
    up.raise_for_status()
    return up.json().get("id")
