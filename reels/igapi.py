"""Instagram Graph API (Instagram Login, graph.instagram.com) -- everything v1.0 needs."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import IG_USER_ID  # noqa: E402
from delivery import instagram_publisher as ig  # noqa: E402

Error = ig.InstagramPublishError
configured = ig._configured


def _publish_ready(creation_id, tries=8, wait=10):
    """media_publish, retried while Instagram still says the container is not ready (code 9007 / 2207027)."""
    import time
    for k in range(tries):
        try:
            return ig._publish(creation_id)
        except Error as exc:
            if ("2207027" not in str(exc) and "'code': 9007" not in str(exc)) or k == tries - 1:
                raise
            time.sleep(wait)


def _publish_container(**params):
    c = ig._post(f"{IG_USER_ID}/media", **params)
    if params.get("media_type") in ("REELS", "STORIES", "VIDEO") or params.get("video_url"):
        ig._wait_until_finished(c["id"], timeout=300)
    return _publish_ready(c["id"])


from .caption_lint import lint as _lint  # noqa: E402


def publish_reel(video_url, caption, cover_url=None, share_to_feed=True):
    caption = _lint(caption)
    p = dict(media_type="REELS", video_url=video_url, caption=caption, share_to_feed="true" if share_to_feed else "false")
    if cover_url:
        p["cover_url"] = cover_url
    return _publish_container(**p)


def publish_story_video(video_url):
    return _publish_container(media_type="STORIES", video_url=video_url)


def publish_image(image_url, caption, alt_text=None):
    caption = _lint(caption)
    if alt_text:
        try:
            return _publish_container(image_url=image_url, caption=caption, alt_text=alt_text[:1000])
        except Error as exc:                        # alt_text not accepted -> publish without it
            print("[igapi] alt_text rejected:", str(exc)[:160])
    return _publish_container(image_url=image_url, caption=caption)


def publish_story_image(image_url):
    return _publish_container(media_type="STORIES", image_url=image_url)


def publish_carousel(image_urls, caption, alts=None):
    caption = _lint(caption)
    alts = alts or [None] * len(image_urls)
    def _kid(u, a):
        if a:
            try:
                return ig._post(f"{IG_USER_ID}/media", image_url=u, is_carousel_item="true", alt_text=a[:1000])["id"]
            except Error as exc:                    # alt_text not accepted -> item without it
                print("[igapi] alt_text rejected:", str(exc)[:160])
        return ig._post(f"{IG_USER_ID}/media", image_url=u, is_carousel_item="true")["id"]
    kids = [_kid(u, a) for u, a in zip(image_urls, alts)]
    for k in kids:                                   # every slide must be processed before the album is built
        ig._wait_until_finished(k, timeout=180, interval=4)
    c = ig._post(f"{IG_USER_ID}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)
    ig._wait_until_finished(c["id"], timeout=180, interval=5)
    return _publish_ready(c["id"])


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
