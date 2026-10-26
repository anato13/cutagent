import io
from pathlib import Path
import tarfile

import pytest

from anato12_studio.captions import read_srt
from anato12_studio.model import Clip, Media, Project, Segment, write_ass
from anato12_studio.moments import suggest_moments
from anato12_studio.speech import ensure_model, model_files
from anato12_studio.video import Cancelled, Runner


def test_import_srt_clips_to_original_duration(tmp_path):
    p = tmp_path / "captions.srt"
    p.write_text("1\n00:00:00,200 --> 00:00:01,500\nNo way!\n\n"
                 "2\n00:00:02,000 --> 00:00:05,000\nLast line\n", encoding="utf-8-sig")
    lines = read_srt(p, 3)
    assert [(s.start, s.end) for s in lines] == [(.2, 1.5), (2, 3)]


def test_suggestions_include_setup_and_deduplicate():
    lines = [Segment(5, 8, "Watch what happens."),
             Segment(9, 12, "No way!!"),
             Segment(13, 15, "That was hilarious. Laughing."),
             Segment(70, 74, "I can't believe that!")]
    moments = suggest_moments(lines, 75)
    assert 1 <= len(moments) <= 2
    assert all(0 <= m.start < m.end <= 75 for m in moments)
    assert any(m.start <= 5 and m.end >= 15 for m in moments)


def test_ordinary_dialogue_is_not_labeled_funny():
    assert suggest_moments([Segment(0, 10, "Bro, the next match starts at seven.")], 30) == []


def test_ass_offsets_and_control_text_are_safe(tmp_path):
    p = tmp_path / "captions.ass"
    write_ass(p, [Segment(36000, 36002, r"Hello {\pos(0,0)}")], 35999, 4, 1080, 1920)
    text = p.read_text(encoding="utf-8-sig")
    assert "0:00:01.00,0:00:03.00" in text
    assert r"{\pos" not in text
    assert "PlayResX: 1080" in text


def test_model_download_extracts_only_expected_data(tmp_path, monkeypatch):
    name = "tiny.en"
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:bz2") as archive:
        for path, size in [(p, 1_000_001 if p.suffix == ".onnx" else 2000)
                           for p in model_files(Path("model"), name)]:
            entry = tarfile.TarInfo("../outside/" + path.name)
            entry.size = size
            archive.addfile(entry, io.BytesIO(b"x" * size))
        entry = tarfile.TarInfo("unneeded.exe")
        entry.size = 4
        archive.addfile(entry, io.BytesIO(b"nope"))
    body = buffer.getvalue()
    class Response(io.BytesIO):
        headers = {"Content-Length": str(len(body))}
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Response(body))
    model = ensure_model(name, tmp_path / "models", Runner(), lambda *_: None)
    assert all(p.exists() for p in model_files(model, name))
    assert not (tmp_path / "outside").exists()
    assert not (model / "unneeded.exe").exists()


def test_download_cancellation_does_not_leave_partial_model(tmp_path, monkeypatch):
    runner = Runner()
    class Response(io.BytesIO):
        headers = {}
        def read(self, size=-1):
            runner.cancel()
            return super().read(size)
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Response(b"some data"))
    with pytest.raises(Cancelled):
        ensure_model("tiny.en", tmp_path, runner, lambda *_: None)
    assert list(tmp_path.iterdir()) == []


def test_reject_invalid_project_range(tmp_path):
    project = Project(media={"m": Media("m", "missing.mp4", 10, 320, 180)},
                      clips=[Clip("m", 8, 3)])
    path = tmp_path / "bad.anato12.json"
    project.save(path)
    with pytest.raises(ValueError, match="one video frame"):
        Project.load(path)


def test_transcription_ignores_blank_audio_marker_preserves_reaction(tmp_path, recording, binaries, monkeypatch):
    """Exercise real audio preparation with a controlled recognizer result."""
    import json
    from types import SimpleNamespace
    sherpa = pytest.importorskip("sherpa_onnx")
    from anato12_studio.speech import transcribe
    from anato12_studio.video import probe
    class Recognizer:
        def create_stream(self):
            return SimpleNamespace(accept_waveform=lambda *a: None, result=json.dumps({
                "segment_timestamps": [0, 1, 2], "segment_durations": [.5, .5, .5],
                "segment_texts": ["[BLANK_AUDIO]", "Actual dialogue", "[LAUGHTER]"]}))
        def decode_stream(self, stream):
            pass
    monkeypatch.setattr(sherpa.OfflineRecognizer, "from_whisper", lambda **k: Recognizer())
    monkeypatch.setattr("anato12_studio.speech.ensure_model", lambda *a: tmp_path)
    media = Media("m", str(recording), **probe(str(recording), binaries[1]))
    result = transcribe(media, binaries[0], "tiny.en", Runner(), lambda *a: None)
    assert [s.text for s in result] == ["Actual dialogue", "[LAUGHTER]"]
