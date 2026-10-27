"""Bounded, cancellable HTTP for the explicitly selected loopback model server."""
import http.client
import json
import socket
import threading
import time
import urllib.parse


def request_json(base, path, payload=None, runner=None, timeout=60, headers=None, service="Local model"):
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
    if timeout <= 0:
        raise ValueError("Local-model request timeout must be positive.")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        if (set(headers) != {"Authorization"} or not isinstance(headers["Authorization"], str)
                or "\r" in headers["Authorization"] or "\n" in headers["Authorization"]):
            raise ValueError("Invalid local authorization header.")
        request_headers.update(headers)
    connection = kind(parsed.hostname, parsed.port, timeout=min(5, timeout))
    deadline = time.monotonic() + timeout
    done = threading.Event()
    values, errors, active_socket = [], [], []

    def abort():
        # A socket shutdown usually interrupts recv immediately. On Windows an
        # HTTPResponse can retain a buffered reader after Connection: close, so
        # the caller also stops waiting independently of the socket wake-up.
        sock = active_socket[0] if active_socket else connection.sock
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
        connection.close()

    def transfer():
        try:
            connection.connect()
            active_socket.append(connection.sock)
            connection.sock.settimeout(timeout)
            connection.request("GET" if payload is None else "POST", path, body, request_headers)
            with connection.getresponse() as response:
                if 300 <= response.status < 400:
                    raise ValueError("Local-model redirects are not allowed.")
                if response.status != 200:
                    detail = ""
                    try:
                        problem = json.loads(response.read(4096))
                        if isinstance(problem, dict) and isinstance(problem.get("error"), str):
                            detail = problem["error"][:400] + " "
                    except (ValueError, OSError):
                        pass
                    raise RuntimeError(f"{service} is unavailable: HTTP {response.status}. "
                                       + detail
                                       + ("Start Ollama and select an installed model." if service == "Local model"
                                          else "Check that the local service is running and the API key is current."))
                data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise ValueError("Local-model response exceeded the size limit.")
            value = json.loads(data)
            if not isinstance(value, dict):
                raise ValueError("Local-model response must be a JSON object.")
            values.append(value)
        except Exception as error:
            errors.append(error)
        finally:
            done.set()

    worker = threading.Thread(target=transfer, daemon=True)
    worker.start()
    try:
        while not done.wait(.05):
            if runner:
                runner.check()
            if time.monotonic() >= deadline:
                raise RuntimeError(f"{service} request timed out. Try a smaller installed model "
                                   "or shorter dialogue sections; completed windows remain cached.")
        if runner:
            runner.check()
        if errors:
            error = errors[0]
            if isinstance(error, (OSError, http.client.HTTPException)):
                if isinstance(error, TimeoutError) or time.monotonic() >= deadline:
                    raise RuntimeError(f"{service} request timed out. Try a smaller installed model "
                                       "or shorter dialogue sections; completed windows remain cached.") from error
                raise RuntimeError(f"{service} is unavailable: {error}. "
                                   + ("Start Ollama and select an installed model." if service == "Local model"
                                      else "Start the local service and try again.")) from error
            raise error
        return values[0]
    finally:
        abort()
