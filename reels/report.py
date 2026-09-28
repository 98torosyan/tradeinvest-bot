"""Sunday report: last 7 days of Instagram results -> Telegram, and bandit learning
(which CTA type earns more sends per reach)."""
import datetime as dt
import os
import statistics
import sys
from zoneinfo import ZoneInfo

from . import bandit, settings, state

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from delivery.telegram_sender import send_text  # noqa: E402


def main():
    from . import igapi
    now = dt.datetime.now(ZoneInfo(settings.TZ))
    since = (now - dt.timedelta(days=7)).strftime("%Y-%m-%d")
    st = state.load()
    rows = []
    for lid, p in st.get("published", {}).items():
        if p.get("date", "") < since or p.get("insights_done"):
            continue
        ins = igapi.insights(p["media"])
        if not ins:
            continue
        reach = max(1, ins.get("reach", 0))
        rows.append({"id": lid, "hour": p.get("hour"), "cta": p.get("cta"), "reach": reach,
                     "send_rate": ins.get("shares", 0) / reach, "save_rate": ins.get("saved", 0) / reach,
                     "watch": ins.get("ig_reels_avg_watch_time", 0), **ins})
    if not rows:
        send_text("📈 Շաբաթական հաշվետվություն. տվյալներ դեռ չկան (կամ insights-ի թույլտվությունը բացակայում է token-ում)։")
        return
    med = statistics.median(r["send_rate"] + r["save_rate"] for r in rows)
    for r in rows:
        if r.get("cta"):
            bandit.update(st, "cta", r["cta"], r["send_rate"] + r["save_rate"] > med)
        st["published"][r["id"]]["insights_done"] = True
    top = sorted(rows, key=lambda r: r["send_rate"] + r["save_rate"], reverse=True)[:3]
    by_hour = {}
    for r in rows:
        by_hour.setdefault(r["hour"], []).append(r["reach"])
    best_hour = max(by_hour, key=lambda h: statistics.mean(by_hour[h])) if by_hour else "?"
    try:
        fol = igapi.me().get("followers_count")
    except Exception:  # noqa: BLE001
        fol = "?"
    lines = [f"📈 Շաբաթական հաշվետվություն ({since} → {now:%Y-%m-%d})",
             f"Հետևորդներ՝ {fol}", f"Դասեր՝ {len(rows)}, ընդհանուր reach՝ {sum(r['reach'] for r in rows)}",
             f"Միջին դիտման ժամանակ՝ {statistics.mean(r['watch'] or 0 for r in rows) / 1000:.1f} վրկ",
             f"Ամենաարդյունավետ ժամը՝ {best_hour}:07", "", "🏆 Լավագույն դասերը (ուղարկումներ + save-եր / reach)."]
    lines += [f"• {r['id']}՝ {100 * (r['send_rate'] + r['save_rate']):.1f}% (reach {r['reach']})" for r in top]
    arms = st.get("bandit", {}).get("cta", {})
    lines += ["", "🎯 CTA-ներ՝ " + ", ".join(f"{k} {a / (a + n):.0%}" for k, (a, n) in arms.items())]
    send_text("\n".join(lines))
    state.save(st)
    from .control import commit
    commit(["reels/state.json"], "weekly report")


if __name__ == "__main__":
    main()
