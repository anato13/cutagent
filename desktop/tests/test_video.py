"""Real FFmpeg checks: import, precise trims, framing, silence and multi-clip audio."""
import json
import subprocess

import pytest

from anato12_studio.model import Clip, Media, Segment, Project, write_srt
from anato12_studio.video import ExportPlan, Runner, export_video, probe



def media_for(recording, binaries):
    return Media("m", str(recording), **probe(str(recording), binaries[1]))


@pytest.mark.parametrize("profile,expected", [
    ("YouTube · 16:9", (1920, 1080)), ("Shorts · 9:16", (1080, 1920))])
def test_trim_export_real_video(tmp_path, recording, binaries, profile, expected):
    media = media_for(recording, binaries)
    dest = tmp_path / "export.mp4"
    clip = Clip("m", .5, 1.5, fit="fill", zoom=1.1, focus_x=.2)
    plan = ExportPlan({"m": media}, [clip], dest, profile, save_srt=False)
    values = []
    export_video(plan, binaries[0], Runner(), lambda value, _: values.append(value))
    result = probe(str(dest), binaries[1])
    assert (result["width"], result["height"]) == expected
    assert abs(result["duration"] - 1) < .08
    assert result["has_audio"] and values[-1] == 1
    subprocess.run([binaries[0], "-v", "error", "-xerror", "-i", str(dest), "-f", "null", "-"], check=True)


def test_join_has_matching_audio_and_video(tmp_path, recording, binaries):
    media = media_for(recording, binaries)
    clips = [Clip("m", 0, .5), Clip("m", 2, 2.5), Clip("m", 1, 1.5)]
    dest = tmp_path / "joined.mp4"
    export_video(ExportPlan({"m": media}, clips, dest, save_srt=False), binaries[0], Runner())
    data = json.loads(subprocess.check_output([binaries[1], "-v", "error", "-show_streams", "-of", "json", str(dest)]))
    durations = [float(s["duration"]) for s in data["streams"]]
    assert all(abs(d - 1.5) < .06 for d in durations)
    assert abs(durations[0] - durations[1]) < .04


def test_silent_source_is_supported(tmp_path, binaries):
    source = tmp_path / "silent.mp4"
    subprocess.run([binaries[0], "-v", "error", "-f", "lavfi", "-i",
                    "color=red:s=160x90:r=30:d=1", "-c:v", "libx264", str(source)], check=True)
    media = media_for(source, binaries)
    assert not media.has_audio
    out = tmp_path / "output.mp4"
    export_video(ExportPlan({"m": media}, [Clip("m", 0, .5)], out, save_srt=False), binaries[0], Runner())
    assert probe(str(out), binaries[1])["has_audio"]


def test_never_overwrite_source(recording, binaries):
    media = media_for(recording, binaries)
    plan = ExportPlan({"m": media}, [Clip("m", 0, 1)], recording, overwrite=True)
    with pytest.raises(ValueError, match="source recording"):
        plan.validate()


def test_caption_sidecar_cannot_replace_recording(tmp_path, recording, binaries):
    source = tmp_path / "output.srt"
    source.write_bytes(recording.read_bytes())
    media = media_for(source, binaries)
    plan = ExportPlan({"m": media}, [Clip("m", 0, 1)], tmp_path / "output.mp4",
                      save_srt=True, overwrite=True)
    with pytest.raises(ValueError, match="source recording"):
        plan.validate()


def test_cancel_preserves_existing_export(tmp_path, recording, binaries):
    media = media_for(recording, binaries)
    out = tmp_path / "existing.mp4"
    out.write_bytes(b"keep my existing file")
    runner = Runner()
    runner.cancel()
    from anato12_studio.video import Cancelled
    with pytest.raises(Cancelled):
        export_video(ExportPlan({"m": media}, [Clip("m", 0, 1)], out, overwrite=True), binaries[0], runner)
    assert out.read_bytes() == b"keep my existing file"
    assert not list(tmp_path.glob(".anato12*"))


def test_project_and_caption_offsets(tmp_path, recording, binaries):
    media = media_for(recording, binaries)
    media.transcript = [Segment(.25, .75, "No way!"), Segment(2, 3, "What happened?")]
    clips = [Clip("m", .5, 1), Clip("m", 2, 2.5)]
    project = Project(media={"m": media}, clips=clips)
    path = tmp_path / "project.anato12.json"
    project.save(path)
    assert Project.load(path).clips == clips
    srt = tmp_path / "out.srt"
    write_srt(srt, clips, project.media)
    text = srt.read_text()
    assert "00:00:00,000 --> 00:00:00,250" in text
    assert "00:00:00,500 --> 00:00:01,000" in text


def test_burned_captions_real_video(tmp_path, recording, binaries):
    media = media_for(recording, binaries)
    media.transcript = [Segment(0, 2, "It's working! [caption] {not a style}")]
    out = tmp_path / "burned.mp4"
    export_video(ExportPlan({"m": media}, [Clip("m", 0, .5)], out, burn_captions=True),
                 binaries[0], Runner())
    assert out.exists() and out.with_suffix(".srt").exists()


def test_real_export_caption_publish_failure_restores_existing_pair(tmp_path, recording, binaries, monkeypatch):
    import os
    from pathlib import Path
    media = media_for(recording, binaries)
    media.transcript = [Segment(0, 1, 'Caption')]
    destination = tmp_path/'existing.mp4'
    sidecar = destination.with_suffix('.srt')
    destination.write_bytes(b'previous video')
    sidecar.write_bytes(b'previous captions')
    replace = os.replace
    def fail_captions(src, dst):
        if (Path(dst) == sidecar and Path(src).name.startswith('.anato12-')
                and not Path(src).name.startswith('.anato12-backup-')):
            raise OSError('injected caption publish failure')
        return replace(src, dst)
    monkeypatch.setattr(os, 'replace', fail_captions)
    with pytest.raises(OSError, match='caption publish failure'):
        export_video(ExportPlan({'m': media}, [Clip('m', 0, .2)], destination, overwrite=True),
                     binaries[0], Runner())
    assert destination.read_bytes() == b'previous video'
    assert sidecar.read_bytes() == b'previous captions'
    assert not list(tmp_path.glob('.anato12-*'))
