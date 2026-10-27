"""Explicit loopback-only Ollama adapter. Transcript text is data, not instructions."""
import json
import hashlib
import base64
import urllib.parse
from .model_context import checked_messages, response_schema, CONTEXT_TOKENS, OUTPUT_TOKENS
from .local_transport import request_json
from .model_policy import context_tokens


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

    def running_models(self, runner=None):
        entries = self.request("/api/ps", runner=runner).get("models", [])
        if not isinstance(entries, list):
            raise ValueError("The local server returned an invalid running-model list.")
        return [{"name": item["name"],
                 "size_vram": item["size_vram"] if type(item.get("size_vram")) is int and
                 item["size_vram"] >= 0 else 0}
                for item in entries if isinstance(item, dict) and isinstance(item.get("name"), str)]

    def unload(self, runner=None):
        """Release this previously selected Studio model before switching."""
        if self.model and not self.cloud_name(self.model):
            self.request("/api/generate", {"model": self.model, "keep_alive": 0}, runner)

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

    def analyze(self, rows, callbacks, query, preferences, runner, focus="standard", excluded_ids=(),
                editing_style="anato"):
        self.last_metrics = {}
        if not self.model:
            raise ValueError("Connect to Ollama and select an installed model first.")
        runner.check()
        if self.cloud_name(self.model):
            raise ValueError("Cloud-backed Ollama models are not enabled.")
        messages = checked_messages(rows, callbacks, query, preferences, focus, excluded_ids,
                                    editing_style)
        details = self.request("/api/show", {"model": self.model}, runner)
        if details.get("remote_host") or details.get("remote_model"):
            raise ValueError("This model declares a remote backend. Only downloaded local models are enabled.")
        payload = {"model": self.model, "stream": False, "format": response_schema(rows, callbacks),
                   "options": {"temperature": .1, "num_ctx": context_tokens(self.model),
                               "num_predict": OUTPUT_TOKENS},
                   "messages": messages}
        capabilities = details.get("capabilities")
        if capabilities is None:
            capabilities = []
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
        if len(value['highlights']) > 4:
            raise ValueError('The model exceeded the four-candidate limit; this response was not cached.')
        # Server-reported measurements, not estimates of quality or GPU usage.
        self.last_metrics = {key: response[key] for key in (
            "total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration",
            "eval_count", "eval_duration")
            if type(response.get(key)) is int and response[key] >= 0}
        return value["highlights"]

    def chat(self, question, history, runner):
        """Bounded, session-only conversation through the selected local model."""
        if not isinstance(question, str) or not question.strip() or len(question) > 2000:
            raise ValueError('Write a question of 1–2000 characters for your local AI.')
        if (not isinstance(history, list) or len(history) > 8 or
                any(not isinstance(m, dict) or m.get('role') not in ('user', 'assistant') or
                    not isinstance(m.get('content'), str) or len(m['content']) > 8000 for m in history) or
                sum(len(m['content']) for m in history) > 8000):
            raise ValueError('Conversation history is invalid; reconnect and try again.')
        self.last_metrics = {}
        self.identity(runner)  # Also refuses missing or remote-backed models.
        messages = [{'role': 'system', 'content': 'You are Anato12 Studio’s local editing assistant. '
                     'Answer clearly. Do not claim to have watched or analyzed video unless it was supplied in this chat.'}]
        messages += history + [{'role': 'user', 'content': question}]
        response = self.request('/api/chat', {'model': self.model, 'stream': False,
            'messages': messages, 'options': {'num_ctx': min(4096, context_tokens(self.model)),
                                              'num_predict': 600},
            **({'keep_alive': '0'} if self.model == 'qwen3:14b' else {})}, runner)
        runner.check()
        if response.get('done') is False or response.get('done_reason') == 'length':
            raise ValueError('The local AI reply was cut off. Ask a shorter question.')
        message = response.get('message')
        content = message.get('content') if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip() or len(content) > 8000:
            raise ValueError('The local AI returned an empty or invalid reply. Try again.')
        self.last_metrics = {key: response[key] for key in (
            'total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration',
            'eval_count', 'eval_duration')
            if type(response.get(key)) is int and response[key] >= 0}
        return content.strip()

    def describe_image(self, jpeg, question, runner):
        """One local JPEG to an installed vision model; no frame is uploaded elsewhere."""
        self.last_metrics = {}
        if not isinstance(jpeg, bytes) or not jpeg.startswith(b'\xff\xd8') or len(jpeg) > 2_000_000:
            raise ValueError('Choose a readable JPEG frame under 2 MB.')
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1000:
            raise ValueError('Write a frame question of 1–1000 characters.')
        self.identity(runner)
        details = self.request('/api/show', {'model': self.model}, runner)
        capabilities = details.get('capabilities', [])
        if not isinstance(capabilities, list) or 'vision' not in capabilities:
            raise ValueError(f'{self.model} does not advertise image understanding in Ollama. '
                             'Install and select gemma3:12b for frame analysis.')
        response = self.request('/api/chat', {'model': self.model, 'stream': False,
            'messages': [{'role': 'system', 'content': 'Describe only visible evidence in this single game frame. '
                          'Do not claim to have watched the full video or heard audio.'},
                         {'role': 'user', 'content': question.strip(),
                          'images': [base64.b64encode(jpeg).decode('ascii')]}],
            'options': {'num_ctx': 4096, 'num_predict': 350}, 'keep_alive': 0}, runner)
        runner.check()
        if response.get('done') is False or response.get('done_reason') == 'length':
            raise ValueError('The frame analysis was incomplete. Try a shorter question.')
        message = response.get('message')
        answer = message.get('content') if isinstance(message, dict) else None
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 8000:
            raise ValueError('The vision model returned an empty or invalid description.')
        self.last_metrics = {key: response[key] for key in (
            'total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration',
            'eval_count', 'eval_duration')
            if type(response.get(key)) is int and response[key] >= 0}
        return answer.strip()
