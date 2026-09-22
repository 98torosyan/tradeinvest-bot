"""
Sends the finished daily content package to Telegram via the plain
Bot HTTP API (no extra SDK needed). One text message with the full
plan, then the carousel slide images, the chart, and the two Reel
videos as separate messages so they preview nicely in the chat.
"""
import os
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API_BASE = "https://api.telegram.org/bot{token}/{method}"
MAX_TEXT_LEN = 4000  # Telegram's real limit is 4096; leave headroom


def _url(method):
    return API_BASE.format(token=TELEGRAM_BOT_TOKEN, method=method)


def _check_configured():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[telegram] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set -- skipping send")
        return False
    return True


def send_text(text):
    if not _check_configured():
        return
    for i in range(0, len(text), MAX_TEXT_LEN):
        chunk = text[i:i + MAX_TEXT_LEN]
        resp = requests.post(_url("sendMessage"), data={
            "chat_id": TELEGRAM_CHAT_ID, "text": chunk,
        }, timeout=30)
        if not resp.ok:
            print(f"[telegram] sendMessage failed: {resp.status_code} {resp.text}")


def send_photo(path, caption=None):
    if not _check_configured() or not os.path.exists(path):
        return
    with open(path, "rb") as fh:
        resp = requests.post(_url("sendPhoto"), data={
            "chat_id": TELEGRAM_CHAT_ID, "caption": (caption or "")[:1024],
        }, files={"photo": fh}, timeout=60)
    if not resp.ok:
        print(f"[telegram] sendPhoto failed: {resp.status_code} {resp.text}")


def send_video(path, caption=None):
    if not _check_configured() or not os.path.exists(path):
        return
    with open(path, "rb") as fh:
        resp = requests.post(_url("sendVideo"), data={
            "chat_id": TELEGRAM_CHAT_ID, "caption": (caption or "")[:1024],
        }, files={"video": fh}, timeout=180)
    if not resp.ok:
        print(f"[telegram] sendVideo failed: {resp.status_code} {resp.text}")
