from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Node(BaseModel):
    code: Optional[str] = None  # blank codes in the portal become null
    name: Optional[str] = None


class Hierarchy(BaseModel):
    zone: Node
    circle: Node
    division: Node
    subdivision: Node
    substation: Node
    feeder: Node
    dt: Node


class Location(BaseModel):
    latitude: float
    longitude: float


class Meter(BaseModel):
    meter_id: str
    serial_no: str
    make: str
    phase_type: str          # "single" | "three"
    install_status: str      # "Installed" | "Faulty" | "Decommissioned"
    install_type: str        # "Whole Current" | "CT Operated"
    build: str               # "legacy" | "v2"
    dt_code: str
    hierarchy: Hierarchy
    location: Location


class MeterPage(BaseModel):
    items: list[Meter]
    total: int
    page: int
    page_size: int


class Reading(BaseModel):
    timestamp: datetime
    kwh: Optional[float] = None
    kvah: Optional[float] = None
    volt_r: Optional[float] = None


class Consumption(BaseModel):
    meter_id: str
    readings: list[Reading]


class Transformer(BaseModel):
    code: str
    name: Optional[str] = None
    feeder_code: Optional[str] = None
    capacity_kva: Optional[float] = None