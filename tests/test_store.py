from app.store import to_meter, to_reading


def raw_meter(**overrides):
    base = {
        "meterId": "J1", "serialNo": "S1", "make": "Genus", "phaseType": "single",
        "installStatus": "Installed", "installType": "CT Operated",
        "build": "legacy", "dtCode": "DT-001",
        "hierarchy": {lv: {"name": lv.title(), "code": f"{lv[:2].upper()}-01"}
                        for lv in ["zone", "circle", "division", "subdivision",
                                    "substation", "feeder", "dt"]},
        "geo": {"lat": 26.9, "lng": 75.8},
    }
    base.update(overrides)
    return base


def test_to_meter_maps_fields():
    m = to_meter(raw_meter())
    assert m.meter_id == "J1"
    assert m.location.latitude == 26.9 and m.location.longitude == 75.8


def test_blank_hierarchy_code_becomes_none_but_keeps_name():
    raw = raw_meter()
    raw["hierarchy"]["circle"] = {"name": "Circle 6", "code": ""}
    m = to_meter(raw)
    assert m.hierarchy.circle.code is None
    assert m.hierarchy.circle.name == "Circle 6"


def test_reading_strings_become_floats():
    r = to_reading({"timestamp": "2026-10-26T12:00:00Z", "kwh": "142.50",
                    "kvah": "148.20", "voltR": "231.4"})
    assert r.kwh == 142.5 and r.volt_r == 231.4


def test_reading_bad_value_becomes_none():
    r = to_reading({"timestamp": "2026-10-26T12:00:00Z", "kwh": "n/a"})
    assert r.kwh is None
