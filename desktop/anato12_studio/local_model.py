"""Explicit loopback-only Ollama adapter. Transcript text is data, not instructions."""
import json
import hashlib
import urllib.parse
from .model_context import checked_messages, CONTEXT_TOKENS, OUTPUT_TOKENS
from .local_transport import request_json


class LocalModel:
    def __init__(self, base="http://127.0.0.1:11434", model=""):
        parsed = urllib.parse.urlsplit(base)
        if (parsed.scheme not in ("http", "https") or parsed.hostname not in ("127.0.0.1", "localhost", "::1")
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/")):
            raise ValueError("Local model URL must be a loopback address, e.g. http://127.0.0.1:11434. "
                             "Cloud integrations are not enabled.")
        self.base, self.model = base.rstrip("/"), model
        self.last_metrics = {}

    def request(self, path, payload=None, runner=None):
        return request_json(self.base, path, payload, runner, timeout=300 if path == "/api/chat" else 60)

    def models(self, runner=None):
        return [m["name"] for m in self.catalog(runner)
                if not self.cloud_name(m["name"]) and not m.get("remote_host") and not m.get("remote_model")]

    def catalog(self, runner=None):
        entries = self.request("/api/tags", runner=runner).get("models")
        if not isinstance(entries, list) or any(not isinstance(m, dict) or
                not isinstance(m.get("name"), str) for m in entries):
            raise ValueError("The local server returned an invalid model list.")
        return entries

    def identity(self, runner=None):
        """Resolve the actual installed weights before accepting cached responses."""
        if runner:
            runner.check()
        if not self.model or self.cloud_name(self.model):
            raise ValueError("Choose a downloaded local model; cloud-backed models are not enabled.")
        entry = next((m for m in self.catalog(runner) if m["name"] == self.model), None)
        if runner:
            runner.check()
        if not entry:
            raise ValueError("The selected model is no longer installed. Connect and select a model again.")
        if entry.get("remote_host") or entry.get("remote_model"):
            raise ValueError("This model declares a remote backend.")
        digest = entry.get("digest")
        if not isinstance(digest, str) or not digest.strip():
            raise ValueError("The server did not report a model digest; cached analysis cannot be verified.")
        details = self.request("/api/show", {"model": self.model}, runner)
        if runner:
            runner.check()
        if details.get("remote_host") or details.get("remote_model"):
            raise ValueError("This model declares a remote backend. Only downloaded local models are enabled.")
        config = {k: details.get(k) for k in ("template", "parameters", "system", "model_info", "capabilities")}
        return {"digest": digest, "configuration": hashlib.sha256(
            json.dumps(config, sort_keys=True).encode()).hexdigest()}

    @staticmethod
    def cloud_name(name):
        return name.casefold().endswith(("-cloud", ":cloud"))

    def analyze(self, rows, callbacks, query, preferences, runner):
        self.last_metrics = {}
        if not self.model:
            raise ValueError("Connect to Ollama and select an installed model first.")
        runner.check()
        if self.cloud_name(self.model):
            raise ValueError("Cloud-backed Ollama models are not enabled.")
        messages = checked_messages(rows, callbacks, query, preferences)
        details = self.request("/api/show", {"model": self.model}, runner)
        if details.get("remote_host") or details.get("remote_model"):
            raise ValueError("This model declares a remote backend. Only downloaded local models are enabled.")
        payload = {"model": self.model, "stream": False, "format": "json",
                   "options": {"temperature": .1, "num_ctx": CONTEXT_TOKENS, "num_predict": OUTPUT_TOKENS},
                   "messages": messages}
        capabilities = details.get("capabilities") or []
        if not isinstance(capabilities, list) or any(not isinstance(c, str) for c in capabilities):
            raise ValueError("The local server returned invalid model capabilities. Reconnect or update Ollama.")
        if "thinking" in capabilities:
            # Keep the bounded output budget for the review JSON. This is local
            # model inference behavior, unrelated to the user's Codex setting.
            payload["think"] = False
        response = self.request("/api/chat", payload, runner)
        runner.check()
        if response.get("done") is False or response.get("done_reason") == "length":
            raise ValueError("The model response was incomplete. Try a shorter dialogue window or another model.")
        message = response.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("The model response did not contain textual message content.")
        value = json.loads(message["content"])
        if not isinstance(value, dict) or not isinstance(value.get("highlights"), list):
            raise ValueError("The model did not return the expected highlight schema.")
        # Server-reported measurements, not estimates of quality or GPU usage.
        self.last_metrics = {key: response[key] for key in (
            "total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration",
            "eval_count", "eval_duration")
            if type(response.get(key)) is int and response[key] >= 0}
        return value["highlights"][:4]
