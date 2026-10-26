"""Actual long synthetic files: import, end-of-file timestamps and exported streams.

These fixtures do NOT establish long genuine speech or humor-recognition quality.
"""
import json
import subprocess
import time

import pytest

from anato12_studio.finder import analyze
from anato12_studio.model import Clip, Media, Segment
from anato12_studio.store import Store
from anato12_studio.video import ExportPlan, Runner, export_video, probe


@pytest.mark.parametrize("duration", [30, 300, 1200, 3600, 7200])
def test_full_duration_import_find_end_and_export(tmp_path, binaries, duration):
    start = time.monotonic()
    source_path = tmp_path / f"synthetic-{duration}s.mp4"
    subprocess.run([binaries[0], "-v", "error", "-f", "lavfi", "-i",
        f"color=blue:s=64x36:r=1:d={duration}", "-f", "lavfi", "-i",
        "anullsrc=r=8000:cl=mono", "-t", str(duration), "-c:v", "libx264", "-threads", "2",
        "-preset", "ultrafast", "-c:a", "aac", "-b:a", "8k", str(source_path)],
        check=True, timeout=60)
    media = Media("long", str(source_path), **probe(str(source_path), binaries[1]))
    assert abs(media.duration-duration) < .2
    media.transcript = [Segment(duration-4, duration-3, "Did you open that?"),
                        Segment(duration-2.8, duration-2, "No actually, wait what?"),
                        Segment(duration-1.8, duration-1, "[laughing] Oh my god")]
    store = Store(tmp_path / "profile")
    key = store.source(media)
    ids = analyze(store, key, media.transcript, media.duration, Runner(), lambda *a: None)
    assert len(ids) == 1
    item = store.highlight(ids[0])
    assert item["start"] == duration-8 and item["end"] == duration
    assert all(duration-4 <= r["start"] < duration for r in json.loads(item["evidence"]))
    dest = tmp_path / "end.mp4"
    export_start = time.monotonic()
    export_video(ExportPlan({"long": media}, [Clip("long", duration-2, duration-1)],
                           dest, save_srt=True), binaries[0], Runner())
    export_elapsed = time.monotonic()-export_start
    result = probe(str(dest), binaries[1])
    assert abs(result["duration"]-1) < .08 and result["has_audio"]
    data = json.loads(subprocess.check_output([binaries[1], "-v", "error", "-show_streams",
                                               "-of", "json", str(dest)]))
    assert all(abs(float(s["duration"])-1) < .08 for s in data["streams"])
    assert "00:00:00,200 --> 00:00:01,000" in dest.with_suffix(".srt").read_text()
    subprocess.run([binaries[0], "-v", "error", "-xerror", "-i", str(dest), "-f", "null", "-"],
                   check=True, timeout=15)
    print(f"\nsynthetic_source={duration}s source_bytes={source_path.stat().st_size} "
          f"end_export_wall={export_elapsed:.3f}s total_wall={time.monotonic()-start:.3f}s")


@pytest.mark.parametrize("kind", ["missing", "corrupt"])
def test_bad_media_is_rejected(tmp_path, binaries, kind):
    path = tmp_path / "broken.mp4"
    if kind == "corrupt":
        path.write_bytes(b"this is not video")
    with pytest.raises((ValueError, RuntimeError)):
        probe(str(path), binaries[1])
