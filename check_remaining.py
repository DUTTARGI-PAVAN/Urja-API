import json
from collections import Counter
from app.portal_client import PortalClient

rows = json.load(open("export.json"))
c = PortalClient()
levels = ["zone", "circle", "division", "subdivision", "substation", "feeder", "dt"]

# 1. Blank codes: how many meters, which levels, which build
blank = Counter()
for r in rows:
    for lv in levels:
        if not r["hierarchy"][lv].get("code"):
            blank[(lv, r["build"])] += 1
print("blank codes (level, build):", dict(blank))

# 2. Geo bounds
lats = [r["geo"]["lat"] for r in rows]
lngs = [r["geo"]["lng"] for r in rows]
print("lat", min(lats), max(lats), "lng", min(lngs), max(lngs))

# 3. Search total vs export total
print("search total:", c._get("/portal/meters/search", params={"q": "", "page": 1})["total"],
      "export total:", len(rows))

# 4. Does every dtCode exist in /portal/dts?
dts = {d["code"] for d in c.list_dts()}
missing = sorted({r["dtCode"] for r in rows} - dts)
print("DTs in portal:", len(dts), "| meter dtCodes not in DT list:", missing)

# 5. Export geo vs /geo endpoint
for r in rows[:5]:
    g = c._get(f"/portal/meters/{r['meterId']}/geo")["data"]
    print(r["meterId"], r["geo"], g)