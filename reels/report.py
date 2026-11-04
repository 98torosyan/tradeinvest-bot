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


def _label(st):
    """media id -> (kind, our id) for everything the bot published."""
    lab = {}
    for sid, p in st.get("shorts_done", {}).items():
        lab[p.get("media")] = ("Կարճ դաս", sid)
    for p in st.get("analysis_media", []):
        lab[p.get("media")] = ("Վերլուծություն", p.get("asset", ""))
    for pid, p in st.get("posters_done", {}).items():
        lab[p.get("media")] = ("Պոստեր", pid)
    for p in st.get("monthly_media", []):
        lab[p.get("media")] = ("Ամսական ինֆոգրաֆիկա", p.get("date", ""))
    for p in st.get("weekly_media", []):
        lab[p.get("media")] = ("Շաբաթվա ամփոփում", p.get("date", ""))
    for cid, p in st.get("edu_carousels_done", {}).items():
        lab[p.get("media")] = ("Կարուսել", cid)
    return lab


def main(dry=False):
    from . import igapi
    global send_text
    if dry:
        send_text = print  # noqa: F811
    now = dt.datetime.now(ZoneInfo(settings.TZ))
    since_dt = now - dt.timedelta(days=7)
    since = since_dt.strftime("%Y-%m-%d")
    st = state.load()
    lab = _label(st)
    rows = []
    for m in igapi.recent_media(50):
        if (m.get("timestamp") or "")[:10] < since:
            continue
        ins = igapi.insights(m["id"])
        if not ins:
            continue
        kind, sid = lab.get(m["id"], ("Հին գրառում", ""))
        reach = max(1, ins.get("reach", 0))
        rows.append({"id": sid or m["id"][-5:], "kind": kind, "reach": reach, "views": ins.get("views", 0),
                     "saved": ins.get("saved", 0), "shares": ins.get("shares", 0), "likes": ins.get("likes", 0),
                     "eng": (ins.get("saved", 0) + ins.get("shares", 0)) / reach,
                     "watch": ins.get("ig_reels_avg_watch_time", 0), "hour": int((m.get("timestamp") or "T00")[11:13] or 0)})
    try:
        fol = igapi.me().get("followers_count")
    except Exception:  # noqa: BLE001
        fol = None
    prev = st.get("followers_last")
    if fol is not None:
        st["followers_last"] = fol
        st.setdefault("followers_hist", []).append({"date": now.strftime("%Y-%m-%d"), "n": fol})
        st["followers_hist"] = st["followers_hist"][-60:]
    if not rows:
        send_text("📈 Շաբաթական հաշվետվություն. այս շաբաթ տվյալներ դեռ չկան (կամ insights-ի թույլտվությունը բացակայում է token-ում)։")
        if not dry:
            state.save(st)
        return
    delta = f" ({fol - prev:+d} շաբաթում)" if fol is not None and prev is not None else ""
    lines = [f"📈 Շաբաթական հաշվետվություն · {since} → {now:%Y-%m-%d}", "",
             f"👥 Հետևորդներ՝ {fol if fol is not None else '?'}{delta}",
             f"👁 Դիտումներ՝ {sum(r['views'] for r in rows)} · Reach՝ {sum(r['reach'] for r in rows)}",
             f"📌 Save՝ {sum(r['saved'] for r in rows)} · 📩 Share՝ {sum(r['shares'] for r in rows)}", "", "Ըստ տեսակի (միջինը).",]
    kinds = {}
    for r in rows:
        kinds.setdefault(r["kind"], []).append(r)
    for k, rs in sorted(kinds.items(), key=lambda kv: -statistics.mean(r["views"] for r in kv[1])):
        lines.append(f"• {k} ({len(rs)})՝ {statistics.mean(r['views'] for r in rs):.0f} դիտում, "
                     f"{100 * statistics.mean(r['eng'] for r in rs):.1f}% save+share")
    top = sorted(rows, key=lambda r: r["views"], reverse=True)[:3]
    lines += ["", "🏆 Ամենաշատ դիտված."] + [f"• {r['kind']} {r['id']}՝ {r['views']} դիտում" for r in top]
    best = max(rows, key=lambda r: r["eng"])
    lines += ["", f"💎 Ամենաշատ պահված/կիսված՝ {best['kind']} {best['id']} ({100 * best['eng']:.1f}%)"]
    try:                                                   # which hook formulas work best (shorts only)
        from . import shorts as _sh
        fm = {x["id"]: x.get("formula") for x in _sh.load() if x.get("formula")}
        byf = {}
        for r in rows:
            if r["kind"] == "Կարճ դաս" and fm.get(r["id"]):
                byf.setdefault(fm[r["id"]], []).append(r["views"])
        if byf:
            best_f = sorted(byf.items(), key=lambda kv: -statistics.mean(kv[1]))[:3]
            lines += ["", "🪝 Hook-ի բանաձևեր (միջին դիտում)."] + [f"• {k}՝ {statistics.mean(v):.0f}" for k, v in best_f]
    except Exception as exc:  # noqa: BLE001
        print("[report] formulas", exc)
    reels = [r for r in rows if r["watch"]]
    if reels:
        lines.append(f"⏱ Reel-ի միջին դիտման ժամանակ՝ {statistics.mean(r['watch'] for r in reels) / 1000:.1f} վրկ")
    # simple, honest recommendations
    rec = []
    if len(kinds) > 1:
        k_best = max(kinds, key=lambda k: statistics.mean(r["views"] for r in kinds[k]))
        rec.append(f"«{k_best}» տեսակն այս շաբաթ ամենաշատն է դիտվել")
    if reels and statistics.mean(r["watch"] for r in reels) < 4000:
        rec.append("Reel-երի դիտման ժամանակը կարճ է. hook-ը պետք է ավելի ուժեղ լինի առաջին 1 վրկ-ում")
    if sum(r["shares"] for r in rows) == 0:
        rec.append("Share չկա. caption-ում ավելի հաճախ խնդրենք «ուղարկիր ընկերոջդ»")
    if rec:
        lines += ["", "💡 Եզրակացություն."] + [f"• {x}" for x in rec]
    send_text("\n".join(lines))
    if dry:
        return
    st.setdefault("weekly_reports", []).append({"date": now.strftime("%Y-%m-%d"), "rows": rows[:30], "followers": fol})
    st["weekly_reports"] = st["weekly_reports"][-12:]
    state.save(st)
    from .control import commit
    commit(["reels/state.json"], "weekly report")


if __name__ == "__main__":
    main()
