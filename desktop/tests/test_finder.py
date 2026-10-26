"""Persistent reviews, absolute evidence, durable recovery and real pipeline checks."""
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

import pytest

from anato12_studio.finder import (
    analyze, callbacks, context_cues, deduplicate, literal_search, model_proposals, rows_for, windows,
)
from anato12_studio.finder_jobs import run_pipeline, thumbnail_path
from anato12_studio.model import Media, Segment
from anato12_studio.store import Store, fingerprint
from anato12_studio.video import Cancelled, Runner, probe


@pytest.fixture
def review(tmp_path, recording, binaries):
    store = Store(tmp_path / "profile")
    media = Media("m", str(recording), **probe(str(recording), binaries[1]))
    media.transcript = [Segment(.1, .7, "Did you open the door?"),
                        Segment(.8, 1.5, "No, actually that was the wrong door."),
                        Segment(1.6, 2.2, "Wait what?"),
                        Segment(2.3, 3.2, "[laughing] Oh my god.")]
    source = store.source(media)
    ids = analyze(store, source, media.transcript, media.duration, Runner(), lambda *a: None)
    assert len(ids) == 1
    return store, media, source, ids[0]


def test_review_adjustment_feedback_survive_restart_and_reanalysis(review):
    store, media, source, identifier = review
    store.review(identifier, "approved")
    store.adjust(identifier, .5, 1.5, "My chosen setup", "exact transcript")
    store.add_feedback(identifier, "Keep more setup", False)
    assert store.preferences() == {}
    store.add_feedback(identifier, "This category works", True)
    assert store.preferences() == {"misunderstanding": 1}
    restarted = Store(store.root)
    assert restarted.highlight(identifier)["status"] == "approved"
    analyze(restarted, source, media.transcript, media.duration, Runner(), lambda *a: None)
    item = restarted.highlight(identifier)
    assert (item["start"], item["end"], item["title"], item["edited"]) == (.5, 1.5, "My chosen setup", 1)
    assert all(f["kind"] == "user_confirmed" for f in restarted.feedback())
    opted_in = next(f for f in restarted.feedback() if f["personalize"])
    restarted.delete_feedback(opted_in["id"])
    assert restarted.preferences() == {}


def test_cache_deletion_preserves_reviews_and_source_deletion_preserves_video(review, tmp_path):
    store, media, source, identifier = review
    store.review(identifier, "approved")
    store.add_feedback(identifier, "Keep", True)
    store.clear_cache()
    assert store.highlight(identifier)["status"] == "approved" and len(store.feedback()) == 1
    assert store.cache_get(f"analysis-transcript:{source}") is None
    thumb = thumbnail_path(store, store.highlight(identifier))
    thumb.parent.mkdir(parents=True)
    thumb.write_bytes(b"disposable preview")
    original = Path(media.path).read_bytes()
    export = tmp_path / "data.json"
    store.export_data(export)
    assert json.loads(export.read_text())["highlights"][0]["id"] == identifier
    store.delete_source_data(source)
    assert not store.highlights() and not store.feedback() and not thumb.exists()
    assert Path(media.path).read_bytes() == original


def test_job_restart_recovery_and_source_change(review):
    store, media, source, _ = review
    identifier = store.create_job(source, {"query": "door"})
    store.update_job(identifier, "running", .42, "Analyzing")
    restarted = Store(store.root)
    restarted.recover_jobs()
    job = restarted.jobs()[0]
    assert (job["status"], job["progress"]) == ("interrupted", .42)
    changed = Path(media.path).with_name("new.mp4")
    changed.write_bytes(Path(media.path).read_bytes() + b"changed")
    assert fingerprint(str(changed)) != source
    media.path = str(changed)
    with pytest.raises(ValueError, match="source changed"):
        run_pipeline(store, source, media, {}, identifier, "unused", Runner(), lambda *a: None)
    assert store.jobs()[0]["status"] == "failed"


def test_model_times_and_quotes_only_come_from_supplied_evidence():
    rows = rows_for([Segment(3601, 3604, "setup"), Segment(3606, 3610, "reaction")])
    item = {"first_id": 0, "last_id": 1, "evidence_ids": [0, 1], "category": "banter",
            "title": "Review this exchange", "reason": "Potential contrast", "start": -99, "end": 999999}
    proposal = model_proposals([item], rows, {}, 7200)[0]
    assert (proposal.start, proposal.end) == (3597, 3615)
    assert proposal.evidence == rows
    invalid = [dict(item, first_id=-1), dict(item, last_id=999), dict(item, evidence_ids=[42]),
               dict(item, first_id=True), dict(item, evidence_ids="0"), None]
    assert model_proposals(invalid, rows, {}, 7200) == []
    assert model_proposals([dict(item, category=[])], rows, {}, 7200)[0].category == "other"


def test_overlapping_windows_sparse_absolute_timestamps_and_dedup():
    rows = rows_for([Segment(i, i+1, f"line {i}") for i in range(0, 121, 10)] +
                    [Segment(7190, 7192, "last moment")])
    chunks = list(windows(rows))
    assert len(chunks) == 4 and chunks[-1][0]["start"] == 7190
    assert set(r["id"] for r in chunks[0]) & set(r["id"] for r in chunks[1])
    raw = {"first_id": 0, "last_id": 1, "evidence_ids": [0]}
    proposals = model_proposals([raw, raw], rows[:2], {}, 7200)
    assert len(deduplicate(proposals)) == 1


@pytest.mark.parametrize("texts", [
    ["[laughing]", "[laughing]"], ["damn", "fuck"], ["VERY LOUD", "LOUDER"], ["normal words", "hello"],
])
def test_laughter_profanity_volume_alone_do_not_establish_humor(texts):
    rows = rows_for([Segment(i*3, i*3+2, text) for i, text in enumerate(texts)])
    assert context_cues(rows, {}, 20) == []


def test_callback_evidence_has_real_earlier_phrase():
    rows = rows_for([Segment(1, 3, "purple banana dance squad"),
                     Segment(120, 123, "The purple banana dance squad returns")])
    evidence = callbacks(rows)
    assert evidence[1] == [rows[0]]
    assert callbacks(rows_for([Segment(1, 3, "you are in the"), Segment(120, 123, "you are in the")])) == {}


def test_literal_search_no_fake_match_or_substring():
    rows = rows_for([Segment(3600, 3604, "The update is ready"), Segment(3610, 3614, "Pretend this is a date")])
    assert literal_search(rows[:1], "find the date", 7200) == []
    hits = literal_search(rows, "date", 7200)
    assert len(hits) == 1 and "date" in hits[0].title
    assert hits[0].start == 3596 and hits[0].end == 3619
    assert literal_search(rows, "everyone laughing", 7200) == []


def test_real_pipeline_generates_frame_and_cancel_is_durable(review, binaries):
    store, media, source, identifier = review
    params = {"query": "", "contextual": False}
    job = store.create_job(source, params)
    result = run_pipeline(store, source, media, params, job, binaries[0], Runner(), lambda *a: None)
    assert result["ids"] == [identifier] and store.jobs()[0]["status"] == "completed"
    path = thumbnail_path(store, store.highlight(identifier))
    assert path.read_bytes().startswith(b"\x89PNG")
    cancelled_job = store.create_job(source, params)
    runner = Runner()
    runner.cancel()
    with pytest.raises(Cancelled):
        run_pipeline(store, source, media, params, cancelled_job, binaries[0], runner, lambda *a: None)
    assert next(j for j in store.jobs() if j["id"] == cancelled_job)["status"] == "cancelled"


def test_newer_database_refused_without_erasing_data(tmp_path):
    root = tmp_path / "future"
    store = Store(root)
    with store.connect() as db:
        db.execute("PRAGMA user_version=99")
    before = store.path.read_bytes()
    with pytest.raises(ValueError, match="newer"):
        Store(root)
    with sqlite3.connect(store.path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 99
    assert store.path.read_bytes() == before


def test_invalid_adjustment_and_export_cannot_destroy_source(review, tmp_path, monkeypatch):
    store, media, _, identifier = review
    with pytest.raises(ValueError):
        store.adjust(identifier, float("nan"), 1, "bad", "")
    disguised = tmp_path / "source.json"
    disguised.hardlink_to(media.path)
    with pytest.raises(ValueError, match="source recording"):
        store.export_data(disguised)
    destination = tmp_path / "existing.json"
    destination.write_text("preserve")
    def full_disk(*a, **k):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr("anato12_studio.store.json.dump", full_disk)
    with pytest.raises(OSError):
        store.export_data(destination)
    assert destination.read_text() == "preserve"
    assert not list(tmp_path.glob(".anato12-data-*"))


def test_cached_transcript_needs_no_optional_runtime(review, monkeypatch):
    from anato12_studio.speech import transcribe, TRANSCRIPT_VERSION
    store, media, source, _ = review
    store.cache_put(f"{TRANSCRIPT_VERSION}:{source}:tiny.en", source, "transcript", [asdict(s) for s in media.transcript])
    monkeypatch.setattr("anato12_studio.speech.importlib.util.find_spec",
                        lambda *a: (_ for _ in ()).throw(AssertionError("should not import runtime")))
    result = transcribe(media, "unused", "tiny.en", Runner(), lambda *a: None, cache=store)
    assert result == media.transcript


def test_resumed_analysis_reuses_saved_imported_transcript(review, binaries, monkeypatch):
    store, media, source, identifier = review
    media.transcript = []
    def unexpected(*a, **k):
        raise AssertionError("saved imported dialogue should not trigger automatic transcription")
    monkeypatch.setattr("anato12_studio.speech.transcribe", unexpected)
    params = {"contextual": False}
    job = store.create_job(source, params)
    store.update_job(job, "interrupted")
    result = run_pipeline(store, source, media, params, job, binaries[0], Runner(), lambda *a: None)
    assert result["ids"] == [identifier] and len(result["segments"]) == 4


def test_abrupt_worker_exit_preserves_committed_job_for_restart(review):
    import subprocess
    import sys
    store, _, source, _ = review
    script = """import os,sys
from pathlib import Path
from anato12_studio.store import Store
s=Store(Path(sys.argv[1]))
j=s.create_job(sys.argv[2], {})
s.update_job(j,'running',.4,'Processing')
os._exit(7)
"""
    result = subprocess.run([sys.executable, "-c", script, str(store.root), source],
                            cwd=Path(__file__).resolve().parents[1], timeout=10)
    assert result.returncode == 7
    restarted = Store(store.root)
    restarted.recover_jobs()
    assert restarted.jobs()[0]["status"] == "interrupted"
    assert restarted.jobs()[0]["progress"] == .4


def test_interrupted_model_analysis_reuses_completed_windows_and_separates_endpoints(review):
    """Controlled adapter responses test caching, not semantic accuracy."""
    store, _, source, _ = review
    segments = [Segment(i, i+1, f"source line {i}") for i in range(0, 141, 10)]
    class ControlledModel:
        model = "fixture-only"
        base = "http://127.0.0.1:12345"
        digest = "original"
        def identity(self, runner=None):
            return {"digest": self.digest}
        def __init__(self, fail=False):
            self.calls, self.fail = [], fail
        def analyze(self, window, *args):
            self.calls.append(window[0]["id"])
            if self.fail and len(self.calls) == 2:
                raise RuntimeError("fixture connection interrupted")
            return [{"first_id": window[0]["id"], "last_id": window[0]["id"],
                     "evidence_ids": [window[0]["id"]], "category": "other"}]
    initial = ControlledModel(fail=True)
    with pytest.raises(RuntimeError, match="interrupted"):
        analyze(store, source, segments, 150, Runner(), lambda *a: None, initial)
    assert initial.calls == [0, 6]
    resumed = ControlledModel()
    assert len(analyze(store, source, segments, 150, Runner(), lambda *a: None, resumed)) == 2
    assert resumed.calls == [6]  # First completed response survives failure.
    other_endpoint = ControlledModel()
    other_endpoint.base = "http://127.0.0.1:23456"
    analyze(store, source, segments, 150, Runner(), lambda *a: None, other_endpoint)
    assert other_endpoint.calls == [0, 6]  # No endpoint-to-endpoint response reuse.
    replaced = ControlledModel()
    replaced.digest = "replacement-weights"
    analyze(store, source, segments, 150, Runner(), lambda *a: None, replaced)
    assert replaced.calls == [0, 6]


def test_invalid_model_evidence_is_not_cached_as_no_match(review):
    store, media, source, _ = review
    class InvalidModel:
        base, model = "http://localhost", "fixture"
        def identity(self, runner=None):
            return {"digest": "fixture"}
        def analyze(self, *a):
            return [{"first_id": 999, "last_id": 999, "evidence_ids": [999]}]
    with pytest.raises(ValueError, match="valid source evidence"):
        analyze(store, source, media.transcript, media.duration, Runner(), lambda *a: None, InvalidModel())
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM cache WHERE kind='analysis_window'").fetchone()[0] == 0


def test_model_replacement_during_request_is_not_cached(review):
    store, media, source, _ = review
    class ChangedModel:
        base, model, digest = "http://localhost", "fixture", "old"
        def identity(self, runner=None):
            return {"digest": self.digest}
        def analyze(self, *a):
            self.digest = "new"
            return [{"first_id": 0, "last_id": 1, "evidence_ids": [0, 1]}]
    with pytest.raises(ValueError, match="changed during analysis"):
        analyze(store, source, media.transcript, media.duration, Runner(), lambda *a: None, ChangedModel())
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM cache WHERE kind='analysis_window'").fetchone()[0] == 0
