"""Bounded-frame scene-change observations, not visual comprehension or cut truth."""
from pathlib import Path
import re
import tempfile


def observe_scene_changes(media, root, ffmpeg, runner, progress):
    """Stream the recording through small frames; retain at most 200 references."""
    count, references = 0, []
    with tempfile.TemporaryDirectory(prefix='scene-observations-', dir=root) as temporary:
        folder = Path(temporary)
        runner.run([ffmpeg, '-nostdin', '-hide_banner', '-i', str(Path(media.path).resolve()),
                    '-an', '-vf', "setpts=PTS-STARTPTS,fps=2,scale=160:-2,select='gt(scene,0.30)',metadata=print:file=scenes.txt",
                    '-progress', 'pipe:1', '-nostats', '-f', 'null', '-'], folder, media.duration,
                   lambda v: progress(v, 'Measuring possible visual scene changes'))
        path = folder / 'scenes.txt'
        if path.exists():
            with path.open(encoding='utf-8', errors='replace') as stream:
                for line in stream:
                    runner.check()
                    match = re.search(r'\bpts_time:([0-9]+(?:\.[0-9]+)?)', line)
                    if match:
                        point = float(match[1])
                        if 0 <= point < media.duration:
                            count += 1
                            if len(references) < 200:
                                references.append(point)
    return {'method': 'FFmpeg scene score > 0.30 at 2 sampled frames/second, 160px wide',
            'candidate_count': count, 'candidates_per_minute': count * 60 / media.duration,
            'candidate_seconds': references, 'omitted_references': max(0, count-len(references)),
            'interpretation': 'Possible scene changes; motion/flashes can trigger these. Fast cuts can be missed. '
                              'Not verified editing cuts, engaging sequences or visual technique recognition.'}
