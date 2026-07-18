"""Dependency-light HTTP server for the live demo and static interface."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
import time
from collections import defaultdict, deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from agent import AgentError
from demo_service import DemoService, FlowError, FlowNotFound
from human_gate import HumanGateError


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
MAX_BODY_BYTES = 64 * 1024
START_LIMIT = 12
START_WINDOW_SECONDS = 3600


def load_dotenv(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


class DemoHandler(BaseHTTPRequestHandler):
    service: DemoService
    starts_by_ip: dict[str, deque[float]] = defaultdict(deque)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "agent_mode": os.environ.get("MARGELIS_AGENT_MODE", "fixture"),
                    "synthetic_data_only": True,
                },
            )
            return
        match = re.fullmatch(r"/api/flow/([0-9a-f-]+)(?:/(passport|verify))?", path)
        if match:
            flow_id, action = match.groups()
            try:
                if action == "passport":
                    result = self.service.passport(flow_id)
                elif action == "verify":
                    result = self.service.verify(flow_id)
                else:
                    result = self.service.get_flow(flow_id)
                self._json(HTTPStatus.OK, result)
            except FlowNotFound as exc:
                self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            return
        self._serve_static(path)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/flow/start":
                if not self._allow_start():
                    self._json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Demo start limit reached"})
                    return
                self._json(HTTPStatus.CREATED, self.service.start_flow())
                return

            match = re.fullmatch(r"/api/flow/([0-9a-f-]+)/(correct|rerun|tamper-check)", path)
            if not match:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Route not found"})
                return
            flow_id, action = match.groups()
            body = self._read_json()
            if action == "correct":
                result = self.service.correct_and_approve(
                    flow_id,
                    corrected_text=str(body.get("corrected_text", "")),
                    actor_id=str(body.get("actor_id", "Human reviewer")),
                )
            elif action == "rerun":
                result = self.service.run_regression(flow_id)
            else:
                result = self.service.tamper_check(flow_id)
            self._json(HTTPStatus.OK, result)
        except FlowNotFound as exc:
            self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
        except (FlowError, HumanGateError, ValueError) as exc:
            self._json(HTTPStatus.CONFLICT, {"error": str(exc)})
        except AgentError as exc:
            self._json(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
        except json.JSONDecodeError:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})

    def _read_json(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length", "0")
        length = int(raw_length)
        if length > MAX_BODY_BYTES:
            raise ValueError("Request body is too large")
        if length == 0:
            return {}
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _serve_static(self, path: str) -> None:
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        candidate = (WEB_ROOT / relative).resolve()
        if WEB_ROOT.resolve() not in candidate.parents and candidate != WEB_ROOT.resolve():
            self._json(HTTPStatus.NOT_FOUND, {"error": "File not found"})
            return
        if not candidate.is_file():
            self._json(HTTPStatus.NOT_FOUND, {"error": "File not found"})
            return
        content = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _allow_start(self) -> bool:
        ip = self.client_address[0]
        now = time.monotonic()
        bucket = self.starts_by_ip[ip]
        while bucket and now - bucket[0] > START_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= START_LIMIT:
            return False
        bucket.append(now)
        return True

    def _json(self, status: HTTPStatus, payload: Any) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stdout.write("demo-server " + (format % args) + "\n")


def main() -> None:
    load_dotenv()
    service = DemoService()
    DemoHandler.service = service
    host = os.environ.get("MARGELIS_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), DemoHandler)
    print(
        f"Margelis Governor demo running at http://{host}:{port} "
        f"in {os.environ.get('MARGELIS_AGENT_MODE', 'fixture')} mode"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
