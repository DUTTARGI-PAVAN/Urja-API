from app.portal_client import PortalClient

c = PortalClient()
print(c.search_meters(page=1))
print(c.list_dts())
print(c.export_meters(page=1))