import json
from collections import Counter, defaultdict

rows = json.load(open("export.json"))
print("rows:", len(rows), "unique ids:", len({r["meterId"] for r in rows}))

# 1. Which key sets exist? (messy records show up here)
print(Counter(tuple(sorted(r.keys())) for r in rows))

# 2. Distinct values of categorical fields
for f in ["make", "phaseType", "installStatus", "installType", "build"]:
    print(f, Counter(r.get(f) for r in rows))

# 3. Missing / null geo or hierarchy levels
print("no geo:", sum(1 for r in rows if not r.get("geo")))
levels = ["zone", "circle", "division", "subdivision", "substation", "feeder", "dt"]
for lv in levels:
    print(lv, "missing:", sum(1 for r in rows if not (r.get("hierarchy") or {}).get(lv)))

# 4. Does each code have exactly one parent? (tests the "not a tree" finding)
parents = defaultdict(set)
for r in rows:
    h = r.get("hierarchy") or {}
    for child, parent in zip(levels[1:], levels[:-1]):
        if h.get(child) and h.get(parent):
            parents[(child, h[child]["code"])].add(h[parent]["code"])
print({k: v for k, v in parents.items() if len(v) > 1})

# 5. Top-level dtCode vs hierarchy.dt.code mismatches
print([r["meterId"] for r in rows
       if r.get("dtCode") != (r.get("hierarchy") or {}).get("dt", {}).get("code")])