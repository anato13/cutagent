"""Exercise cancellation during real stalled loopback HTTP reads."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time

import pytest

from anato12_studio.local_transport import request_json
from anato12_studio.local_model import LocalModel
from anato12_studio.video import Cancelled, Runner


@pytest.fixture(params=["headers", "body"])
def stalled_endpoint(request):
    entered, release = threading.Event(), threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            try:
                if request.param == "body":
                    self.send_response(200)
                    self.send_header("Content-Length", "2")
                    self.end_headers()
                    self.wfile.write(b"{")
                    self.wfile.flush()
                entered.set()
                release.wait(5)
                if request.param == "headers":
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"{}")
                else:
                    self.wfile.write(b"}")
            except (BrokenPipeError, ConnectionResetError):
                pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", entered
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        thread.join()


def test_cancel_interrupts_headers_and_partial_body(stalled_endpoint):
    url, entered = stalled_endpoint
    runner, errors = Runner(), []
    def call():
        try:
            LocalModel(url).models(runner)
        except Exception as error:
            errors.append(error)
    thread = threading.Thread(target=call, daemon=True)
    thread.start()
    try:
        assert entered.wait(2)
        tick = time.monotonic()
        runner.cancel()
        thread.join(2)
        assert not thread.is_alive()
        assert time.monotonic() - tick < 1
        assert len(errors) == 1 and isinstance(errors[0], Cancelled)
    finally:
        runner.cancel()
        thread.join(2)


def test_total_deadline_interrupts_stalled_response(stalled_endpoint):
    url, _ = stalled_endpoint
    tick = time.monotonic()
    with pytest.raises(RuntimeError, match="timed out"):
        request_json(url, "/api/tags", timeout=.2)
    assert time.monotonic() - tick < 1


def test_cancelled_request_does_not_contact_server(stalled_endpoint):
    url, entered = stalled_endpoint
    runner = Runner()
    runner.cancel()
    with pytest.raises(Cancelled):
        request_json(url, "/api/tags", runner=runner)
    assert not entered.is_set()


@pytest.mark.parametrize("url", ["http://example.com", "http://localhost@evil.test", "http://localhost/path"])
def test_transport_rejects_remote_destination(url):
    with pytest.raises(ValueError, match="loopback"):
        request_json(url, "/api/tags")
