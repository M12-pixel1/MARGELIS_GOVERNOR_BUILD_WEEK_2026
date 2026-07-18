import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from agent import FixtureAgent, SYNTHETIC_SAFE_SENTENCE
from demo_service import DemoService
from server import DemoHandler


def call(base_url: str, path: str, method: str = "GET", body: dict | None = None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        base_url + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_http_api_runs_the_complete_fixture_flow(tmp_path) -> None:
    class IsolatedHandler(DemoHandler):
        service = DemoService(data_dir=tmp_path, agent=FixtureAgent())
        starts_by_ip = {}

        def _allow_start(self) -> bool:
            return True

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), IsolatedHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        status, health = call(base_url, "/api/health")
        assert status == 200
        assert health["synthetic_data_only"] is True

        status, flow = call(base_url, "/api/flow/start", "POST", {})
        assert status == 201
        assert flow["stage"] == "BLOCKED"
        flow_id = flow["flow_id"]
        corrected = flow["draft"]["text"]
        for finding in flow["claim_review"]["findings"]:
            corrected = corrected.replace(finding["excerpt"], SYNTHETIC_SAFE_SENTENCE)

        _, flow = call(
            base_url,
            f"/api/flow/{flow_id}/correct",
            "POST",
            {"corrected_text": corrected, "actor_id": "HTTP test reviewer"},
        )
        assert flow["stage"] == "SIGNED"

        _, flow = call(base_url, f"/api/flow/{flow_id}/rerun", "POST", {})
        assert flow["stage"] == "REGRESSION_PASSED"

        _, verification = call(base_url, f"/api/flow/{flow_id}/verify")
        assert verification["valid"] is True

        _, tamper = call(base_url, f"/api/flow/{flow_id}/tamper-check", "POST", {})
        assert tamper["before"]["valid"] is True
        assert tamper["after"]["valid"] is False
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
