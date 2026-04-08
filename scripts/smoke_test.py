import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me")
API_KEY = os.getenv("API_KEY", "")
TEMPLATE_NAME = os.getenv("SMOKE_TEMPLATE_NAME", "sample_legacy_records")


def request(url: str, method: str = "GET", data: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None):
    req = urllib.request.Request(url=url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.status, response.read().decode("utf-8")


def main() -> int:
    try:
        status, body = request(f"{BASE_URL}/health")
        print("health:", status, body)

        payload = {
            "hostname": "polaris-smoke-host",
            "ipaddress": "192.168.1.10",
            "area": "tokyo",
            "building": "dc-a",
            "category": "server",
            "model": "test-model",
            "ping_test_result": "success",
            "exec_result": "ok",
        }
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["X-API-Key"] = API_KEY
        status, body = request(
            f"{BASE_URL}/api/v1/records/{TEMPLATE_NAME}",
            method="POST",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
        )
        print("post:", status, body)

        status, body = request(f"{BASE_URL}/api/v1/records?template_name={TEMPLATE_NAME}")
        print("list:", status, body)

        auth = base64.b64encode(f"{ADMIN_USERNAME}:{ADMIN_PASSWORD}".encode("utf-8")).decode("ascii")
        status, _ = request(
            f"{BASE_URL}/settings/mappings?template_name={TEMPLATE_NAME}",
            headers={"Authorization": f"Basic {auth}"},
        )
        print("settings:", status)
        return 0
    except urllib.error.URLError as exc:
        print(f"smoke test failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
