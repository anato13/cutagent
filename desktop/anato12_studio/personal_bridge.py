"""Opt-in bridge to the independent, loopback-only ANATO12 AI memory service."""
import os
from pathlib import Path

from .local_transport import request_json


def personal_data_dir():
    if os.environ.get("ANATO12_AI_DATA_DIR"):
        return Path(os.environ["ANATO12_AI_DATA_DIR"]).expanduser().resolve()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Anato12AI"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "Anato12AI"


class PersonalAIClient:
    def __init__(self, root=None, base="http://127.0.0.1:8766"):
        if base != "http://127.0.0.1:8766":
            raise ValueError("Personal AI integration accepts only the local service on port 8766.")
        self.base = base
        self.root = Path(root or personal_data_dir())

    def request(self, path, payload=None, runner=None, timeout=15):
        key = self.root / "api-key"
        try:
            token = key.read_text(encoding="utf-8").strip()
        except OSError as error:
            raise RuntimeError("Personal AI memory is not set up. Launch ANATO12 AI first, "
                               "or turn off Use Personal AI memory.") from error
        if not 20 <= len(token) <= 200 or not token.isascii() or not token.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Personal AI API key is invalid. Restart ANATO12 AI to repair its local profile.")
        try:
            return request_json(self.base, "/api/v1/" + path, payload, runner, timeout,
                                {"Authorization": "Bearer " + token}, service="Personal AI")
        except RuntimeError as error:
            raise RuntimeError(f"Personal AI connection failed: {error}. Start ANATO12 AI, "
                               "or turn off Use Personal AI memory.") from error

    def preferences(self, runner=None):
        data = self.request("integration/preferences", runner=runner)
        rows = data.get("confirmed_memories")
        if not isinstance(rows, list):
            raise ValueError("Personal AI returned an invalid preference list.")
        return [{"kind": r["kind"], "text": r["content"][:160]}
                for r in rows[:4] if isinstance(r, dict) and r.get("kind") in
                {"preference", "humor_like", "humor_dislike", "editing_style"} and
                isinstance(r.get("content"), str)]

    def chat(self, question, model, conversation=None, runner=None):
        if conversation is not None:
            try:
                self.request(f"conversations/{int(conversation)}", runner=runner)
            except RuntimeError as error:
                if "HTTP 400" not in str(error):
                    raise
                conversation = None  # Deleted in Personal AI; create a fresh chat.
        if conversation is None:
            conversation = self.request("conversations", {"title": "Studio chat"}, runner)["id"]
        result = self.request("chat", {"conversation": conversation,
                                       "message": question, "model": model}, runner, timeout=200)
        if not isinstance(result.get("answer"), str):
            raise ValueError("Personal AI returned no answer.")
        return {"answer": result["answer"], "conversation": conversation,
                "used_memories": result.get("used_memories", []),
                "metrics": result.get("model_metrics", {})}
