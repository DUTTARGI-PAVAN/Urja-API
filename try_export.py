import json
from app.portal_client import PortalClient

c = PortalClient()
rows, page = [], 1
while True:
    resp = c.export_meters(page=page)
    batch = resp["data"]
    if not batch:
        break
    rows.extend(batch)
    print(f"page {page}: {len(batch)} rows, total={resp['total']}")
    if len(rows) >= resp["total"]:
        break
    page += 1

json.dump(rows, open("export.json", "w"), indent=2)
print("saved", len(rows))