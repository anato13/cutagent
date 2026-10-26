"""Real approved-draft assembly, independent project export and failure cleanup."""
from dataclasses import asdict
import json
from pathlib import Path
import pytest

from anato12_studio.drafts import DraftOptions, assemble, create_bundle
from anato12_studio.model import Media, Project, Segment
from anato12_studio.store import Store
from anato12_studio.video import Runner, Cancelled, probe


def item(identifier, start, end, source="source", status="approved"):
    return {"id": identifier, "start": start, "end": end, "source": source, "status": status,
            "title": f"Moment {identifier}"}


def test_assembly_preserves_ranges_merges_overlap_and_skips_long_or_duplicate_shorts():
    media = Media("m", "original.mp4", 120, 320, 180, transcript=[Segment(0, 110, "dialogue")])
    before = asdict(media)
    highlights = [item("late", 90, 100), item("first", 2, 6), item("overlap", 5, 9),
                  item("duplicate", 2, 6), item("long", 20, 85), item("no", 0, 1, status="rejected"),
                  item("other", 0, 110, source="other")]
    main, shorts, details = assemble(media, "source", highlights, DraftOptions())
    assert [(c.start, c.end) for c in main.clips] == [(2, 9), (20, 85), (90, 100)]
    assert len(shorts) == 3 and len(details["shorts_skipped"]) == 2
    assert main.profile == "YouTube · 16:9"
    assert all(p.profile == "Shorts · 9:16" and len(p.clips) == 1 for _, p in shorts)
    shorts[0][1].media["m"].transcript[0].text = "edited Short"
    assert main.media["m"].transcript[0].text == "dialogue" and asdict(media) == before


def test_bundle_projects_and_real_mp4s_both_ratios(tmp_path, recording, binaries):
    media = Media("m", str(recording), **probe(str(recording), binaries[1]))
    media.transcript = [Segment(.5, 1, "setup"), Segment(1, 2, "reaction")]
    store = Store(tmp_path / "profile")
    source = store.source(media)
    highlights = [item("a", .5, 1.5, source), item("b", 1, 2, source)]
    original = asdict(media)
    result = create_bundle(media, source, highlights, tmp_path,
                           DraftOptions(burn_captions=True, save_srt=True, render=True),
                           binaries[0], Runner(), lambda *a: None)
    folder = Path(result["directory"])
    manifest = json.loads((folder / "draft-manifest.json").read_text())
    assert len(manifest["outputs"]) == 3 and result["main_clips"] == 1 and result["shorts"] == 2
    assert asdict(media) == original
    for entry in manifest["outputs"]:
        project = Project.load(folder / entry["project"])
        exported = probe(str(folder / entry["video"]), binaries[1])
        assert project.profile == entry["profile"]
        expected = (1920, 1080) if project.profile == "YouTube · 16:9" else (1080, 1920)
        assert (exported["width"], exported["height"]) == expected and exported["has_audio"]
        assert abs(exported["duration"]-entry["duration_seconds"]) < .06
        assert (folder / entry["captions"]).is_file()
    assert "00:00:00,000 --> 00:00:00,500" in (folder / "YouTube.srt").read_text()
    assert not list(tmp_path.glob(".anato12-drafts-*"))


@pytest.mark.parametrize("failure", ["cancel", "disk_full", "render_cancel"])
def test_failure_publishes_no_partial_bundle_and_preserves_existing_files(
        tmp_path, recording, binaries, monkeypatch, failure):
    media = Media("m", str(recording), **probe(str(recording), binaries[1]))
    store = Store(tmp_path / "profile")
    source = store.source(media)
    old = tmp_path / "existing.mp4"
    old.write_bytes(b"preserve")
    runner = Runner()
    if failure == "disk_full":
        def full(*a):
            raise OSError(28, "No space left on device")
        monkeypatch.setattr(Project, "save", full)
        expected = OSError
    else:
        expected = Cancelled
    with pytest.raises(expected):
        create_bundle(media, source, [item("a", .5, 1.5, source)], tmp_path,
                      DraftOptions(render=failure == "render_cancel"), binaries[0], runner,
                      lambda value, message: runner.cancel() if failure != "render_cancel" or value >= .5 else None)
    assert old.read_bytes() == b"preserve" and Path(media.path).is_file()
    assert not list(tmp_path.glob("*drafts-*")) and not list(tmp_path.glob(".anato12-drafts-*"))


def test_source_change_and_unapproved_input_do_not_create_output(tmp_path, recording, binaries):
    media = Media("m", str(recording), **probe(str(recording), binaries[1]))
    source = Store(tmp_path / "profile").source(media)
    with pytest.raises(ValueError, match="changed"):
        create_bundle(media, "different", [item("a", 0, 1)], tmp_path, DraftOptions(), "",
                      Runner(), lambda *a: None)
    with pytest.raises(ValueError, match="Approve"):
        create_bundle(media, source, [item("a", 0, 1, source, "rejected")], tmp_path, DraftOptions(), "",
                      Runner(), lambda *a: None)
    assert not list(tmp_path.glob("*drafts-*"))


def test_draft_query_includes_all_approved_beyond_display_limit(tmp_path, recording, binaries):
    store = Store(tmp_path / "profile")
    media = Media("m", str(recording), **probe(str(recording), binaries[1]))
    source = store.source(media)
    for i in range(501):
        identifier = store.upsert_highlight(source, str(i), 0, 1, str(i), "other", "", "", [], "test", 1)
        store.review(identifier, "approved")
    assert len(store.highlights(source)) == 500
    assert len(store.approved_for_source(source)) == 501
