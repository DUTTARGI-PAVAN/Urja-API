from datetime import datetime
import threading
import time
from typing import Callable, Optional

from .models import Consumption, Hierarchy, Location, Meter, Node, Reading, Transformer
from .portal_client import PortalClient

LEVELS = ["zone", "circle", "division", "subdivision", "substation", "feeder", "dt"]


def _blank_to_none(v):
    if v is None:
        return None
    v = str(v).strip()
    return v or None


def _to_float(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_timestamp(v) -> datetime:
    if isinstance(v, datetime):
        return v
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(v, fmt)
        except (ValueError, TypeError):
            continue
    return datetime.fromisoformat(v)


def to_meter(raw: dict) -> Meter:
    h = raw.get("hierarchy") or {}
    hierarchy = Hierarchy(**{
        lv: Node(code=_blank_to_none((h.get(lv) or {}).get("code")),
                 name=_blank_to_none((h.get(lv) or {}).get("name")))
        for lv in LEVELS
    })
    return Meter(
        meter_id=raw["meterId"],
        serial_no=raw["serialNo"],
        make=raw["make"],
        phase_type=raw["phaseType"],
        install_status=raw["installStatus"],
        install_type=raw["installType"],
        build=raw["build"],
        dt_code=raw["dtCode"],
        hierarchy=hierarchy,
        location=Location(latitude=raw["geo"]["lat"], longitude=raw["geo"]["lng"]),
    )


def to_reading(raw: dict) -> Reading:
    return Reading(
        timestamp=_parse_timestamp(raw["timestamp"]),
        kwh=_to_float(raw.get("kwh")),
        kvah=_to_float(raw.get("kvah")),
        volt_r=_to_float(raw.get("voltR")),
    )


def to_transformer(raw: dict) -> Transformer:
    return Transformer(
        code=raw["code"],
        name=raw.get("name"),
        feeder_code=raw.get("feederCode"),
        capacity_kva=_to_float(raw.get("capacityKva")),
    )


class TTLCache:
    """Holds one value; refreshes after `ttl` seconds. Thread-safe."""

    def __init__(self, loader: Callable, ttl: float):
        self._loader, self._ttl = loader, ttl
        self._value, self._loaded_at = None, 0.0
        self._lock = threading.Lock()

    def get(self):
        with self._lock:
            if self._value is None or time.time() - self._loaded_at > self._ttl:
                self._value = self._loader()
                self._loaded_at = time.time()
            return self._value


class Store:
    def __init__(self, client: PortalClient, ttl_seconds: float = 300):
        self.client = client
        self._meters = TTLCache(
            lambda: {m.meter_id: m for m in map(to_meter, client.export_all())}, ttl_seconds
        )
        self._dts = TTLCache(
            lambda: [to_transformer(r) for r in client.list_dts()], ttl_seconds
        )

    def meters(self) -> dict[str, Meter]:
        return self._meters.get()

    def transformers(self) -> list[Transformer]:
        return self._dts.get()

    def consumption(self, meter_id: str) -> Consumption:
        raw = self.client.get_energy(meter_id)
        readings = sorted((to_reading(r) for r in raw), key=lambda r: r.timestamp)
        return Consumption(meter_id=meter_id, readings=readings)