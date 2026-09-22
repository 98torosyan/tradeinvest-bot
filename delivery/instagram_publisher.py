"""
Publishes directly to Instagram via Meta's official (free) Graph API
Content Publishing endpoints. Needs a one-time manual setup only the
account owner can do (Business/Creator account + linked Facebook Page
+ Meta app + access token) -- see README.md.

Known platform limits (Meta's, not this code's):
  - Interactive Story stickers (poll/quiz/question) cannot be added
    through the public API -- a Story posted here is a plain
    image/video. The sticker text still exists in the content plan
    for whoever wants to add it by hand afterwards.
  - Max ~25 posts per rolling 24h per IG account.
  - image_url / video_url must be a PUBLICLY reachable URL at the
    moment Instagram fetches it (see delivery/media_hosting.py).
  - The access token is a *long-lived* token (~60 days); it must be
    refreshed periodically -- see scripts/refresh_ig_token.py.
"""
import time
import requests

from config import IG_USER_ID, IG_ACCESS_TOKEN, GRAPH_API_VERSION

# graph.instagram.com, NOT graph.facebook.com: the token this project uses
# comes from the "Instagram API with Instagram Login" flow (direct Instagram
# business login, no Facebook Page token involved) -- Meta's current default
# path for a new app. Tokens from that flow are Instagram User Access Tokens
# and only work against the graph.instagram.com host; calling
# graph.facebook.com with one fails authentication.
GRAPH_BASE = f"https://graph.instagram.com/{GRAPH_API_VERSION}"


class InstagramPublishError(RuntimeError):
    pass


def _configured():
    return bool(IG_USER_ID and IG_ACCESS_TOKEN)


def _post(path, **params):
    params["access_token"] = IG_ACCESS_TOKEN
    resp = requests.post(f"{GRAPH_BASE}/{path}", data=params, timeout=60)
    data = resp.json()
    if not resp.ok or "error" in data:
        raise InstagramPublishError(f"{path} failed: {data}")
    return data


def _get(path, **params):
    params["access_token"] = IG_ACCESS_TOKEN
    resp = requests.get(f"{GRAPH_BASE}/{path}", params=params, timeout=30)
    data = resp.json()
    if not resp.ok or "error" in data:
        raise InstagramPublishError(f"{path} failed: {data}")
    return data


def _wait_until_finished(creation_id, timeout=240, interval=8):
    """Video containers (Reels/video Stories) process async server-side."""
    waited = 0
    while waited < timeout:
        data = _get(creation_id, fields="status_code")
        status = data.get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise InstagramPublishError(f"container {creation_id} failed to process: {data}")
        time.sleep(interval)
        waited += interval
    raise InstagramPublishError(f"container {creation_id} did not finish within {timeout}s")


def _publish(creation_id):
    return _post(f"{IG_USER_ID}/media_publish", creation_id=creation_id)["id"]


def publish_feed_image(image_url, caption=""):
    if not _configured():
        print("[instagram] IG_USER_ID/IG_ACCESS_TOKEN not set -- skipping")
        return None
    container = _post(f"{IG_USER_ID}/media", image_url=image_url, caption=caption)
    return _publish(container["id"])


def publish_carousel(image_urls, caption=""):
    """A carousel post (the Post/Carousel slides) -- 2 to 10 images."""
    if not _configured():
        print("[instagram] IG_USER_ID/IG_ACCESS_TOKEN not set -- skipping")
        return None
    if not (2 <= len(image_urls) <= 10):
        raise InstagramPublishError("carousel needs between 2 and 10 images")
    child_ids = []
    for url in image_urls:
        child = _post(f"{IG_USER_ID}/media", image_url=url, is_carousel_item="true")
        child_ids.append(child["id"])
    parent = _post(
        f"{IG_USER_ID}/media", media_type="CAROUSEL",
        children=",".join(child_ids), caption=caption,
    )
    return _publish(parent["id"])


def publish_reel(video_url, caption=""):
    if not _configured():
        print("[instagram] IG_USER_ID/IG_ACCESS_TOKEN not set -- skipping")
        return None
    container = _post(
        f"{IG_USER_ID}/media", media_type="REELS", video_url=video_url, caption=caption,
    )
    _wait_until_finished(container["id"])
    return _publish(container["id"])


def publish_story_image(image_url):
    if not _configured():
        print("[instagram] IG_USER_ID/IG_ACCESS_TOKEN not set -- skipping")
        return None
    container = _post(f"{IG_USER_ID}/media", media_type="STORIES", image_url=image_url)
    return _publish(container["id"])


def publish_story_video(video_url):
    if not _configured():
        print("[instagram] IG_USER_ID/IG_ACCESS_TOKEN not set -- skipping")
        return None
    container = _post(f"{IG_USER_ID}/media", media_type="STORIES", video_url=video_url)
    _wait_until_finished(container["id"])
    return _publish(container["id"])


def post_sources_comment(media_id, sources):
    """Posts a plain comment listing the real data-source links used for
    that post -- a cheap, high-trust credibility signal (this page shows
    its work, unlike a meme account). Note: the public Graph API does
    NOT expose a "pin comment" endpoint for Instagram, so this comment
    is posted but not pinned -- pinning it (one tap, in the Instagram
    app) is the one small manual step left if you want it pinned."""
    if not _configured() or not sources:
        return None
    message = "Տվյալների աղբյուրներ:\n" + "\n".join(sources)
    try:
        return _post(f"{media_id}/comments", message=message)["id"]
    except InstagramPublishError as exc:
        print(f"[instagram] could not post sources comment: {exc}")
        return None
