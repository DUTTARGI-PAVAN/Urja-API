import hashlib
import hmac
import os
import threading
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

PORTAL_URL = os.getenv("PORTAL_URL", "https://urja-ops.flockenergy.tech")
USERNAME = os.getenv("PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD")
MAX_PAGES = 200  # safety cap so a pagination bug can't loop forever


class PortalError(Exception):
    """The portal failed, or returned something we can't use."""


class PortalClient:
    def __init__(self):
        # follow_redirects=False so we can SEE a redirect-to-login (session expiry)
        self._http = httpx.Client(base_url=PORTAL_URL, timeout=15, follow_redirects=False)
        self._lock = threading.Lock()
        self._logged_in = False

    # ---------- auth ----------
    def login(self):
        with self._lock:
            try:
                resp = self._http.post(
                    "/login",
                    data={"email": USERNAME, "password": PASSWORD},
                    headers={
                        "Origin": PORTAL_URL,
                        "Referer": f"{PORTAL_URL}/login",
                        "Accept": "application/json",
                        "x-sveltekit-action": "true",
                    },
                )
                body = resp.json()
            except (httpx.HTTPError, ValueError) as e:
                raise PortalError(f"login request failed: {e}") from e
            if body.get("type") != "redirect":
                raise PortalError(f"login rejected: {body.get('type')}")
            self._logged_in = True

    @staticmethod
    def _session_expired(resp: httpx.Response) -> bool:
        if resp.status_code == 401:
            return True
        if resp.is_redirect and "/login" in resp.headers.get("location", ""):
            return True
        return False

    # ---------- generic request with re-login ----------
    def _get(self, path, retry=True, **kwargs):
        if not self._logged_in:
            self.login()
        try:
            resp = self._http.get(path, **kwargs)
        except httpx.HTTPError as e:
            raise PortalError(f"GET {path} failed: {e}") from e

        if self._session_expired(resp):
            if not retry:
                raise PortalError("session expired and re-login did not help")
            self._logged_in = False
            return self._get(path, retry=False, **kwargs)

        if resp.status_code == 404:
            raise PortalError(f"404 {path}")
        if resp.status_code >= 400:
            raise PortalError(f"GET {path} -> {resp.status_code}")
        try:
            return resp.json()
        except ValueError as e:
            raise PortalError(f"GET {path} returned non-JSON") from e

    # ---------- data ----------
    def get_energy(self, meter_id: str):
        return self._get(f"/portal/meters/{meter_id}/energy")["data"]

    def list_dts(self):
        rows, page = [], 1
        while page <= MAX_PAGES:
            resp = self._get("/portal/dts", params={"page": page})
            batch = resp["data"]
            if not batch:
                break
            rows.extend(batch)
            if len(rows) >= resp["total"]:
                break
            page += 1
        return rows

    def export_all(self):
        """Bulk path: signed export, all pages."""
        secret = self._get("/portal/keys")["data"]["signingSecret"]
        rows, page = [], 1
        while page <= MAX_PAGES:
            ts = str(int(time.time()))
            to_sign = f"GET\n/portal/export\npage={page}\n{ts}"
            sig = hmac.new(secret.encode(), to_sign.encode(), hashlib.sha256).hexdigest()
            resp = self._get(
                "/portal/export",
                params={"page": page},
                headers={"x-timestamp": ts, "x-signature": sig},
            )
            batch = resp["data"]
            if not batch:
                break
            rows.extend(batch)
            if len(rows) >= resp["total"]:
                break
            page += 1
        return rows