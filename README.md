# Urja Meter API

A clean, documented RESTful API service built with FastAPI (Python) that interfaces with the legacy "Urja Meter Ops" portal (`https://urja-ops.flockenergy.tech`).

The upstream portal provides no public API and relies on session cookies and internal SvelteKit endpoints. This service handles authentication, session recovery, data normalization, caching, and querying to expose a standard JSON API.

---

## 1. What I Built and How It's Structured

The service sits directly between API consumers and the legacy Urja Meter Ops portal:

```
[ Client / Browser ]
         │
         ▼  (Clean JSON API)
┌────────────────────────────────────────┐
│              FastAPI App               │
│                                        │
│  app/main.py       Routes & Handlers   │
│  app/models.py     Pydantic Schemas    │
│  app/store.py      Normalizer & Cache  │
│  app/portal_client.py Auth & Upstream  │
└────────────────────────────────────────┘
         │
         ▼  (Session Auth & HMAC-SHA256 Signed Export)
[ Legacy Urja Meter Ops Portal ]
```

### Repository Structure
- `app/main.py` — FastAPI application instance, route declarations, query filtering, and upstream error translation.
- `app/portal_client.py` — Portal client handling login, redirect detection, session re-authentication, HMAC-SHA256 signed exports, and pagination safety caps.
- `app/store.py` — In-memory TTL cache, data transformation, and normalization logic.
- `app/models.py` — Pydantic domain models for meters, hierarchy, consumption readings, and transformers.
- `tests/test_store.py` — Unit tests for data mapping and normalization.
- `PROTOCOL.md` — Reverse-engineered network protocol documentation of the legacy portal.
- `openapi.json` — Static OpenAPI 3.1 specification of this service.
- Exploration scripts: `try_export.py`, `analyse.py`, `compare_detail.py`, `check_remaining.py` [keep in repo or move to scripts/: fill in].

---

## 2. Quick Start

### Prerequisites
- Python 3.12 (developed and tested on Python 3.12.10, Windows)
- pip & virtualenv

### Installation & Configuration
1. Clone the repository and navigate into the project directory:
   ```bash
   cd urja-api
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your portal credentials:
   ```env
   PORTAL_URL=https://urja-ops.flockenergy.tech
   PORTAL_USERNAME=your_username
   PORTAL_PASSWORD=your_password
   ```

### Running the Service
Start the Uvicorn development server:
```bash
uvicorn app.main:app --reload
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Raw OpenAPI Spec: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Running Tests
Run the test suite via pytest:
```bash
python -m pytest -q
```
Result: `4 passed`

---

## 3. Sample Request and Response

### Sample 1: Fetch Single Meter (`GET /meters/J100395`)

**Request:**
```bash
curl -X GET "http://localhost:8000/meters/J100395" -H "Accept: application/json"
```

**Response (`200 OK`):**
```json
{
  "meter_id": "J100395",
  "serial_no": "AL42611",
  "make": "Secure",
  "phase_type": "single",
  "install_status": "Installed",
  "install_type": "CT Operated",
  "build": "legacy",
  "dt_code": "DT-036",
  "hierarchy": {
    "zone": {
      "code": "Z-03",
      "name": "Jaipur Zone 3"
    },
    "circle": {
      "code": "C-06",
      "name": "Circle 6"
    },
    "division": {
      "code": "D-06",
      "name": "Division 6"
    },
    "subdivision": {
      "code": "SD-08",
      "name": "Subdivision 8"
    },
    "substation": {
      "code": "SS-18",
      "name": "Substation 18"
    },
    "feeder": {
      "code": "F-008",
      "name": "Feeder 8"
    },
    "dt": {
      "code": "DT-036",
      "name": "Jhotwara DT 36"
    }
  },
  "location": {
    "latitude": 26.988115068203864,
    "longitude": 75.87841832903
  }
}
```

### Sample 2: Filtered Meters (`GET /meters?status=Faulty&page_size=2`)

**Request:**
```bash
curl -X GET "http://localhost:8000/meters?status=Faulty&page_size=2" -H "Accept: application/json"
```

**Response (`200 OK`):**
```json
{
  "items": [
    {
      "meter_id": "J100004",
      "serial_no": "SE65293",
      "make": "Genus",
      "phase_type": "single",
      "install_status": "Faulty",
      "install_type": "CT Operated",
      "build": "v2",
      "dt_code": "DT-005",
      "hierarchy": {
        "zone": {
          "code": "Z-02",
          "name": "Jaipur Zone 2"
        },
        "circle": {
          "code": "C-05",
          "name": "Circle 5"
        },
        "division": {
          "code": "D-05",
          "name": "Division 5"
        },
        "subdivision": {
          "code": "SD-05",
          "name": "Subdivision 5"
        },
        "substation": {
          "code": "SS-05",
          "name": "Substation 5"
        },
        "feeder": {
          "code": "F-005",
          "name": "Feeder 5"
        },
        "dt": {
          "code": "DT-005",
          "name": "Bani Park DT 5"
        }
      },
      "location": {
        "latitude": 26.907425164505934,
        "longitude": 75.72503661059095
      }
    },
    {
      "meter_id": "J100005",
      "serial_no": "HP63682",
      "make": "Allied",
      "phase_type": "three",
      "install_status": "Faulty",
      "install_type": "Whole Current",
      "build": "legacy",
      "dt_code": "DT-006",
      "hierarchy": {
        "zone": {
          "code": "Z-03",
          "name": "Jaipur Zone 3"
        },
        "circle": {
          "code": "C-06",
          "name": "Circle 6"
        },
        "division": {
          "code": "D-06",
          "name": "Division 6"
        },
        "subdivision": {
          "code": "SD-06",
          "name": "Subdivision 6"
        },
        "substation": {
          "code": "SS-06",
          "name": "Substation 6"
        },
        "feeder": {
          "code": "F-006",
          "name": "Feeder 6"
        },
        "dt": {
          "code": "DT-006",
          "name": "Jhotwara DT 6"
        }
      },
      "location": {
        "latitude": 26.84670538836401,
        "longitude": 75.86828425070057
      }
    }
  ],
  "total": 90,
  "page": 1,
  "page_size": 2
}
```

---

## 4. Endpoints

| Method | Endpoint | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | — | Service health check (`{"status": "ok"}`). |
| `GET` | `/meters` | `q`, `status`, `make`, `dt_code`, `page` (default 1), `page_size` (default 20, max 100) | Paginated list of meters matching optional filters. |
| `GET` | `/meters/{meter_id}` | — | Detailed metadata for a single meter. |
| `GET` | `/meters/{meter_id}/consumption` | — | Historical energy consumption readings. |
| `GET` | `/transformers` | — | List of all distribution transformers (DTs). |

### Error Responses
- **404 Not Found:** Returned when requesting an unknown `meter_id` (`{"detail": "Meter <id> not found"}`).
- **502 Bad Gateway:** Returned if an upstream portal call fails (`{"detail": "Upstream portal error: <message>"}`).

---

## 5. Assumptions

- **Authoritative Source:** The export endpoint (`/portal/export`) is treated as the primary authority for meter metadata. All checked meters exhibited 100% agreement between the export and the detail page values.
- **Cache Staleness:** 5 minutes (300 seconds) of cache staleness is acceptable for meter and transformer metadata in operational contexts.
- **Read-Only Portal:** The portal should not be subjected to heavy load or redundant polling. Bulk export data is cached, and exploration scripts sampled or used local caches (`export.json` is gitignored).
- **Non-Unique Hierarchy Codes:** Regional codes are not globally unique across the tree (e.g. division code `D-01` appears under circle `C-01`, `C-03`, and `C-05`). Consequently, individual codes cannot serve as standalone global identifiers.
- [fill in any assumption of mine about consumption units, timezone, etc.]

---

## 6. Design Decisions and Trade-offs

- **Primary Data Ingestion via Signed Export:** Instead of making individual requests per meter to `/meters/[id]/__data.json` and `/portal/meters/[id]/geo`, the service uses the HMAC-SHA256 signed `/portal/export` endpoint. This downloads all 403 meters across 21 pages in bulk, including complete hierarchy and geographical coordinates.
- **Bypassing Detail Page Devalue Parsing:** The detail page uses two distinct nameplate formats tied to the meter build:
  - `legacy` build: an array of `{ parameterName, parameterValue }` objects.
  - `v2` build: a JSON-serialized string inside a `classData` field.
  Both encodings ultimately contain the exact same 6 fields as the export endpoint (`meterId`, `serialNo`, `make`, `phaseType`, `installStatus`, `installType`), while `/geo` returns string coordinates. Using the export avoids reverse-parsing SvelteKit's internal devalue serialization format while providing pre-parsed, structured data.
- **Verification Across Sources:** Verified the export against the detail page and `/geo`: 51 sample meters checked across legacy and v2 for hierarchy agreement (100% match); 5 meters checked against `/geo` (exact match between float coordinates and string coordinates); total count matched (403 search total == 403 export total); all 403 meter DT codes map to valid transformers in `/portal/dts`.
- **In-Memory TTL Caching:** Meter metadata and transformers are cached in-memory with a 300-second TTL. Consumption data is fetched live per request because readings are historical and meter-specific.
- **Local Filtering, Search, and Pagination:** Query filtering (`q`, `status`, `make`, `dt_code`) and pagination are evaluated in-memory over the cached meter list.
- **Session Lifecycle & Expiry Detection:** The portal client uses an HTTP client with `follow_redirects=False` so that authentication redirects (`302 Found` to `/login`) are visible rather than silently followed. If an authenticated request encounters a `401 Unauthorized` or a redirect to `/login`, it automatically re-authenticates once. Failed logins are identified by checking the SvelteKit action response envelope (`type != "redirect"`), since the portal returns HTTP `200` for incorrect credentials.
- **Data Normalization:**
  - Standardized JSON responses to `snake_case`.
  - Converted consumption values (`kwh`, `kvah`, `volt_r`) and geographic coordinates (`latitude`, `longitude`) from strings to floats.
  - Converted blank hierarchy code strings (`""`) to `null` (there are 14 blank code cells in the export dataset across `circle`, `feeder`, and `substation`; blank codes never appear at `zone`, `division`, `subdivision`, or `dt`).
- **Concurrency & Secrets:**
  - Login operations and cache reloads are guarded by threading locks (`threading.Lock`).
  - All portal URLs and credentials are read strictly from environment variables via `python-dotenv`.

---

## 7. What I Intentionally Skipped

- **Hierarchy Tree Endpoint:** Skipped reconstructing a standalone hierarchical tree endpoint because codes are not globally unique and require full path composite keys.
- **Geospatial / Radius Queries:** Skipped nearby-meter geospatial distance calculations.
- **Web Frontend:** Focused entirely on a robust backend API service.
- **Distributed Cache & Persistence:** Skipped Redis/database storage, background cache warmers, and automatic exponential backoff retries.
- **API Consumer Authentication:** Kept the service endpoints open without an extra API key / JWT layer.
- **Consumption Time-Range Filtering:** Returns the raw chronological array provided by the upstream `/energy` endpoint without interval filtering.
- [fill in anything else I skipped]

---

## 8. What I'd Improve with More Time

- [fill in from this list, pick what I truly would do: hierarchy endpoint with full-path identity, stale-while-revalidate cache, retries/backoff, integration tests with a mocked portal, Dockerfile, query by location, data-quality report endpoint, small web dashboard]

### Known Limitations
- **Cold-Start Latency:** The in-memory cache is populated on the first request to `/meters`, taking a few seconds to fetch 21 export pages. A cache TTL expiration similarly blocks one request during reload.
- **Process-Bound Cache:** The in-memory cache is tied to the Python process and is reset on server restarts.
- **Single Session Concurrency:** The portal client uses a single session guarded by a thread lock, which does not scale horizontally across multiple workers.
- **Linear Filtering Performance:** Filtering runs as a linear scan over 403 Python objects. While sub-millisecond for ~400 items, it would require indexing or a database at scale [fill in my estimate, e.g. 100k+].
- **Consumption Units & Names:** Consumption field names and units are derived directly from the portal's `/energy` endpoint: `timestamp` (ISO string), `kwh`, `kvah`, `volt_r` (stored as strings in the upstream response and converted to floats).
- **Unverified Edge Cases:** Signature rejection under altered signing secrets, expired timestamps, upstream session timeout durations, and secret rotation policies were not tested against the production portal.

---

## 9. Where to Find PROTOCOL.md and openapi.json

- **[PROTOCOL.md](file:///d:/urja-api/PROTOCOL.md):** Comprehensive reverse-engineering documentation of the Urja Meter Ops portal architecture, authentication lifecycle, HMAC-SHA256 signing scheme, and internal endpoints.
- **[openapi.json](file:///d:/urja-api/openapi.json):** Full OpenAPI 3.1 specification generated directly from the FastAPI application models.
- **Interactive API Documentation:** Available at runtime at `/docs` (Swagger UI) and `/redoc` (ReDoc).

---

## 10. Reflection

### Assumptions
[my draft]

### Most difficult part and how I got unstuck
[my draft]

### If I had another day
[my draft]

### A mistake I made
[my draft]

### What I'd criticise in my own submission
[my draft]
