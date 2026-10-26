"""FFmpeg discovery, probing and cancellable, transactional rendering."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from typing import Callable

from .model import Clip, Media, PROFILES, write_ass, write_srt

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def find_tool(name: str, folder: str = "") -> str:
    override = os.environ.get(f"ANATO12_{name.upper()}")
    candidates = [override] if override else []
    suffix = ".exe" if os.name == "nt" else ""
    if folder:
        candidates += [str(Path(folder) / (name + suffix)),
                       str(Path(folder) / "bin" / (name + suffix))]
    candidates += [shutil.which(name)]
    root = (Path(sys.executable).parent if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parents[1])
    candidates += [str(root / "tools" / "ffmpeg" / "bin" / (name + suffix))]
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        candidates += [str(local / "Microsoft" / "WinGet" / "Links" / (name + suffix))]
        packages = local / "Microsoft" / "WinGet" / "Packages"
        if packages.is_dir():
            for package in packages.glob("Gyan.FFmpeg*"):
                candidates += [str(p) for p in package.glob(f"*/bin/{name}.exe")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise FileNotFoundError(
        f"{name} was not found. Install FFmpeg, restart the app, or choose its bin folder "
        "in Settings. See START_HERE.md."
    )


def probe(path: str, ffprobe: str) -> dict:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", path],
        capture_output=True, text=True, timeout=45, creationflags=NO_WINDOW,
    )
    if result.returncode:
        raise ValueError("Could not read this video.\n" + result.stderr[-1500:])
    data = json.loads(result.stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"
                  and not s.get("disposition", {}).get("attached_pic")), None)
    if not video:
        raise ValueError("This file has no usable video stream.")
    duration = float(data.get("format", {}).get("duration") or video.get("duration") or 0)
    if not math.isfinite(duration) or duration < 1 / 30:
        raise ValueError("The recording has no readable duration. Try remuxing it to MP4.")
    width, height = int(video["width"]), int(video["height"])
    rotation = float(video.get("tags", {}).get("rotate", 0))
    for side in video.get("side_data_list", []):
        rotation = float(side.get("rotation", rotation))
    if round(abs(rotation)) % 180 == 90:
        width, height = height, width
    return dict(duration=duration, width=width, height=height,
                has_audio=any(s.get("codec_type") == "audio" for s in data["streams"]))


def layout(sw: float, sh: float, width: int, height: int, clip: Clip):
    scale = min(width / sw, height / sh) if clip.fit == "fit" else max(width / sw, height / sh)
    base_w, base_h = sw * scale, sh * scale
    # Framing happens before the full output frame is zoomed.
    x = (width - base_w) * (clip.focus_x if clip.fit == "fill" else .5)
    y = (height - base_h) * (clip.focus_y if clip.fit == "fill" else .5)
    zoom_w, zoom_h = math.ceil(width * clip.zoom / 2) * 2, math.ceil(height * clip.zoom / 2) * 2
    zx, zy = zoom_w / width, zoom_h / height
    return (x * zx - (zoom_w - width) * clip.focus_x,
            y * zy - (zoom_h - height) * clip.focus_y, base_w * zx, base_h * zy)


def video_filter(width: int, height: int, clip: Clip, captions: bool = False) -> str:
    if clip.fit == "fit":
        filters = [f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2",
                   f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x0b0e14"]
    else:
        filters = [f"scale={width}:{height}:force_original_aspect_ratio=increase:force_divisible_by=2",
                   f"crop={width}:{height}:(iw-ow)*{clip.focus_x:.6f}:(ih-oh)*{clip.focus_y:.6f}"]
    if clip.zoom > 1:
        w, h = math.ceil(width * clip.zoom / 2) * 2, math.ceil(height * clip.zoom / 2) * 2
        filters += [f"scale={w}:{h}",
                    f"crop={width}:{height}:(iw-ow)*{clip.focus_x:.6f}:(ih-oh)*{clip.focus_y:.6f}"]
    filters += ["setsar=1", "fps=30", "setpts=PTS-STARTPTS"]
    if captions:
        # Fixed relative filename avoids Windows drive-letter/filter escaping problems.
        filters.append("ass=filename=captions.ass")
    return ",".join(filters)


class Cancelled(Exception):
    pass


class Runner:
    def __init__(self):
        self.stopped = threading.Event()
        self.process: subprocess.Popen | None = None

    def cancel(self):
        self.stopped.set()
        proc = self.process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                timer = threading.Timer(2, lambda: proc.kill() if proc.poll() is None else None)
                timer.daemon = True
                timer.start()
            except OSError:
                pass

    def check(self):
        if self.stopped.is_set():
            raise Cancelled("Cancelled. Your source files and existing exports were kept.")

    def run(self, args: list[str], cwd: Path, duration: float,
            progress: Callable[[float], None] = lambda _: None):
        self.check()
        log = cwd / "ffmpeg.log"
        with log.open("w", encoding="utf-8") as errors:
            self.process = subprocess.Popen(
                args, cwd=cwd, stdout=subprocess.PIPE, stderr=errors,
                text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW,
            )
            try:
                assert self.process.stdout
                for line in self.process.stdout:
                    self.check()
                    if line.startswith("out_time_us="):
                        try:
                            progress(min(.999, int(line.split("=")[1]) / 1e6 / duration))
                        except ValueError:
                            pass
                code = self.process.wait()
            finally:
                if self.process.poll() is None:
                    self.process.kill()
                    self.process.wait()
                self.process.stdout.close()
                self.process = None
        self.check()
        if code:
            raise RuntimeError("FFmpeg could not finish this operation:\n" +
                               log.read_text(encoding="utf-8", errors="replace")[-4000:])
        progress(1)


@dataclass
class ExportPlan:
    media: dict[str, Media]
    clips: list[Clip]
    destination: Path
    profile: str = "YouTube · 16:9"
    burn_captions: bool = False
    save_srt: bool = True
    overwrite: bool = False

    def validate(self):
        if self.profile not in PROFILES or not self.clips:
            raise ValueError("Choose an export format and at least one clip.")
        if self.destination.suffix.lower() != ".mp4":
            raise ValueError("Choose an output filename ending in .mp4.")
        if not self.destination.parent.is_dir():
            raise ValueError("The output folder does not exist.")
        for clip in self.clips:
            media = self.media[clip.media_id]
            clip.validate(media)
            if not Path(media.path).is_file():
                raise ValueError(f"Source recording is missing: {media.path}")
        targets = [self.destination]
        if self.save_srt:
            targets.append(self.destination.with_suffix(".srt"))
        # Protect every imported source from either output, including aliases.
        for media in self.media.values():
            source = Path(media.path)
            for target in targets:
                if os.path.normcase(str(source.resolve())) == os.path.normcase(str(target.resolve())):
                    raise ValueError("Choose a new filename. An export cannot replace a source recording.")
                if source.exists() and target.exists() and source.samefile(target):
                    raise ValueError("The output points to a source recording.")
        if not self.overwrite and any(p.exists() for p in targets):
            raise FileExistsError("An output file already exists. Choose a new filename.")


def export_video(plan: ExportPlan, ffmpeg: str, runner: Runner,
                 progress: Callable[[float, str], None] = lambda *_: None) -> str:
    plan.validate()
    width, height = PROFILES[plan.profile]
    if plan.burn_captions:
        result = subprocess.run([ffmpeg, "-hide_banner", "-filters"], capture_output=True,
                                text=True, timeout=20, creationflags=NO_WINDOW)
        if " ass " not in result.stdout:
            raise RuntimeError("This FFmpeg build cannot burn captions. Disable burned-in captions "
                               "and export an SRT, or install a full FFmpeg build with libass.")
    temporary_output = plan.destination.with_name(f".anato12-{uuid.uuid4().hex}.mp4")
    total = sum(c.frame_range()[1] for c in plan.clips)
    try:
        with tempfile.TemporaryDirectory(prefix="anato12-") as temp:
            folder = Path(temp)
            intermediates = []
            elapsed = 0.0
            for index, clip in enumerate(plan.clips):
                runner.check()
                media = plan.media[clip.media_id]
                start, duration = clip.frame_range()
                clip_folder = folder / str(index)
                clip_folder.mkdir()
                write_ass(clip_folder / "captions.ass", media.transcript, start, duration, width, height)
                intermediate = clip_folder / "clip.mkv"
                args = [ffmpeg, "-nostdin", "-hide_banner", "-y", "-ss", f"{start:.9f}",
                        "-i", media.path]
                if not media.has_audio:
                    args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
                args += ["-map", "0:v:0", "-map", "0:a:0" if media.has_audio else "1:a:0",
                         "-t", f"{duration:.9f}", "-vf", video_filter(width, height, clip, plan.burn_captions),
                         "-af", f"aresample=48000,apad,atrim=duration={duration:.9f},asetpts=PTS-STARTPTS",
                         "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-threads", "2",
                         "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
                         "-metadata:s:v:0", "rotate=0", "-progress", "pipe:1", "-nostats", str(intermediate)]
                runner.run(args, clip_folder, duration,
                           lambda p, e=elapsed, d=duration, i=index:
                           progress((e + d * p) / total * .9, f"Rendering clip {i+1}/{len(plan.clips)}"))
                elapsed += duration
                intermediates.append(intermediate)
            # Temp directory paths are generated by us. Use relative names in the list.
            (folder / "clips.txt").write_text(
                "".join(f"file '{i}/clip.mkv'\n" for i in range(len(intermediates))), encoding="utf-8")
            runner.run(
                [ffmpeg, "-nostdin", "-hide_banner", "-y", "-f", "concat", "-safe", "0",
                 "-i", "clips.txt", "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total:.9f}",
                 "-movflags", "+faststart", "-progress", "pipe:1", "-nostats", str(temporary_output)],
                folder, total, lambda p: progress(.9 + p * .1, "Finishing MP4"),
            )
            runner.check()
            if temporary_output.stat().st_size < 100:
                raise RuntimeError("The output was empty.")
            # Recheck immediately before committing; never replace a source.
            plan.validate()
            srt = folder / "captions.srt"
            if plan.save_srt:
                write_srt(srt, plan.clips, plan.media)
            os.replace(temporary_output, plan.destination)
            if plan.save_srt:
                # Copy through a sibling so a cross-drive TEMP folder is supported on Windows.
                sidecar = plan.destination.with_suffix(".srt")
                part = sidecar.with_name(f".anato12-{uuid.uuid4().hex}.srt")
                try:
                    shutil.copyfile(srt, part)
                    os.replace(part, sidecar)
                finally:
                    part.unlink(missing_ok=True)
        progress(1, "Export complete")
        return str(plan.destination)
    finally:
        temporary_output.unlink(missing_ok=True)
