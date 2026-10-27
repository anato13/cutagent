"""Local routing and explicit install checks; no model downloads in tests."""
from io import StringIO

import pytest

from anato12_studio.model_policy import (choose_model, context_tokens, installation_check,
                                          model_speed, resource_snapshot, install_model)
from anato12_studio.personal_bridge import PersonalAIClient
from anato12_studio.video import Runner


def test_modes_route_only_to_installed_local_models_and_fallback_is_visible():
    installed = ["qwen2.5:7b", "qwen3:8b", "qwen3:14b", "remote:cloud"]
    assert choose_model(installed, "Fast", "chat")[0] == "qwen3:8b"
    assert choose_model(installed + ["qwen2.5:3b"], "Fast", "chat")[0] == "qwen2.5:3b"
    assert choose_model(installed, "Balanced", "analysis")[0] == "qwen3:8b"
    assert choose_model(installed, "Maximum intelligence", "analysis")[0] == "qwen3:14b"
    assert choose_model(installed, "Automatic", "chat", "hi")[0] == "qwen3:8b"
    assert choose_model(installed, "Automatic", "chat", "Analyze the humor in this exchange")[0] == "qwen3:14b"
    assert choose_model(installed, "Automatic", "analysis")[0] == "qwen3:14b"
    model, note = choose_model(["qwen2.5:7b"], "Maximum intelligence", "analysis")
    assert model == "qwen2.5:7b" and "not installed" in note
    assert choose_model(installed, "Fast", "chat", selected="qwen2.5:7b")[0] == "qwen2.5:7b"
    with pytest.raises(ValueError, match="not installed"):
        choose_model(installed, selected="remote:cloud")
    with pytest.raises(ValueError, match="No compatible"):
        choose_model(["remote:cloud"], task="analysis")
    with pytest.raises(ValueError, match="No compatible"):
        choose_model(["qwen3:8b"], task="visual")


def test_model_context_and_actual_speed_report_are_bounded():
    assert context_tokens("qwen3:14b") == 4096
    assert context_tokens("qwen3:8b") == 8192
    assert model_speed({"eval_count": 50, "eval_duration": 2_000_000_000}) == 25.0
    assert model_speed({"eval_count": 10, "eval_duration": 0}) is None
    assert model_speed({"eval_count": True, "eval_duration": 100}) is None


def test_storage_precheck_rejects_insufficient_space_and_unknown_tags():
    with pytest.raises(ValueError, match="Free storage"):
        installation_check("qwen3:14b", {"disk_free_gb": 10})
    assert "estimate" in installation_check("qwen3:8b", {"disk_free_gb": 20})
    with pytest.raises(ValueError, match="verified model tag"):
        installation_check("untrusted:latest", {"disk_free_gb": 100})
    assert resource_snapshot()["disk_free_gb"] >= 0


def test_personal_bridge_uses_local_key_and_bounds_confirmed_notes(tmp_path, monkeypatch):
    (tmp_path / "api-key").write_text("abcdefghijklmnopqrstuvwxyz123456", encoding="utf-8")
    calls = []
    def fake_request(base, path, payload, runner, timeout, headers, service):
        calls.append((base, path, payload, headers, service))
        if path.endswith("preferences"):
            return {"confirmed_memories": [{"kind": "humor_like", "content": "absurd " * 100},
                                            {"kind": "fact", "content": "private"}]}
        if path.endswith("/chat"):
            return {"answer": "Hello", "used_memories": [1],
                    "model_metrics": {"eval_count": 20, "eval_duration": 1_000_000_000}}
        if path.endswith("/conversations"):
            return {"id": 7}
        return {"messages": []}
    monkeypatch.setattr("anato12_studio.personal_bridge.request_json", fake_request)
    client = PersonalAIClient(tmp_path)
    assert client.preferences() == [{"kind": "humor_like", "text": ("absurd " * 100)[:160]}]
    result = client.chat("hi", "qwen3:8b")
    assert result["conversation"] == 7 and model_speed(result["metrics"]) == 20.0
    assert calls[-1][2]["model"] == "qwen3:8b"
    assert all(call[0] == "http://127.0.0.1:8766" and
               call[3]["Authorization"].startswith("Bearer ") and call[4] == "Personal AI" for call in calls)
    with pytest.raises(ValueError, match="local service"):
        PersonalAIClient(tmp_path, "http://evil.invalid")


def test_model_install_is_explicit_and_reports_pull_progress(monkeypatch):
    calls = []
    class Process:
        def __init__(self):
            self.stdout = StringIO("pulling 10%\rpulling 95%\rdownload complete\n")
        def poll(self):
            return 0
        def wait(self):
            return 0
    monkeypatch.setattr("anato12_studio.model_policy.resource_snapshot",
                        lambda: {"disk_free_gb": 30, "ram_available_gb": 20})
    monkeypatch.setattr("anato12_studio.model_policy.shutil.which", lambda name: "/fake/ollama")
    def fake_popen(args, **kwargs):
        calls.append(args)
        return Process()
    monkeypatch.setattr("anato12_studio.model_policy.subprocess.Popen", fake_popen)
    progress = []
    assert install_model("qwen3:8b", Runner(), lambda value, label: progress.append((value, label))) == "qwen3:8b"
    assert calls == [["/fake/ollama", "pull", "qwen3:8b"]]
    assert any(value == .95 for value, _ in progress)
    assert progress[-1][0] == 1
    with pytest.raises(ValueError, match="verified model tag"):
        install_model("unknown:latest", Runner(), lambda *_: None)
    assert len(calls) == 1
