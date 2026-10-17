"""Builds content/hits.json from hits.py (season 1) and hits2.py (season 2). Ids are stable: H-001...
Season 2 Reels get a visual style, rotated so that neighbours always differ."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hits import H, SERIES
from hits2 import H2
ORDER = ["neon", "editorial", "terminal", "glass", "marker"]
out = [dict(spec, id=f"H-{i:03d}", module=ser, n=i, status="script", series=SERIES[ser], type="explain")
       for i, (ser, spec) in enumerate(H, 1)]
for j, (ser, spec) in enumerate(H2):
    i = len(H) + 1 + j
    out.append(dict(spec, id=f"H-{i:03d}", module=ser, n=i, status="script", series=SERIES[ser], type="explain",
                    style=ORDER[(j + j // 5) % 5], season=2))
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"series": SERIES, "modules": [{"n": k, "title": v} for k, v in SERIES.items()], "lessons": out},
          open(os.path.join(here, "hits.json"), "w"), ensure_ascii=False, indent=1)
print(len(out), "Reels;", len(H2), "new")
