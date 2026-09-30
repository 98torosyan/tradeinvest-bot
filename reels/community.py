"""Every 15 minutes: Telegram commands (/status /pause /resume /fix) and AI replies to comments.
Runs in its own concurrency group; never renders or publishes reels."""
import datetime as dt
import os
import sys
from zoneinfo import ZoneInfo

import requests

from . import control, curriculum, gemini, settings, state

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  # noqa: E402
from delivery.telegram_sender import send_text  # noqa: E402

TG = "https://api.telegram.org/bot{}/{}"


def status_text(st):
    cur = curriculum.load()
    idx = st.get("course_index", 0)
    last = (open(os.path.join(ROOT, "reels", "last_run.md"), encoding="utf-8").read().split("\n---\n")[0]
            if os.path.exists(os.path.join(ROOT, "reels", "last_run.md")) else "—")
    nxt = cur["lessons"][idx]["id"] if idx < len(cur["lessons"]) else "—"
    return (f"📊 TradeInvest\nՎիճակ՝ {'⏸ կանգնեցված' if control.paused() else '▶️ աշխատում է'}\n"
            f"Հրապարակված դասեր՝ {len(st.get('published', {}))}, հաջորդը՝ {nxt}\n"
            f"Պատրաստի սցենարներ՝ {curriculum.scripted_left(cur, idx)}\n\nՎերջին run՝\n{last[:600]}")


def telegram_commands(st):
    if not TELEGRAM_BOT_TOKEN:
        return False
    off = control.get("tg_offset", 0) or 0
    try:
        r = requests.get(TG.format(TELEGRAM_BOT_TOKEN, "getUpdates"), params={"offset": off + 1, "timeout": 0}, timeout=30).json()
    except requests.RequestException:
        return False
    changed = False
    for u in r.get("result", []):
        off = max(off, u["update_id"]); changed = True
        cq = u.get("callback_query")
        if cq:
            if str(((cq.get("message") or {}).get("chat") or {}).get("id")).strip() == str(TELEGRAM_CHAT_ID).strip():
                from . import music_hunt
                music_hunt.on_callback(cq)
            continue
        msg = u.get("message") or {}
        if str(msg.get("chat", {}).get("id")).strip() != str(TELEGRAM_CHAT_ID).strip():
            # only the owner's chat may control the bot; remember who tried (helps to fix a wrong TELEGRAM_CHAT_ID)
            ch = msg.get("chat", {})
            control.put("tg_last_foreign", {"chat_id": ch.get("id"), "type": ch.get("type"),
                                            "name": ch.get("first_name") or ch.get("title"), "text": (msg.get("text") or "")[:30],
                                            "secret_digits": len(str(TELEGRAM_CHAT_ID).strip()),
                                            "secret_has_spaces": str(TELEGRAM_CHAT_ID) != str(TELEGRAM_CHAT_ID).strip()})
            continue
        text = (msg.get("text") or "").strip()
        media = msg.get("audio") or msg.get("document")
        if media and (msg.get("audio") or str(media.get("mime_type", "")).startswith("audio")
                      or str(media.get("file_name", "")).lower().endswith((".mp3", ".wav", ".m4a", ".ogg", ".flac"))):
            from . import music_hunt
            try:
                res, why = music_hunt.save_incoming(media["file_id"], media.get("file_name") or media.get("title") or "track",
                                                    msg.get("caption"))
            except Exception as exc:  # noqa: BLE001
                res, why = None, str(exc)[:120]
            if res:
                changed = True
                where = {"lesson": "դասերի", "news": "լուրերի", "story": "Story-ների"}[res[0]]
                send_text(f"✅ Trek-ը ստացվեց ({where} համար)։ Այն կմշակվի և կօգտագործվի հաջորդ Reel-ից սկսած։")
            elif why == "no-profile":                    # no caption: keep it and wait for one word (դաս / լուր / story)
                waiting = control.get("audio_waiting", []) or []
                waiting.append({"file_id": media["file_id"], "name": media.get("file_name") or media.get("title") or "track"})
                control.put("audio_waiting", waiting[-20:]); changed = True
                send_text(f"🎵 Ստացա ({len(waiting)} ֆայլ սպասում է)։ Հիմա գրիր մեկ բառ՝ «դաս», «լուր» կամ «story», "
                          "և այն կկիրառվի բոլոր սպասող ֆայլերի համար։")
            else:
                send_text(f"⚠️ Trek-ը չհաջողվեց ստանալ՝ {why}")
            continue
        waiting = control.get("audio_waiting", []) or []
        if waiting and text and not text.startswith("/"):
            from . import music_hunt
            prof = music_hunt.profile_from_caption(text)
            if prof:
                ok, bad = [], []
                for w in waiting:
                    try:
                        res, why = music_hunt.save_incoming(w["file_id"], w["name"], text)
                        (ok if res else bad).append(w["name"])
                    except Exception as exc:  # noqa: BLE001
                        bad.append(f"{w['name']} ({str(exc)[:40]})")
                control.put("audio_waiting", []); changed = True
                where = {"lesson": "դասերի", "news": "լուրերի", "story": "Story-ների"}[prof]
                msg_txt = f"✅ {len(ok)} trek ստացվեց ({where} համար)։ Կօգտագործվեն հաջորդ Reel-ից սկսած։"
                if bad:
                    msg_txt += "\n⚠️ Չհաջողվեց՝ " + ", ".join(bad)
                send_text(msg_txt)
                continue
        if text.startswith("/pause"):
            control.set_paused(True); send_text("⏸ Բոլոր հրապարակումները կանգնեցված են։ /resume՝ վերսկսելու համար։")
        elif text.startswith("/resume"):
            control.set_paused(False); send_text("▶️ Հրապարակումները վերսկսված են։")
        elif text.startswith("/allow"):
            words = [w.strip(".,;:") for w in text.split()[1:] if w.strip(".,;:")]
            if words:
                wl = os.path.join(ROOT, "reels", "content", "whitelist_hy.txt")
                with open(wl, "a", encoding="utf-8") as f:
                    f.write("\n".join(words) + "\n")
                changed = True
                send_text("✅ Ավելացվեց ուղղագրական բառարանում՝ " + ", ".join(words))
        elif text.startswith("/status"):
            send_text(status_text(st))
        elif text.startswith("/fix"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                send_text("Օգտագործում՝ /fix M1-03 ուղղման տեքստը"); continue
            lid, note = parts[1].upper(), parts[2]
            p = st.get("published", {}).get(lid)
            if not p:
                send_text(f"{lid} դասը դեռ հրապարակված չէ։"); continue
            try:
                from . import igapi
                igapi.comment_on(p["media"], f"✏️ Ուղղում. {note}")
                fixes = control.get("fixes", []) or []; fixes.append({"id": lid, "note": note})
                control.put("fixes", fixes)
                send_text(f"✅ Ուղղումը ավելացվեց {lid}-ի տակ։ Սցենարը կթարմացվի հաջորդ թարմացման ժամանակ։")
            except Exception as exc:  # noqa: BLE001
                send_text(f"⚠️ Ուղղումը չհաջողվեց՝ {exc}")
    if changed:
        control.put("tg_offset", off)
    return changed


REPLY_PROMPT = """You reply to Instagram comments for TradeInvest, an Armenian crypto EDUCATION page.
Lesson context (the ONLY facts you may use):
{context}

Comment by @{user}: "{text}"

Rules: answer in natural Eastern Armenian (keep terms like Bitcoin, stop loss in English), max 2 short sentences,
friendly and calm. Never give financial advice, price predictions, buy/sell suggestions or promises. If the comment asks
for advice or something outside the lesson, politely say that the page is educational and point to the course (bio link).
Decide an action: "reply" for genuine questions/feedback, "hide" for spam, scams, links, insults, "ignore" for emojis/very short praise.
Return ONLY JSON: {{"action": "reply|hide|ignore", "reply": "<text or empty>"}}"""


def comments(st):
    from . import igapi
    if not igapi.configured():
        return 0
    try:
        me = igapi.me(); my_name = me.get("username", "")
    except igapi.Error as exc:
        print("[comments] token problem:", exc); return 0
    by_media = {p["media"]: lid for lid, p in st.get("published", {}).items()}
    cur = {l["id"]: l for l in curriculum.load()["lessons"]}
    done = 0
    try:
        media = igapi.recent_media(8)
    except igapi.Error as exc:
        print("[comments]", exc); return 0
    for m in media:
        try:
            cs = igapi.comments(m["id"])
        except igapi.Error as exc:
            print("[comments] no permission or error:", str(exc)[:160]); return done
        for c in cs:
            if done >= settings.COMMENT_REPLIES_PER_RUN:
                return done
            if c.get("username") == my_name or c.get("hidden"):
                continue
            if any(r.get("username") == my_name for r in (c.get("replies") or {}).get("data", [])):
                continue
            l = cur.get(by_media.get(m["id"], ""), {})
            context = (l.get("title", "") + ". " + l.get("summary", "") + " " +
                       " ".join(b.get("text", "") + " " + b.get("title", "") for b in l.get("beats", []))) or (m.get("caption") or "")[:600]
            try:
                d = gemini.generate_json(REPLY_PROMPT.format(context=context[:1500], user=c.get("username"), text=c.get("text", "")[:500]), 0.3)
            except Exception as exc:  # noqa: BLE001
                print("[comments] gemini:", exc); return done
            act, reply = d.get("action"), (d.get("reply") or "").strip()
            from .qa import BANNED
            from .qa import text_ok
            spelled_ok = text_ok(reply, 0.05, 1)[0] if reply else False
            if act == "reply" and reply and spelled_ok and len(reply) < 400 and not any(b.lower() in reply.lower() for b in BANNED):
                igapi.reply(c["id"], f"{reply}\n{settings.AI_SIGNATURE}")
                send_text(f"💬 @{c.get('username')}: {c.get('text')}\n↳ {reply}")
                done += 1
            elif act == "hide":
                try:
                    igapi.hide(c["id"]); send_text(f"🙈 Թաքցված comment @{c.get('username')}: {c.get('text')}")
                except igapi.Error:
                    pass
    return done


def main():
    st = state.load()
    changed = telegram_commands(st)
    try:
        comments(st)
    except Exception as exc:  # noqa: BLE001
        print("[comments] failed:", exc)
    if changed:
        control.commit(["control", "reels/content/whitelist_hy.txt", "reels/assets/music/incoming"], "control: telegram commands")


if __name__ == "__main__":
    main()
