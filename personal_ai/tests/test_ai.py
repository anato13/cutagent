import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anato12_ai.core import Assistant, Ollama, Store
from anato12_ai.server import make_server


class FakeModel:
    def __init__(self):
        self.calls = []

    def chat(self, model, messages):
        self.calls.append((model, messages))
        if "Suggest ONE short factual memory" in messages[0]["content"]:
            return "The user prefers quiet, absurd humor with friends."
        if "moon owes" in messages[-1]["content"]:
            return "An absurd claim gets a practical, deadpan follow-up about an invoice."
        system = messages[0]["content"]
        if "purple" in system:
            return "You prefer purple."
        if "orange" in system:
            return "You prefer orange."
        return "I do not have that saved."

    def request(self, path):
        return {"models": [{"name": "qwen2.5:7b"}]}


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.model = FakeModel()

    def test_memory_retrieval_restart_and_correction(self):
        cid = self.store.new_conversation()
        mid = self.store.add_memory("preference", "I prefer purple thumbnails.")
        assistant = Assistant(self.store, self.model)
        first = assistant.chat(cid, "Which thumbnail color do I prefer?")
        self.assertEqual(first["used_memories"], [mid])
        self.assertEqual(first["answer"], "You prefer purple.")
        restarted = Store(self.tmp.name)
        self.assertEqual(len(restarted.messages(cid)), 2)
        restarted.update_memory(mid, "I prefer orange thumbnails.")
        second = Assistant(restarted, self.model).chat(cid, "Which thumbnail color do I prefer?")
        self.assertEqual(second["answer"], "You prefer orange.")
        self.assertIn('I prefer orange thumbnails.', self.model.calls[-1][1][0]["content"])
        self.assertNotIn('I prefer purple thumbnails.', self.model.calls[-1][1][0]["content"])
        restarted.delete_memory(mid)
        third = Assistant(restarted, self.model).chat(cid, "Which thumbnail color do I prefer?")
        self.assertEqual(third["used_memories"], [])

    def test_unapproved_memory_not_used_and_chat_deletion_independent(self):
        cid = self.store.new_conversation()
        mid = self.store.add_memory("humor_like", "I like absurd friend conversations", "suggestion", False)
        self.assertEqual(Assistant(self.store, self.model).chat(cid, "What humor do I like?")["used_memories"], [])
        self.store.update_memory(mid, confirmed=True)
        self.assertEqual(Assistant(self.store, self.model).chat(cid, "What humor do I like?")["used_memories"], [mid])
        self.store.delete_conversation(cid)
        self.assertEqual(self.store.rows("memories")[0]["id"], mid)

    def test_switching_local_models_keeps_conversation_and_memory(self):
        cid = self.store.new_conversation()
        mid = self.store.add_memory("preference", "I prefer purple thumbnails.")
        assistant = Assistant(self.store, self.model)
        first = assistant.chat(cid, "Which thumbnail color?", "qwen2.5:7b")
        second = Assistant(Store(self.tmp.name), self.model).chat(cid, "Which thumbnail color now?", "qwen3:8b")
        self.assertEqual([first["used_memories"], second["used_memories"]], [[mid], [mid]])
        self.assertEqual([call[0] for call in self.model.calls], ["qwen2.5:7b", "qwen3:8b"])
        self.assertEqual(len(Store(self.tmp.name).messages(cid)), 4)

    def test_documents_feedback_personality_and_backup_restore(self):
        cid = self.store.new_conversation()
        mid = self.store.add_memory("editing_style", "Keep the setup before the punchline.")
        doc = self.store.add_document("funny.srt", "00:03 My friend says the moon owes him money")
        result = Assistant(self.store, self.model).chat(cid, "What happened when my friend mentioned the moon?")
        self.assertIn(doc, result["used_documents"])
        self.store.add_feedback(result["message_id"], "funny", "I like deadpan absurd claims")
        self.store.set_personality("Talk casually.")
        Assistant(self.store, self.model).chat(cid, "How do you talk?")
        system = self.model.calls[-1][1][0]["content"]
        self.assertIn("Talk casually.", system)
        self.assertIn("deadpan absurd claims", system)
        snapshot = self.store.export_data()
        self.store.delete_memory(mid)
        self.store.restore_data(snapshot)
        self.assertEqual(self.store.export_data(), snapshot)
        self.assertEqual(Store(self.tmp.name).personality(), "Talk casually.")
        with self.assertRaises(ValueError):
            self.store.restore_data({"version": 1})
        self.assertEqual(self.store.export_data(), snapshot)

    def test_ollama_releases_previous_model_on_switch(self):
        ollama = Ollama()
        calls = []
        def fake_request(path, payload=None):
            calls.append((path, payload))
            if path == "/api/tags":
                return {"models": [{"name": "qwen2.5:7b"}, {"name": "qwen3:8b"}]}
            if path == "/api/chat":
                return {"message": {"content": "Hello"}, "eval_count": 20,
                        "eval_duration": 1_000_000_000}
            return {}
        ollama.request = fake_request
        ollama.chat("qwen2.5:7b", [{"role": "user", "content": "hi"}])
        ollama.chat("qwen3:8b", [{"role": "user", "content": "hi"}])
        self.assertEqual([payload for path, payload in calls if path == "/api/generate"],
                         [{"model": "qwen2.5:7b", "keep_alive": 0}])
        self.assertEqual(ollama.last_metrics["eval_count"], 20)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.server = make_server(self.store, FakeModel(), 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def call(self, path, method="GET", payload=None, token=True, origin=None):
        headers = {"Host": f"127.0.0.1:{self.server.server_port}"}
        if token:
            headers["Authorization"] = "Bearer " + self.store.key
        if origin:
            headers["Origin"] = origin
        body = json.dumps(payload).encode() if payload is not None else None
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = Request(f"http://127.0.0.1:{self.server.server_port}{path}", body, headers, method=method)
        with urlopen(req, timeout=5) as response:
            return json.load(response)

    def test_auth_chat_search_feedback_integration(self):
        with self.assertRaises(HTTPError) as error:
            self.call("/api/v1/state", token=False)
        self.assertEqual(error.exception.code, 401)
        with self.assertRaises(HTTPError) as error:
            self.call("/api/v1/state", origin="http://evil.invalid")
        self.assertEqual(error.exception.code, 403)
        memory = self.call("/api/v1/memories", "POST", {"kind": "humor_like", "content": "Deadpan absurd claims are funny"})["id"]
        cid = self.call("/api/v1/conversations", "POST", {})["id"]
        answer = self.call("/api/v1/chat", "POST", {"conversation": cid, "message": "What absurd humor do I like?"})
        self.assertEqual(answer["used_memories"], [memory])
        self.assertEqual(len(self.call(f"/api/v1/conversations/{cid}")["messages"]), 2)
        self.assertEqual(len(self.call("/api/v1/conversations?q=absurd")["conversations"]), 1)
        self.call("/api/v1/feedback", "POST", {"message": answer["message_id"], "decision": "funny", "note": "Good"})
        self.assertEqual(self.call("/api/v1/integration/preferences")["confirmed_memories"][0]["id"], memory)
        self.assertEqual(self.call("/api/v1/backup")["feedback"][0]["decision"], "funny")

    def test_transcript_analysis_requires_approval(self):
        document = self.call("/api/v1/documents", "POST", {"title": "approved.srt",
            "content": "00:00:03 Friend: The moon owes me money.\n00:00:06 Anato: Did you send it an invoice?"})["id"]
        suggestion = self.call(f"/api/v1/documents/{document}/analyze", "POST", {"model": "qwen2.5:7b"})
        memory = suggestion["suggested_memory"]
        self.assertFalse(self.store.rows("memories")[0]["confirmed"])
        self.assertEqual(self.store.relevant_memories("moon"), [])
        self.call(f"/api/v1/memories/{memory}", "PUT", {"confirmed": True})
        self.assertEqual(self.store.relevant_memories("moon")[0]["id"], memory)

    def test_chat_suggestion_remains_pending(self):
        cid = self.call("/api/v1/conversations", "POST", {})["id"]
        self.call("/api/v1/chat", "POST", {"conversation": cid,
            "message": "I prefer quiet, absurd humor with friends."})
        suggestion = self.call(f"/api/v1/conversations/{cid}/suggest-memory", "POST", {})
        self.assertIsNotNone(suggestion["suggested_memory"])
        self.assertEqual(self.store.rows("memories")[0]["confirmed"], 0)
        self.assertEqual(self.store.relevant_memories("quiet humor"), [])


if __name__ == "__main__":
    unittest.main()
