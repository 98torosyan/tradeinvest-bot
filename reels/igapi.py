"""Instagram Graph API (Instagram Login, graph.instagram.com) -- everything v1.0 needs."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import IG_USER_ID  # noqa: E402
from delivery import instagram_publisher as ig  # noqa: E402

Error = ig.InstagramPublishError
configured = ig._configured


def _publish_container(**params):
    c = ig._post(f"{IG_USER_ID}/media", **params)
    if params.get("media_type") in ("REELS", "STORIES", "VIDEO") or params.get("video_url"):
        ig._wait_until_finished(c["id"], timeout=300)
    return ig._publish(c["id"])


def publish_reel(video_url, caption, cover_url=None, share_to_feed=True):
    p = dict(media_type="REELS", video_url=video_url, caption=caption, share_to_feed="true" if share_to_feed else "false")
    if cover_url:
        p["cover_url"] = cover_url
    return _publish_container(**p)


def publish_story_video(video_url):
    return _publish_container(media_type="STORIES", video_url=video_url)


def publish_carousel(image_urls, caption):
    kids = [ig._post(f"{IG_USER_ID}/media", image_url=u, is_carousel_item="true")["id"] for u in image_urls]
    c = ig._post(f"{IG_USER_ID}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)
    return ig._publish(c["id"])


def recent_media(limit=25):
    d = ig._get(f"{IG_USER_ID}/media", fields="id,caption,permalink,timestamp,media_product_type", limit=limit)
    return d.get("data", [])


def permalink(media_id):
    try:
        return ig._get(media_id, fields="permalink").get("permalink")
    except Error:
        return None


def me():
    return ig._get("me", fields="user_id,username,followers_count,media_count")


def comments(media_id):
    d = ig._get(f"{media_id}/comments", fields="id,text,username,timestamp,hidden,replies{username,text}", limit=50)
    return d.get("data", [])


def reply(comment_id, text):
    return ig._post(f"{comment_id}/replies", message=text)


def hide(comment_id):
    return ig._post(comment_id, hide="true")


def comment_on(media_id, text):
    return ig._post(f"{media_id}/comments", message=text)


def insights(media_id, metrics=("reach", "views", "likes", "comments", "saved", "shares", "total_interactions",
                                 "ig_reels_avg_watch_time")):
    out = {}
    for m in metrics:                      # one by one: unsupported metrics must not break the rest
        try:
            d = ig._get(f"{media_id}/insights", metric=m)
            out[m] = d["data"][0]["values"][0]["value"]
        except (Error, KeyError, IndexError):
            pass
    return out


def publishing_quota():
    try:
        d = ig._get(f"{IG_USER_ID}/content_publishing_limit", fields="quota_usage,config")
        return d.get("data", [{}])[0]
    except Error:
        return {}
