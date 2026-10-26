"""Cancellable media checks and real FFmpeg tests for a fixed operation library."""
import hashlib
from pathlib import Path
import tempfile

from .knowledge import RECIPES
from .model import Clip, Media, PROFILES, Segment
from .video import ExportPlan, export_video, probe


def engine_identity(ffmpeg, ffprobe):
    digest = hashlib.sha256()
    for path in (Path(ffmpeg), Path(ffprobe)):
        stat = path.stat()
        digest.update(f'{path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}'.encode())
    for name in ('quality.py', 'video.py', 'model.py', 'export_files.py', 'drafts.py'):
        digest.update(Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


def verify_video(path, project, ffmpeg, ffprobe, runner, progress=lambda *_: None):
    runner.check()
    metadata = probe(str(path), ffprobe)
    expected = sum(c.frame_range()[1] for c in project.clips)
    size = PROFILES[project.profile]
    if (metadata['width'], metadata['height']) != size:
        raise ValueError('Output dimensions do not match the requested format.')
    if abs(metadata['duration'] - expected) > .15:
        raise ValueError('Output duration does not match the planned clips.')
    # Export always supplies an audio stream, including silence for silent sources.
    if not metadata['has_audio']:
        raise ValueError('Output is missing its audio stream.')
    with tempfile.TemporaryDirectory(prefix='.anato12-check-', dir=path.parent) as temporary:
        runner.run([ffmpeg, '-nostdin', '-hide_banner', '-v', 'error', '-xerror', '-i', str(path.resolve()),
                    '-map', '0:v:0', '-map', '0:a:0', '-progress', 'pipe:1', '-nostats',
                    '-f', 'null', '-'], Path(temporary), expected,
                   lambda v: progress(v, 'Checking all exported video and audio frames'))
        if project.save_srt:
            from .model import write_srt
            reference = Path(temporary) / 'expected.srt'
            write_srt(reference, project.clips, project.media)
            if path.with_suffix('.srt').read_bytes() != reference.read_bytes():
                raise ValueError('Exported captions do not match the selected source dialogue and timing.')
    return {'status': 'passed', 'duration_seconds': metadata['duration'], 'expected_seconds': expected,
            'width': size[0], 'height': size[1], 'audio_stream': True, 'full_decode': 'passed',
            'humor_quality': 'NOT_EVALUATED', 'story_quality': 'NOT_EVALUATED'}


def verify_bundle(folder, manifest, ffmpeg, ffprobe, runner, progress):
    from .model import Project
    outputs = manifest['outputs']
    for i, entry in enumerate(outputs):
        runner.check()
        project = Project.load(folder / entry['project'])
        entry['quality'] = verify_video(folder / entry['video'], project, ffmpeg, ffprobe, runner,
            lambda v, m: progress((i+v)/len(outputs), m))
    manifest['quality_scope'] = 'Dimensions, planned duration, audio stream, SRT bounds and full decode. Not comedy/story acceptance.'


def ensure_capabilities(store, required, ffmpeg, ffprobe, runner, progress):
    """Imported examples cannot mark recipes as passed; only these real exports can."""
    if not required or any(recipe not in RECIPES for recipe in required):
        raise ValueError('Unknown or empty executable technique list.')
    engine = engine_identity(ffmpeg, ffprobe)
    latest = {}
    for row in store.technique_results():
        if row['engine'] == engine:
            latest.setdefault(row['recipe'], row)
    pending = [r for r in dict.fromkeys(required) if not latest.get(r, {}).get('passed')]
    if not pending:
        return engine
    with tempfile.TemporaryDirectory(prefix='capability-', dir=store.root) as temporary:
        folder = Path(temporary)
        source = folder / 'fixture.mp4'
        runner.run([ffmpeg, '-nostdin', '-hide_banner', '-y', '-f', 'lavfi', '-i',
                    'testsrc2=size=320x180:rate=30:duration=1', '-f', 'lavfi', '-i',
                    'sine=frequency=440:duration=1', '-c:v', 'libx264', '-preset', 'ultrafast',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', str(source)], folder, 1)
        media = Media('capability', str(source), **probe(str(source), ffprobe),
                      transcript=[Segment(0, .45, 'Caption setup'), Segment(.5, 1, 'Caption reply')])
        for i, recipe in enumerate(pending):
            runner.check()
            from .model import Project
            clips = [Clip(media.id, .1, .4), Clip(media.id, .6, .9)]
            if recipe == 'zoom':
                clips[1].zoom = 1.25
            project = Project(media={media.id: media}, clips=clips,
                              profile='Shorts · 9:16' if recipe == 'portrait_fit' else 'YouTube · 16:9',
                              burn_captions=recipe == 'captions', save_srt=recipe == 'captions')
            output = folder / f'{recipe}.mp4'
            try:
                export_video(ExportPlan(project.media, clips, output, project.profile,
                                       project.burn_captions, project.save_srt), ffmpeg, runner)
                report = verify_video(output, project, ffmpeg, ffprobe, runner)
                report['scope'] = 'Synthetic execution/decode test; not visual or editorial acceptance.'
                store.record_technique_test(recipe, engine, True, report)
            except Exception as error:
                store.record_technique_test(recipe, engine, False, {'error': str(error)})
                raise
            progress((i+1)/len(pending), f'Tested {recipe}')
    return engine
