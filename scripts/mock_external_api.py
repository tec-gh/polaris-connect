import argparse
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local mock API server for testing Polaris Connect external API integration.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Listen host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=9000, help="Listen port. Default: 9000")
    parser.add_argument("--path", default="/mock", help="Accepted request path. Default: /mock")
    parser.add_argument(
        "--output",
        default=str(Path("data") / "mock_external_api_last_request.json"),
        help="Output JSON path for the latest received request.",
    )
    parser.add_argument("--status", type=int, default=200, help="HTTP status code returned by the mock API.")
    return parser.parse_args()


def build_handler(expected_path: str, output_path: Path, response_status: int):
    class MockExternalApiHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != expected_path:
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "not found", "path": self.path}).encode("utf-8"))
                return

            content_length = int(self.headers.get("Content-Length", "0") or "0")
            raw_body = self.rfile.read(content_length)
            body_text = raw_body.decode("utf-8", errors="replace")
            try:
                body_json: Any = json.loads(body_text)
            except json.JSONDecodeError:
                body_json = None

            payload = {
                "received_at": datetime.utcnow().isoformat() + "Z",
                "method": self.command,
                "path": self.path,
                "headers": {key: value for key, value in self.headers.items()},
                "body_text": body_text,
                "body_json": body_json,
            }
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            print(f"[mock_external_api] POST {self.path} -> {output_path}")
            if body_json is not None:
                print(json.dumps(body_json, ensure_ascii=False, indent=2))
            else:
                print(body_text)

            self.send_response(response_status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            response_body = {
                "message": "received",
                "path": self.path,
                "saved_to": str(output_path),
                "status": response_status,
            }
            self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode("utf-8"))

        def log_message(self, format: str, *args):
            return

    return MockExternalApiHandler


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).resolve()
    handler = build_handler(args.path, output_path, args.status)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"[mock_external_api] listening on http://{args.host}:{args.port}{args.path}")
    print(f"[mock_external_api] saving latest request to {output_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[mock_external_api] stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
