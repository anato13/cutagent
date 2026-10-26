"""Optional Whisper ONNX inference. No video/audio is uploaded to any service."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path
import tarfile
import tempfile
import urllib.request
import wave

from .model import Media, Segment
from .video import Runner

MODELS = {"tiny.en": "~110 MB", "base.en": "~200 MB", "small.en": "~640 MB"}
MODEL_HOST = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"


def model_folder() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "Anato12Studio" / "models"


def model_files(folder: Path, name: str) -> tuple[Path, Path, Path]:
    return (folder / f"{name}-encoder.int8.onnx",
            folder / f"{name}-decoder.int8.onnx", folder / f"{name}-tokens.txt")


def model_ready(folder: Path, name: str) -> bool:
    encoder, decoder, tokens = model_files(folder, name)
    return (encoder.is_file() and encoder.stat().st_size > 1_000_000
            and decoder.is_file() and decoder.stat().st_size > 1_000_000
            and tokens.is_file() and tokens.stat().st_size > 1000)


def ensure_model(name: str, root: Path, runner: Runner, progress) -> Path:
    if name not in MODELS:
        raise ValueError("Choose tiny.en, base.en or small.en.")
    target = root / f"sherpa-onnx-whisper-{name}"
    if model_ready(target, name):
        return target
    root.mkdir(parents=True, exist_ok=True)
    url = f"{MODEL_HOST}/sherpa-onnx-whisper-{name}.tar.bz2"
    progress(0, f"Downloading {name} ({MODELS[name]}) · recording stays local")
    # Work beside the destination for same-filesystem, atomic publication.
    with tempfile.TemporaryDirectory(prefix=".download-", dir=root) as temporary:
        working = Path(temporary)
        archive = working / "model.tar.bz2"
        digest = hashlib.sha256()
        request = urllib.request.Request(url, headers={"User-Agent": "Anato12-Studio/0.1"})
        # Python's default HTTPS certificate verification is intentionally retained.
        with urllib.request.urlopen(request, timeout=45) as response, archive.open("wb") as output:
            total = int(response.headers.get("Content-Length", 0))
            received = 0
            while True:
                runner.check()
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                received += len(chunk)
                if received > 2_000_000_000:
                    raise ValueError("The model download exceeded its expected size limit.")
                digest.update(chunk)
                output.write(chunk)
                fraction = min(.14, .14 * received / total) if total else 0
                progress(fraction, f"Downloading {name} · {received//1_000_000} MB")
            if total and received != total:
                raise ValueError("The model download was incomplete. Please retry.")
        extracted = working / "model"
        extracted.mkdir()
        wanted = {p.name for p in model_files(extracted, name)}
        found = set()
        # Never extract paths, links, executables, or unneeded float32 weights.
        with tarfile.open(archive, "r|bz2") as tar:
            for member in tar:
                runner.check()
                filename = Path(member.name).name
                if filename not in wanted:
                    continue
                if not member.isfile() or not 1000 <= member.size <= 1_500_000_000:
                    raise ValueError("Unexpected speech-model archive entry.")
                if filename in found:
                    raise ValueError("Duplicate speech-model archive entry.")
                source = tar.extractfile(member)
                if source is None:
                    raise ValueError("Unreadable speech model.")
                with source, (extracted / filename).open("wb") as output:
                    while chunk := source.read(256 * 1024):
                        runner.check()
                        output.write(chunk)
                found.add(filename)
        if found != wanted or not model_ready(extracted, name):
            raise ValueError("The model archive did not contain the expected ONNX files.")
        (extracted / "download.json").write_text(json.dumps(
            {"url": url, "archive_sha256": digest.hexdigest(),
             "note": "Archive downloaded over verified HTTPS; this local hash records the download."},
            indent=2), encoding="utf-8")
        if target.exists():
            # Do not overwrite an existing incomplete/user-supplied folder silently.
            raise ValueError(f"The model folder is incomplete: {target}. "
                             "Move that folder aside and try again.")
        extracted.rename(target)
    return target


def transcribe(media: Media, ffmpeg: str, name: str, runner: Runner, progress,
               root: Path | None = None) -> list[Segment]:
    if importlib.util.find_spec("sherpa_onnx") is None:
        if getattr(sys, "frozen", False):
            raise RuntimeError("This EXE was built without optional speech tools. Use the source app, "
                               "run INSTALL_SPEECH.bat, then rebuild with BUILD_WINDOWS.bat.")
        raise RuntimeError("Optional speech tools are not installed. Close the app, double-click "
                           "INSTALL_SPEECH.bat, then reopen it. Import/preview/export work without them.")
    import numpy as np
    import sherpa_onnx
    if not media.has_audio:
        raise ValueError("This recording has no audio track.")
    folder = ensure_model(name, root or model_folder(), runner, progress)
    runner.check()
    encoder, decoder, tokens = model_files(folder, name)
    recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=str(encoder), decoder=str(decoder), tokens=str(tokens),
        num_threads=max(1, min(4, os.cpu_count() or 2)), language="en", task="transcribe",
        enable_segment_timestamps=True,
    )
    segments = []
    with tempfile.TemporaryDirectory(prefix="anato12-speech-") as temporary:
        working = Path(temporary)
        audio_path = working / "speech.wav"
        # Quiet dialogue is leveled before recognition; this does not modify the recording.
        runner.run([ffmpeg, "-nostdin", "-hide_banner", "-y", "-i", media.path, "-vn",
                    "-af", "highpass=f=70,dynaudnorm=f=150:g=15:p=0.9:m=20:r=0.15",
                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
                    "-progress", "pipe:1", "-nostats", str(audio_path)],
                   working, media.duration,
                   lambda value: progress(.15 + value * .1, "Preparing dialogue audio"))
        with wave.open(str(audio_path), "rb") as audio:
            rate = audio.getframerate()
            duration = min(media.duration, audio.getnframes() / rate)
            count = math.ceil(duration / 27)
            for index in range(count):
                runner.check()
                start = index * 27.0
                length = min(28.0, duration - start)
                audio.setpos(round(start * rate))
                samples = np.frombuffer(audio.readframes(round(length * rate)),
                                        dtype=np.int16).astype(np.float32) / 32768
                if len(samples) == 0:
                    continue
                rms = float(np.sqrt(np.mean(samples * samples)))
                if rms < .001:
                    continue
                stream = recognizer.create_stream()
                stream.accept_waveform(rate, samples)
                recognizer.decode_stream(stream)
                runner.check()
                result = json.loads(str(stream.result))
                times = result.get("segment_timestamps", [])
                lengths = result.get("segment_durations", [])
                texts = result.get("segment_texts", [])
                for offset, spoken, text in zip(times, lengths, texts):
                    a, b = start + float(offset), min(duration, start + float(offset) + float(spoken))
                    text = str(text).strip()
                    if not text or b <= a:
                        continue
                    # Ignore overlap-only phrases already recognized in the previous window.
                    if index and (a + b) / 2 < start + .5:
                        continue
                    if index < count-1 and (a + b) / 2 >= start + 27.5:
                        continue
                    if segments and text.casefold() == segments[-1].text.casefold() and a < segments[-1].end + 2:
                        continue
                    a = max(a, segments[-1].end if segments else 0)
                    if b > a:
                        segments.append(Segment(round(a, 3), round(b, 3), text))
                progress(.25 + .75 * (index+1)/count,
                         f"Transcribing {index+1}/{count} · local CPU")
    progress(1, f"Transcription complete · {len(segments)} lines")
    return segments
