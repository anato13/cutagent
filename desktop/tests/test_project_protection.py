"""Project saves must preserve recordings even through filesystem aliases."""
import os

import pytest

from anato12_studio.model import Media, Project


@pytest.mark.parametrize("alias", [False, True])
def test_project_save_cannot_replace_source(tmp_path, alias):
    source = tmp_path / "recording.mp4"
    source.write_bytes(b"original recording bytes")
    destination = source
    if alias:
        destination = tmp_path / "edit.anato12.json"
        os.link(source, destination)
    project = Project(media={"m": Media("m", str(source), 10, 320, 180)})
    with pytest.raises(ValueError, match="cannot replace a source"):
        project.save(destination)
    assert source.read_bytes() == b"original recording bytes"
    assert destination.read_bytes() == source.read_bytes()
    assert not list(tmp_path.glob(".anato12-project-*"))


def test_normal_project_save_and_overwrite_still_work(tmp_path):
    source = tmp_path / "recording.mp4"
    source.write_bytes(b"original")
    project = Project(media={"m": Media("m", str(source), 10, 320, 180)})
    destination = tmp_path / "edit.anato12.json"
    project.save(destination)
    project.burn_captions = True
    project.save(destination)
    assert Project.load(destination).burn_captions is True
    assert source.read_bytes() == b"original"
