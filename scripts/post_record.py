import argparse
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
API_KEY = os.getenv("API_KEY", "")


def request(url: str, method: str = "GET", data: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None):
    req = urllib.request.Request(url=url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.status, response.read().decode("utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="テンプレートで追加した API に対して JSON レコードを登録するスクリプト",
    )
    parser.add_argument(
        "template_name",
        help="登録先テンプレート名。API 名でも指定可能です。",
    )
    parser.add_argument(
        "json_file",
        help="POST する JSON ファイルのパス。",
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL,
        help=f"接続先ベース URL。既定値: {BASE_URL}",
    )
    parser.add_argument(
        "--api-key",
        default=API_KEY,
        help="API キー。未設定時はヘッダを付与しません。",
    )
    return parser.parse_args()


def load_payload(json_file: str) -> dict:
    path = Path(json_file)
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("JSON ファイルのルート要素は object である必要があります。")
    return loaded


def main() -> int:
    args = parse_args()
    try:
        payload = load_payload(args.json_file)
        headers = {"Content-Type": "application/json"}
        if args.api_key:
            headers["X-API-Key"] = args.api_key
        status, body = request(
            f"{args.base_url}/api/v1/records/{args.template_name}",
            method="POST",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
        )
        print("status:", status)
        print(body)
        return 0
    except FileNotFoundError:
        print(f"JSON file not found: {args.json_file}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"request failed: {exc.code} {detail}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
