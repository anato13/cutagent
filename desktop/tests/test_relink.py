from dataclasses import asdict
import pytest
from anato12_studio.model import Project, Media, Clip, Segment


@pytest.mark.parametrize('kind', ['clip', 'caption', 'duration'])
def test_failed_relink_preserves_entire_project(tmp_path, kind):
    media = Media('m', str(tmp_path/'old.mp4'), 10, 320, 180)
    project = Project(media={'m': media})
    if kind == 'clip':
        project.clips = [Clip('m', 9, 10)]
    if kind == 'caption':
        media.transcript = [Segment(9, 10, 'ending')]
    before = asdict(project)
    with pytest.raises(ValueError):
        project.relink_media('m', tmp_path/'new.mp4', dict(duration=8 if kind == 'duration' else 9.5,
                             width=640, height=360, has_audio=False))
    assert asdict(project) == before


def test_successful_relink_uses_actual_duration(tmp_path):
    project = Project(media={'m': Media('m', str(tmp_path/'old.mp4'), 10, 320, 180)},
                      clips=[Clip('m', 1, 5)])
    result = project.relink_media('m', tmp_path/'new.mp4',
                                 dict(duration=9.5, width=640, height=360, has_audio=False))
    assert project.media['m'] is result
    assert (result.duration, result.width, result.has_audio) == (9.5, 640, False)
    assert project.clips[0].end == 5
