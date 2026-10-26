"""Bounded, cancellable HTTP for the explicitly selected loopback model server."""
import http.client
import json
import socket
import threading
import time
import urllib.parse


def request_json(base, path, payload=None, runner=None, timeout=60):
    parsed = urllib.parse.urlsplit(base)
    if (parsed.scheme not in ("http", "https") or
            parsed.hostname not in ("127.0.0.1", "localhost", "::1") or
            parsed.username or parsed.password or parsed.query or parsed.fragment or
            parsed.path not in ("", "/")):
        raise ValueError("Local model transport requires a loopback URL.")
    if not path.startswith("/api/") or "\r" in path or "\n" in path:
        raise ValueError("Invalid local-model API path.")
    if runner:
        runner.check()
    kind = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    connection = kind(parsed.hostname, parsed.port, timeout=min(5, timeout))
    finished, expired = threading.Event(), threading.Event()
    active_socket = []
    deadline = time.monotonic() + timeout

    def watch():
        while not finished.wait(.05):
            cancelled = runner is not None and runner.stopped.is_set()
            if not cancelled and time.monotonic() < deadline:
                continue
            if not cancelled:
                expired.set()
            # Keep the connected socket: HTTPConnection may clear its reference
            # after receiving a Connection: close header while the body is pending.
            if active_socket:
                try:
                    active_socket[0].shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            return

    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        connection.connect()
        active_socket.append(connection.sock)
        connection.sock.settimeout(timeout)
        if runner:
            runner.check()
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        connection.request("GET" if payload is None else "POST", path, body,
                           {"Content-Type": "application/json"})
        with connection.getresponse() as response:
            if runner:
                runner.check()
            if 300 <= response.status < 400:
                raise ValueError("Local-model redirects are not allowed.")
            if response.status != 200:
                raise RuntimeError(f"Local model is unavailable: HTTP {response.status}. "
                                   "Start Ollama and select an installed model.")
            data = response.read(2_000_001)
        if runner:
            runner.check()
        if expired.is_set():
            raise TimeoutError()
        if len(data) > 2_000_000:
            raise ValueError("Local-model response exceeded the size limit.")
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError("Local-model response must be a JSON object.")
        return value
    except (OSError, http.client.HTTPException) as error:
        if runner:
            runner.check()
        if expired.is_set() or isinstance(error, TimeoutError):
            raise RuntimeError("Local-model request timed out. Try a smaller installed model "
                               "or shorter dialogue sections; completed windows remain cached.") from error
        raise RuntimeError(f"Local model is unavailable: {error}. "
                           "Start Ollama and select an installed model.") from error
    finally:
        finished.set()
        connection.close()
        watcher.join(timeout=1)
