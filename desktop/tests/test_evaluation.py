"""Evaluation harness contracts; fixture models are not semantic quality evidence."""
import json
import pytest
from anato12_studio.evaluate_model import evaluate
from anato12_studio.local_model import LocalModel
from anato12_studio.model import Media, Project, Segment
from test_local_model import endpoint  # noqa: F401


def make_project(tmp_path):
    path = tmp_path / "review.anato12.json"
    media = Media("m", str(tmp_path / "original.mp4"), 150, 320, 180,
                  transcript=[Segment(i, i+1, f"dialogue {i}") for i in range(0, 141, 10)])
    Project(media={"m": media}).save(path)
    return path


def test_http_evaluation_report_retains_evidence_without_claiming_quality(tmp_path, endpoint):  # noqa: F811
    url, _ = endpoint
    project = make_project(tmp_path)
    before = project.read_bytes()
    destination = evaluate(project, tmp_path / "report", LocalModel(url, "fixture-local"), progress=lambda *a: None)
    report = json.loads(destination.read_text())
    assert report["status"] == "completed" and len(report["windows"]) == 2
    assert report["humor_quality"] == "NOT_EVALUATED"
    assert report["model_identity"]["digest"] == "fixture-sha256"
    assert report["candidates"] and report["candidates"][0]["evidence"][0]["text"] == "dialogue 0"
    assert report["windows"][1]["rejected_proposals"] == 1  # fixture's old IDs are invalid in second window
    assert project.read_bytes() == before
    with pytest.raises(FileExistsError):
        evaluate(project, tmp_path / "report", LocalModel(url, "fixture-local"))


def test_failure_report_preserves_completed_windows(tmp_path):
    class Failing:
        model, base = "fixture", "http://localhost"
        count = 0
        def identity(self, runner=None):
            return {"digest": "fixture"}
        def analyze(self, rows, *a):
            self.count += 1
            if self.count == 2:
                raise RuntimeError("fixture outage")
            return [{"first_id": 0, "last_id": 1, "evidence_ids": [0, 1]}]
    with pytest.raises(RuntimeError, match="outage"):
        evaluate(make_project(tmp_path), tmp_path / "report", Failing(), progress=lambda *a: None)
    report = json.loads((tmp_path / "report/model-evaluation.json").read_text())
    assert report["status"] == "failed" and len(report["windows"]) == 1
    assert report["candidates"]
