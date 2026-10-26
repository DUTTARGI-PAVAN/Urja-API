from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from .models import Consumption, Meter, MeterPage, Transformer
from .portal_client import PortalClient, PortalError
from .store import Store

app = FastAPI(
    title="Urja Meter API",
    description="Clean API over the legacy Urja Meter Ops portal.",
    version="0.1.0",
)
store = Store(PortalClient())


@app.exception_handler(PortalError)
def portal_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=502, content={"detail": f"Upstream portal error: {exc}"})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/meters", response_model=MeterPage)
def list_meters(
    q: Optional[str] = Query(None, description="Substring of meter id or serial number"),
    status: Optional[str] = Query(None, description="Installed | Faulty | Decommissioned"),
    make: Optional[str] = None,
    dt_code: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items = list(store.meters().values())
    if q:
        ql = q.lower()
        items = [m for m in items if ql in m.meter_id.lower() or ql in m.serial_no.lower()]
    if status:
        items = [m for m in items if m.install_status.lower() == status.lower()]
    if make:
        items = [m for m in items if m.make.lower() == make.lower()]
    if dt_code:
        items = [m for m in items if m.dt_code == dt_code]
    total = len(items)
    start = (page - 1) * page_size
    return MeterPage(items=items[start:start + page_size], total=total,
                     page=page, page_size=page_size)


@app.get("/meters/{meter_id}", response_model=Meter)
def get_meter(meter_id: str):
    meter = store.meters().get(meter_id)
    if not meter:
        raise HTTPException(404, f"Meter {meter_id} not found")
    return meter


@app.get("/meters/{meter_id}/consumption", response_model=Consumption)
def get_consumption(meter_id: str):
    if meter_id not in store.meters():
        raise HTTPException(404, f"Meter {meter_id} not found")
    return store.consumption(meter_id)


@app.get("/transformers", response_model=list[Transformer])
def list_transformers():
    return store.transformers()