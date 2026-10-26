# Urja Meter Ops Portal - Reverse-Engineered Network Protocol

This document details the reverse-engineered network API and protocol for the **Urja Meter Ops** portal (`https://urja-ops.flockenergy.tech`).

---

## 1. Overview & Architecture

- **Base URL:** `https://urja-ops.flockenergy.tech`
- **Application Framework:** SvelteKit (Vite build) with client-side hydration and SSR components.
- **Styling:** Tailwind CSS.
- **Authentication Model:** Cookie-based session authentication with CSRF origin checks and SvelteKit Form Actions.
- **Data APIs:** REST-style JSON endpoints under `/portal/*` and `/api/*`.
- **Special Security:** HMAC-SHA256 request signing required for export operations (`/portal/export`).

---

## 2. Authentication Protocol

### 2.1 Sign In
- **Route:** `POST /login`
- **Trigger:** SvelteKit Form Action on `/login`.
- **Headers:**
  ```http
  Content-Type: application/x-www-form-urlencoded
  Origin: https://urja-ops.flockenergy.tech
  Referer: https://urja-ops.flockenergy.tech/login
  Accept: application/json
  x-sveltekit-action: true
  ```
- **Request Body (URL-encoded):**
  ```text
  email=<user_email>&password=<user_password>
  ```
- **Responses:**
  - **Success:** HTTP 200 / 303 Redirect to `/(portal)/meters`.
    - Response sets session cookie (HTTP-only) used for subsequent `/portal/*` calls.
  - **Failure (Invalid credentials):** HTTP 200 (SvelteKit action envelope with status 401):
    ```json
    {
      "type": "failure",
      "status": 401,
      "data": "[{\"email\":1,\"error\":2},\"user@example.com\",\"Invalid email or password.\"]"
    }
    ```
  - **CSRF Failure (missing Origin header):**
    - HTTP 403: `Cross-site POST form submissions are forbidden`

### 2.2 Sign Out
- **Route:** `POST /api/auth/sign-out`
- **Headers:** standard fetch headers with session cookie.
- **Behavior:** Invalidates session cookie and redirects client to `/login`.

---

## 3. Navigation & Portal Layout

The authenticated layout (`/(portal)`) loads user context and exposes:
- **Navigation Links:**
  - `/meters` — Meters search and listings
  - `/transformers` — Distribution transformers and export action
- **User Context:** `data.user.name` displayed in the top header.

---

## 4. Meters API

### 4.1 Search & List Meters
- **Endpoint:** `GET /portal/meters/search`
- **Query Parameters:**
  - `q` (string): Search query matching meter identifier or serial number (UI debounces by 250ms).
  - `page` (integer, 1-indexed): Page number (20 items per page).
- **Example Request:**
  ```http
  GET /portal/meters/search?q=&page=1 HTTP/1.1
  Host: urja-ops.flockenergy.tech
  Cookie: <session-cookie>
  ```
- **Response Format:**
  ```json
  {
    "data": [
      {
        "meterId": "MTR-10023",
        "serialNo": "SN-982341",
        "make": "Schneider / L&T",
        "phaseType": "3-Phase",
        "installStatus": "ACTIVE",
        "dtCode": "DT-BLR-04"
      }
    ],
    "total": 120
  }
  ```

### 4.2 Meter Details (`/meters/[id]`)
Navigating to `/meters/[id]` loads:
1. **Server Load (Layout Data):**
   - `meterId`: String identifier.
   - `hierarchy`: Regional hierarchy mapping:
     ```json
     {
       "Zone": "South Zone",
       "Circle": "Bangalore Urban",
       "Division": "Indiranagar",
       "Subdivision": "HAL 2nd Stage",
       "Sub Station": "USS-04",
       "Feeder": "FDR-11",
       "DT": "DT-BLR-04"
     }
     ```
   - `detail`: Nameplate parameters either as:
     - `classData`: JSON string containing `{ "installed_meter": { "key": "value" } }`
     - OR `data`: Array of objects `[ { "parameterName": "Rating", "parameterValue": "10-60A" } ]`

2. **Client-side Async Endpoints:**
   - **Geographic Coordinates:**
     - **Endpoint:** `GET /portal/meters/{meterId}/geo`
     - **Response:**
       ```json
       {
         "data": {
           "latitude": 12.9716,
           "longitude": 77.5946
         }
       }
       ```
   - **Energy & Consumption Readings:**
     - **Endpoint:** `GET /portal/meters/{meterId}/energy`
     - **Response:**
       ```json
       {
         "data": [
           {
             "timestamp": "2026-10-26T12:00:00Z",
             "kwh": "142.50",
             "kvah": "148.20",
             "voltR": "231.4"
           }
         ]
       }
       ```

---

## 5. Distribution Transformers (DTs) API

- **Endpoint:** `GET /portal/dts`
- **Query Parameters:**
  - `page` (integer, 1-indexed, 20 items per page)
- **Response Format:**
  ```json
  {
    "data": [
      {
        "code": "DT-BLR-04",
        "name": "Indiranagar Feeder Transformer 4",
        "feederCode": "FDR-11",
        "capacityKva": 250
      }
    ],
    "total": 35
  }
  ```

---

## 6. Meter Export Protocol (HMAC-SHA256 Signed API)

On the `/transformers` view, clicking **"Export all meters"** triggers a signed export procedure.

### Step 1: Obtain Signing Secret
- **Endpoint:** `GET /portal/keys`
- **Response:**
  ```json
  {
    "data": {
      "signingSecret": "k9f83a...your_secret..."
    }
  }
  ```

### Step 2: Generate HMAC-SHA256 Signature
- **Timestamp:** Current Unix epoch time in seconds (`Math.floor(Date.now() / 1000)`).
- **String to Sign:** Newline-delimited string of:
  1. HTTP Method (`GET`)
  2. Request Path (`/portal/export`)
  3. Query String (`page=1`)
  4. Timestamp string (`<epoch_seconds>`)

  Format:
  ```text
  GET\n/portal/export\npage=1\n<timestamp>
  ```
- **Signing Algorithm:** HMAC with SHA-256 using UTF-8 encoded `signingSecret` as key.
- **Output:** Lowercase hex-encoded digest string.

### Step 3: Execute Export Request
- **Endpoint:** `GET /portal/export?page=1`
- **Request Headers:**
  ```http
  x-timestamp: <timestamp>
  x-signature: <hex_signature>
  ```
- **Response:**
  ```json
  {
    "data": [
      {
        "meterId": "...",
        "serialNo": "...",
        ...
      }
    ],
    "total": 120
  }
  ```
- The frontend initiates a browser download as `meter-export.json`.

---

## 7. Error Handling & Edge Cases

| Scenario | HTTP Status | Response / Behavior |
| :--- | :--- | :--- |
| Missing / Invalid Origin on `/login` | 403 Forbidden | `Cross-site POST form submissions are forbidden` |
| Invalid credentials | 200 OK (SvelteKit Action failure) | `{"type":"failure","status":401,"data":"..."}` |
| Unauthenticated access to `/portal/*` | 401 Unauthorized / 303 Redirect | Redirects to `/login` |
| Missing or invalid `x-signature` / `x-timestamp` | 401 / 403 Forbidden | Export failed |
