"""Dense/sparse source coverage, UTF-8 budgets and evidence boundaries."""
from dataclasses import asdict
import pytest

from anato12_studio.finder import rows_for, model_proposals, analyze
from anato12_studio.local_model import LocalModel
from anato12_studio.model import Media, Segment
from anato12_studio.model_context import (
    bounded_windows, checked_messages, input_bytes, MAX_INPUT_BYTES, MAX_CALLBACK_LINKS,
)
from anato12_studio.store import Store
from anato12_studio.video import Runner, Cancelled


def test_two_hour_dense_transcript_covered_with_unchanged_ids_times_and_text():
    segments = [Segment(i*.5, i*.5+.4, f"Dialogue {i}: a quick gaming reaction.")
                for i in range(14400)]
    before = [asdict(s) for s in segments]
    rows = rows_for(segments)
    chunks = list(bounded_windows(rows, {}))
    assert len(chunks) > 120  # Dense rows need smaller sections than time-only windows.
    assert {r["id"] for c in chunks for r in c.rows} == set(range(14400))
    assert all(c.content_bytes <= MAX_INPUT_BYTES for c in chunks)
    assert all(a.rows[0]["id"] < b.rows[0]["id"] for a, b in zip(chunks, chunks[1:]))
    assert all(set(r["id"] for r in a.rows) & set(r["id"] for r in b.rows)
               for a, b in zip(chunks, chunks[1:]))
    assert [asdict(s) for s in segments] == before


def test_utf8_quotes_and_feedback_count_toward_actual_content_budget():
    rows = rows_for([Segment(i, i+.5, '🔥漢字"\\' * 70) for i in range(30)])
    preferences = {"notes": [{"note": "保留完整的反应" * 20} for _ in range(4)]}
    chunks = list(bounded_windows(rows, {}, preferences=preferences))
    assert {r["id"] for c in chunks for r in c.rows} == set(range(30))
    for chunk in chunks:
        messages = checked_messages(chunk.rows, chunk.callbacks, "", preferences)
        assert chunk.content_bytes == input_bytes(messages) <= MAX_INPUT_BYTES


def test_oversized_row_or_query_fails_without_contacting_server(monkeypatch):
    row = {"id": 4, "start": 7180., "end": 7185., "text": "x"*20000}
    with pytest.raises(ValueError, match="segment 4 at 7180.000s"):
        list(bounded_windows([row], {}))
    with pytest.raises(ValueError, match="Search text"):
        list(bounded_windows([dict(row, text="normal")], {}, query="q"*10000))
    client = LocalModel(model="fixture")
    def unexpected(*a, **k):
        raise AssertionError("oversized text should not contact the server")
    monkeypatch.setattr(client, "request", unexpected)
    with pytest.raises(ValueError, match="input budget"):
        client.analyze([row], {}, "", {}, Runner())


def test_callback_budget_excludes_unsent_evidence():
    rows = rows_for([Segment(i, i+.5, "earlier phrase") for i in range(6)] +
                    [Segment(120+i, 120+i+.5, "later phrase") for i in range(6)])
    repeated = {r["id"]: rows[:6] for r in rows[6:]}
    last = list(bounded_windows(rows, repeated))[-1]
    assert sum(len(v) for v in last.callbacks.values()) == MAX_CALLBACK_LINKS
    assert last.omitted_callback_links > 0
    assert last.content_bytes <= MAX_INPUT_BYTES
    supplied = {r["id"] for earlier in last.callbacks.values() for r in earlier}
    omitted = next(r["id"] for r in rows[:6] if r["id"] not in supplied)
    raw = [{"first_id": 6, "last_id": 7, "evidence_ids": [6, omitted]}]
    assert model_proposals(raw, last.rows, last.callbacks, 130) == []


def test_sparse_timestamps_and_single_large_row_still_progress():
    rows = rows_for([Segment(0, 1, "a"*3200), Segment(7180, 7182, "last conversation")])
    chunks = list(bounded_windows(rows, {}))
    assert len(chunks) == 2
    assert [c.rows[0]["start"] for c in chunks] == [0, 7180]
    assert chunks[0].rows[0]["text"] == "a"*3200
    runner = Runner()
    runner.cancel()
    with pytest.raises(Cancelled):
        list(bounded_windows(rows, {}, runner=runner))


def test_dense_analysis_resume_uses_matching_bounded_windows(tmp_path):
    path = tmp_path / "source.mp4"
    path.write_bytes(b"identity fixture")
    segments = [Segment(i*.5, i*.5+.4, "dense dialogue " * 20) for i in range(100)]
    media = Media("m", str(path), 60, 320, 180, transcript=segments)
    store = Store(tmp_path / "profile")
    source = store.source(media)
    class Model:
        base, model = "http://localhost", "fixture"
        def __init__(self, fail=False):
            self.calls, self.fail = [], fail
        def identity(self, runner=None):
            return {"digest": "fixture"}
        def analyze(self, rows, references, query, preferences, runner):
            self.calls.append((rows[0]["id"], rows[-1]["id"]))
            assert input_bytes(checked_messages(rows, references, query, preferences)) <= MAX_INPUT_BYTES
            if self.fail and len(self.calls) == 3:
                raise RuntimeError("interrupted fixture")
            return []  # Valid no-match result, not a quality claim.
    first = Model(True)
    with pytest.raises(RuntimeError, match="interrupted"):
        analyze(store, source, segments, 60, Runner(), lambda *a: None, first)
    resumed = Model()
    assert analyze(store, source, segments, 60, Runner(), lambda *a: None, resumed) == []
    assert resumed.calls[0] == first.calls[2]
    assert first.calls[0] not in resumed.calls and first.calls[1] not in resumed.calls
