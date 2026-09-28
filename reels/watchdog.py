"""Hourly health check: missed/failed runs (one automatic retry), token refresh health,
scripts running low; weekly (Sunday) API + limits check."""
import datetime as dt
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

from . import control, curriculum, settings, state

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from delivery.telegram_sender import send_text  # noqa: E402

LESSON_HOURS = [9, 12, 15, 18, 21]


def gh(*args):
    r = subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def last_runs(workflow, n=10):
    out = gh("run", "list", "--workflow", workflow, "-L", str(n), "--json", "conclusion,status,createdAt,displayTitle,event")
    try:
        return json.loads(out or "[]")
    except ValueError:
        return []


def check_lessons(now, st, mem):
    alerts = []
    due = [h for h in LESSON_HOURS if h * 60 + 7 + 50 <= now.hour * 60 + now.minute]      # 50 min grace after each slot
    if not due or control.paused():
        return alerts
    last_slot = due[-1]
    today = now.strftime("%Y-%m-%d")
    pubs_today = [p for p in st.get("published", {}).values() if p.get("date") == today]
    key = f"{today}-{last_slot}"
    cur = curriculum.load()
    if len(pubs_today) < len(due) and curriculum.scripted_left(cur, st.get("course_index", 0)) > 0 and key not in mem.get("retried", []):
        gh("workflow", "run", "reels.yml", "-f", "kind=lesson")
        mem.setdefault("retried", []).append(key); mem["retried"] = mem["retried"][-40:]
        alerts.append(f"⚠️ {last_slot}:07-ի դասը չհրապարակվեց։ Ավտոմատ նոր փորձ է գործարկվել։")
    elif len(pubs_today) < len(due) and key in mem.get("retried", []) and key not in mem.get("alerted", []):
        mem.setdefault("alerted", []).append(key); mem["alerted"] = mem["alerted"][-40:]
        alerts.append(f"❌ {last_slot}:07-ի դասը չհրապարակվեց նաև կրկին փորձից հետո։ Ստուգիր reels/last_run.md-ն կամ գրիր /status։")
    return alerts


def check_token_refresh(mem, today):
    runs = last_runs("refresh-token.yml", 3)
    if runs and runs[0].get("conclusion") == "failure" and mem.get("refresh_alert") != today:
        mem["refresh_alert"] = today
        return ["🔑 Instagram token-ի ավտոմատ թարմացումը ձախողվել է (հավանաբար GH_PAT secret-ը բացակայում է)։ "
                "Առանց դրա token-ը կլրանա մոտ 60 օրում, և հրապարակումները կկանգնեն։"]
    return []


def check_scripts(st, mem, today):
    cur = curriculum.load()
    left = curriculum.scripted_left(cur, st.get("course_index", 0))
    if left < settings.COURSE_LOW_WARNING and mem.get("scripts_alert") != today:
        mem["scripts_alert"] = today
        return [f"📚 Մնացել է {left} պատրաստի սցենար (~{left / 5:.1f} օր)։ Ժամանակն է գրել հաջորդ մոդուլը։"]
    return []


def weekly(now):
    msgs = []
    from . import igapi
    try:
        m = igapi.me(); msgs.append(f"✅ Instagram token՝ աշխատում է (@{m.get('username')}, հետևորդներ՝ {m.get('followers_count')})")
        q = igapi.publishing_quota()
        if q:
            msgs.append(f"✅ Հրապարակման քվոտա՝ {q.get('quota_usage')}/{(q.get('config') or {}).get('quota_total', '?')}")
    except Exception as exc:  # noqa: BLE001
        msgs.append(f"❌ Instagram API՝ {str(exc)[:150]}")
    try:
        from . import gemini
        gemini.generate_json('Return {"ok": true}', 0); msgs.append("✅ Gemini՝ աշխատում է")
    except Exception as exc:  # noqa: BLE001
        msgs.append(f"❌ Gemini՝ {str(exc)[:150]}")
    try:
        import requests
        r = requests.get("https://api.pexels.com/videos/search", params={"query": "city", "per_page": 1},
                         headers={"Authorization": os.environ.get("PEXELS_API_KEY", "")}, timeout=20)
        msgs.append("✅ Pexels՝ աշխատում է" if r.ok else f"❌ Pexels՝ HTTP {r.status_code}")
    except Exception as exc:  # noqa: BLE001
        msgs.append(f"❌ Pexels՝ {exc}")
    size = subprocess.run(["git", "count-objects", "-vH"], cwd=ROOT, capture_output=True, text=True).stdout
    pack = next((l.split(":", 1)[1].strip() for l in size.splitlines() if l.startswith("size-pack")), "?")
    msgs.append(f"ℹ️ Repo-ի չափը՝ {pack}")
    return ["🩺 Շաբաթական տեխնիկական ստուգում\n" + "\n".join(msgs)]


def main():
    now = dt.datetime.now(ZoneInfo(settings.TZ)); today = now.strftime("%Y-%m-%d")
    st = state.load(); mem = control.get("watchdog", {}) or {}
    alerts = []
    for fn in (lambda: check_lessons(now, st, mem), lambda: check_token_refresh(mem, today), lambda: check_scripts(st, mem, today)):
        try:
            alerts += fn()
        except Exception as exc:  # noqa: BLE001
            print("[watchdog]", exc)
    if "--weekly" in sys.argv:
        alerts += weekly(now)
    for a in alerts:
        send_text(a)
    control.put("watchdog", mem)
    control.commit(["control"], "watchdog")


if __name__ == "__main__":
    main()
