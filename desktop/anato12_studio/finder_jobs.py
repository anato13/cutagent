"""Resumable pipeline orchestration and real frame extraction."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from .finder import analyze
from .local_model import LocalModel
from .personal_bridge import PersonalAIClient
from .model_policy import resource_snapshot
from .model import Media, Segment
from .store import fingerprint
from .video import Cancelled


def thumbnail_path(store, item):
    signature = json.dumps([item["source"], item["start"], item["end"]])
    return store.root / "thumbnails" / item["source"] / (hashlib.sha256(signature.encode()).hexdigest() + ".png")


def make_thumbnail(store, item, ffmpeg, runner):
    output = thumbnail_path(store, item)
    if output.exists():
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    source = store.get_source(item["source"])
    point = item["start"] + min(2, (item["end"]-item["start"])/2)
    part = output.with_suffix(".part.png")
    try:
        runner.run([ffmpeg, "-nostdin", "-hide_banner", "-y", "-ss", str(point),
                    "-i", source["path"], "-frames:v", "1",
                    "-vf", "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2",
                    "-progress", "pipe:1", "-nostats", str(part)],
                   output.parent, 1)
        part.replace(output)
    finally:
        part.unlink(missing_ok=True)
    return output


def extract_frame(media, second, ffmpeg, runner):
    """Decode one bounded JPEG at the playhead without loading the recording."""
    if not 0 <= second < media.duration:
        raise ValueError('Move the playhead inside the selected recording.')
    original = fingerprint(media.path)
    with TemporaryDirectory(prefix='anato12-frame-') as folder:
        root = Path(folder)
        target = root / 'frame.jpg'
        runner.run([ffmpeg, '-nostdin', '-hide_banner', '-y', '-ss', str(second),
                    '-i', media.path, '-frames:v', '1', '-vf', 'scale=640:-2',
                    '-q:v', '5', '-progress', 'pipe:1', '-nostats', str(target)], root, 1)
        if not target.is_file() or target.stat().st_size > 2_000_000:
            raise ValueError('FFmpeg could not make a small frame preview at this time.')
        frame = target.read_bytes()
    if fingerprint(media.path) != original:
        raise ValueError('The recording changed while extracting a frame; reimport it.')
    return frame


def run_pipeline(store, source, media: Media, params, job_id, ffmpeg, runner, progress, track_job=True):
    if track_job:
        store.update_job(job_id, "running", 0, "Starting")
    last_update = [0.0]
    last_progress = [0.0]
    def report(value, message):
        last_progress[0] = value
        progress(value, message)
        if track_job and time.monotonic()-last_update[0] >= 1:
            store.update_job(job_id, "running", value, message)
            last_update[0] = time.monotonic()
    try:
        if fingerprint(media.path) != source:
            raise ValueError("This source changed since the job was queued. Reimport it and start a new analysis.")
        segments = media.transcript
        saved = store.cache_get(f"analysis-transcript:{source}") if not segments else None
        if saved is not None:
            segments = [Segment(**s) for s in saved]
        if params.get("transcribe_only") or (not segments and saved is None):
            from .speech import transcribe
            root = Path(params["model_folder"]) if params.get("model_folder") else None
            segments = transcribe(media, ffmpeg, params["speech_model"], runner,
                                  lambda v, m: report(v*.65, m), root, cache=store)
        store.cache_put(f"analysis-transcript:{source}", source, "analysis_transcript",
                        [asdict(s) for s in segments])
        ids = []
        diagnostics = {}
        if not params.get("transcribe_only"):
            if not segments:
                raise ValueError('No timestamped dialogue was found. Import an SRT or check local transcription, then analyze again.')
            model = LocalModel(params["url"], params["model"]) if params.get("contextual") else None
            personal_notes = (PersonalAIClient().preferences(runner)
                              if model and params.get("personal_memory") else None)
            ids = analyze(store, source, segments, media.duration, runner,
                          lambda v, m: report(.65+v*.3, m), model, params.get("query", ""), diagnostics,
                          bool(model), personal_notes, bool(params.get('coverage', False)),
                          int(params.get('coverage_target', 3)))
            if model:
                diagnostics['resources_after_analysis'] = resource_snapshot()
                try:
                    diagnostics['running_models'] = model.running_models(runner)
                except (AttributeError, ValueError, RuntimeError):
                    diagnostics['running_models'] = []
            for i, identifier in enumerate(ids):
                runner.check()
                make_thumbnail(store, store.highlight(identifier), ffmpeg, runner)
                report(.95+.05*(i+1)/len(ids), f"Creating preview {i+1}/{len(ids)}")
        runner.check()
        if fingerprint(media.path) != source:
            raise ValueError("The recording changed during analysis. Results require a new source inspection.")
        if track_job:
            incomplete = len(diagnostics.get('invalid_sections', []))
            store.update_job(job_id, "completed", 1, f"Complete · {len(segments)} lines, {len(ids)} highlights · "
                             f"{diagnostics.get('mode', 'transcript only')}" +
                             (f' · {incomplete} invalid sections skipped' if incomplete else ''))
        return {"segments": segments, "ids": ids, "source": source, "job_id": job_id,
                "diagnostics": diagnostics}
    except Cancelled:
        if track_job:
            store.update_job(job_id, "cancelled", last_progress[0], "Cancelled; completed chunks/windows are cached")
        raise
    except Exception as error:
        try:
            if track_job:
                store.update_job(job_id, "failed", last_progress[0], str(error))
        except Exception:
            pass
        raise
