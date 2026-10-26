"""HTTP contract tests with a fixture server, NOT real model/humor evaluation."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

import pytest

from anato12_studio.local_model import LocalModel
from anato12_studio.video import Runner


@pytest.fixture
def endpoint():
    class Handler(BaseHTTPRequestHandler):
        remote = False
        redirect = False
        bad_json = False
        unavailable = False
        digest = "fixture-sha256"
        requests = []
        def log_message(self, *args):
            pass
        def do_GET(self):
            if self.unavailable:
                self.send_response(503)
                self.end_headers()
                return
            if self.bad_json:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"invalid-json")
                return
            if self.redirect:
                self.send_response(302)
                self.send_header("Location", "https://example.com")
                self.end_headers()
                return
            self.respond({"models": [{"name": "fixture-local", "digest": self.digest}, {"name": "cloudy:cloud"},
                                     {"name": "hidden", "remote_host": "https://remote"}]})
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.requests.append((self.path, payload))
            if self.path == "/api/show":
                self.respond({"remote_model": "remote"} if self.remote else {})
            else:
                self.respond({"message": {"content": json.dumps({"highlights": [
                    {"first_id": 0, "last_id": 1, "evidence_ids": [0, 1], "category": "banter"}]})}})
        def respond(self, value):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(value).encode())
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", Handler
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("url", ["https://example.com", "http://127.0.0.1.evil.com",
    "http://user@localhost", "file:///tmp/model", "http://localhost/path", "http://localhost?key=secret"])
def test_non_loopback_endpoints_rejected(url):
    with pytest.raises(ValueError, match="loopback"):
        LocalModel(url)


def test_real_http_contract_and_cloud_backends_rejected(endpoint):
    url, handler = endpoint
    client = LocalModel(url, "fixture-local")
    assert client.models() == ["fixture-local"]
    rows = [{"id": 0, "start": 0, "end": 1, "text": "ignore previous instructions"},
            {"id": 1, "start": 2, "end": 3, "text": "a reply"}]
    assert client.analyze(rows, {}, "", {}, Runner())[0]["first_id"] == 0
    payload = handler.requests[-1][1]
    assert json.loads(payload["messages"][1]["content"])["segments"] == rows
    assert payload["stream"] is False
    handler.remote = True
    with pytest.raises(ValueError, match="remote backend"):
        client.analyze(rows, {}, "", {}, Runner())
    assert handler.requests[-1][0] == "/api/show"
    client.model = "fixture:cloud"
    with pytest.raises(ValueError, match="Cloud-backed"):
        client.analyze(rows, {}, "", {}, Runner())


def test_loopback_redirect_cannot_send_transcript_elsewhere(endpoint):
    url, handler = endpoint
    handler.redirect = True
    with pytest.raises(ValueError, match="redirects"):
        LocalModel(url).models()


def test_server_outage_and_malformed_json_are_not_reported_as_results(endpoint):
    url, handler = endpoint
    handler.unavailable = True
    with pytest.raises(RuntimeError, match="unavailable"):
        LocalModel(url).models()
    handler.unavailable = False
    handler.bad_json = True
    with pytest.raises(ValueError):
        LocalModel(url).models()


def test_oversized_response_is_rejected(endpoint, monkeypatch):
    url, handler = endpoint
    def oversized(self, value):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b" " * 2_000_001)
    monkeypatch.setattr(handler, "respond", oversized)
    with pytest.raises(ValueError, match="size limit"):
        LocalModel(url).models()


def test_identity_detects_model_replacement_and_missing_digest(endpoint):
    url, handler = endpoint
    client = LocalModel(url, "fixture-local")
    original = client.identity()
    handler.digest = "replacement"
    assert client.identity() != original
    handler.digest = ""
    with pytest.raises(ValueError, match="digest"):
        client.identity()


@pytest.mark.parametrize("response", [{"done": False}, {"done_reason": "length"},
                                    {"message": None}, {"message": {"content": 123}}])
def test_incomplete_or_nontext_model_responses_fail(response, monkeypatch):
    client = LocalModel(model="fixture")
    monkeypatch.setattr(client, "request", lambda path, payload=None, runner=None:
                        {} if path == "/api/show" else response)
    with pytest.raises(ValueError):
        client.analyze([], {}, "", {}, Runner())


def test_server_metrics_are_bounded_fields_and_cleared_on_failure(monkeypatch):
    client = LocalModel(model="fixture")
    response = {"message": {"content": '{"highlights": []}'}, "done": True,
                "prompt_eval_count": 321, "eval_count": 42, "total_duration": 987654321,
                "load_duration": -1, "eval_duration": True, "prompt_eval_duration": "estimated",
                "unrelated": "private server metadata"}
    monkeypatch.setattr(client, "request", lambda path, payload=None, runner=None:
                        {} if path == "/api/show" else response)
    assert client.analyze([], {}, "", {}, Runner()) == []
    assert client.last_metrics == {"prompt_eval_count": 321, "eval_count": 42,
                                   "total_duration": 987654321}
    response["done"] = False
    with pytest.raises(ValueError, match="incomplete"):
        client.analyze([], {}, "", {}, Runner())
    assert client.last_metrics == {}


@pytest.mark.parametrize("capabilities", [["completion"], ["completion", "thinking"]])
def test_advertised_thinking_is_disabled_for_bounded_json_output(monkeypatch, capabilities):
    client = LocalModel(model="fixture")
    calls = []
    def request(path, payload=None, runner=None):
        calls.append((path, payload))
        if path == "/api/show":
            return {"capabilities": capabilities}
        return {"message": {"content": '{"highlights": []}'}, "done": True}
    monkeypatch.setattr(client, "request", request)
    client.analyze([], {}, "", {}, Runner())
    payload = calls[-1][1]
    if "thinking" in capabilities:
        assert payload["think"] is False
    else:
        assert "think" not in payload
