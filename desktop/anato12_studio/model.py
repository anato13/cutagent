"""Portable project data and validation, independent of the desktop UI."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
import tempfile
import uuid


def number(value: object, low: float, high: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or not low <= result <= high:
        raise ValueError(f"{name} must be between {low:g} and {high:g}.")
    return result


def timestamp(seconds: float) -> str:
    ms = round(max(0, seconds) * 1000)
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    whole, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{whole:02}.{ms:03}"


def parse_time(text: str) -> float:
    parts = text.strip().split(":")
    if not 1 <= len(parts) <= 3:
        raise ValueError("Use seconds or HH:MM:SS.mmm.")
    total = 0.0
    for part in parts:
        total = total * 60 + number(part, 0, 1_000_000, "Time")
    return total


@dataclass
class Segment:
    start: float
    end: float
    text: str

    def validate(self, duration: float) -> None:
        self.start = number(self.start, 0, duration, "Caption start")
        self.end = number(self.end, 0, duration, "Caption end")
        if self.end <= self.start:
            raise ValueError("A caption must end after it starts.")
        if not isinstance(self.text, str) or len(self.text) > 20_000:
            raise ValueError("Invalid caption text.")


@dataclass
class Media:
    id: str
    path: str
    duration: float
    width: int
    height: int
    has_audio: bool = True
    transcript: list[Segment] = field(default_factory=list)

    @property
    def name(self) -> str:
        return Path(self.path).name


@dataclass
class Clip:
    media_id: str
    start: float
    end: float
    name: str = "Clip"
    enabled: bool = True
    zoom: float = 1.0
    focus_x: float = 0.5
    focus_y: float = 0.5
    fit: str = "fit"

    def validate(self, media: Media) -> None:
        if not isinstance(self.name, str) or not isinstance(self.enabled, bool):
            raise ValueError("Invalid clip name or selection.")
        self.start = number(self.start, 0, media.duration, "In point")
        self.end = number(self.end, 0, media.duration, "Out point")
        if self.end - self.start < 1 / 30:
            raise ValueError("Select at least one video frame (1/30 second).")
        self.zoom = number(self.zoom, 1, 2, "Zoom")
        self.focus_x = number(self.focus_x, 0, 1, "Horizontal framing")
        self.focus_y = number(self.focus_y, 0, 1, "Vertical framing")
        if self.fit not in ("fit", "fill"):
            raise ValueError("Unknown framing mode.")

    def frame_range(self, fps: int = 30) -> tuple[float, float]:
        first = round(self.start * fps)
        last = max(first + 1, round(self.end * fps))
        return first / fps, (last - first) / fps


PROFILES = {"YouTube · 16:9": (1920, 1080), "Shorts · 9:16": (1080, 1920)}


@dataclass
class Project:
    media: dict[str, Media] = field(default_factory=dict)
    clips: list[Clip] = field(default_factory=list)
    profile: str = "YouTube · 16:9"
    burn_captions: bool = False
    save_srt: bool = True

    def add_media(self, path: str, **metadata: object) -> Media:
        canonical = str(Path(path).resolve())
        for item in self.media.values():
            if item.path == canonical:
                return item
        item = Media(id=uuid.uuid4().hex, path=canonical, **metadata)
        self.media[item.id] = item
        return item

    def save(self, path: Path) -> None:
        path = Path(path)
        for media in self.media.values():
            source = Path(media.path)
            if (source.resolve() == path.resolve() or
                    (source.exists() and path.exists() and source.samefile(path))):
                raise ValueError("Choose a different project filename. A project cannot replace a source recording.")
        data = {"version": 1, **asdict(self)}
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".anato12-project-", suffix=".tmp", delete=False) as f:
            temporary = Path(f.name)
            try:
                f.write(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception:
                f.close()
                temporary.unlink(missing_ok=True)
                raise
        try:
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    @classmethod
    def load(cls, path: Path) -> Project:
        if path.stat().st_size > 50_000_000:
            raise ValueError("This project file is too large.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") != 1:
            raise ValueError("Unsupported project version.")
        profile = data.get("profile", "YouTube · 16:9")
        if profile not in PROFILES:
            raise ValueError("Unknown video profile.")
        project = cls(profile=profile, burn_captions=bool(data.get("burn_captions", False)),
                      save_srt=bool(data.get("save_srt", True)))
        for key, value in data.get("media", {}).items():
            value = dict(value)
            transcript = [Segment(**s) for s in value.pop("transcript", [])]
            media = Media(**value, transcript=transcript)
            if media.id != key or not isinstance(media.path, str):
                raise ValueError("Invalid media entry.")
            media.duration = number(media.duration, 1/30, 1_000_000, "Video duration")
            media.width = int(number(media.width, 1, 32768, "Video width"))
            media.height = int(number(media.height, 1, 32768, "Video height"))
            for segment in media.transcript:
                segment.validate(media.duration)
            project.media[key] = media
        for value in data.get("clips", []):
            clip = Clip(**value)
            if clip.media_id not in project.media:
                raise ValueError("A clip references missing media.")
            clip.validate(project.media[clip.media_id])
            project.clips.append(clip)
        return project


def caption_style(width: int, height: int) -> tuple[int, int]:
    return round(min(width * .065, height * .05)), round(height * .1)


def caption_intersections(segments: list[Segment], start: float, duration: float):
    for segment in sorted(segments, key=lambda x: x.start):
        a, b = max(start, segment.start), min(start + duration, segment.end)
        if b > a and segment.text.strip():
            yield Segment(a - start, b - start, segment.text.strip())


def write_srt(path: Path, clips: list[Clip], media: dict[str, Media]) -> None:
    entries = []
    offset = 0.0
    for clip in clips:
        start, duration = clip.frame_range()
        for segment in caption_intersections(media[clip.media_id].transcript, start, duration):
            a = timestamp(offset + segment.start).replace(".", ",")
            b = timestamp(offset + segment.end).replace(".", ",")
            entries.append(f"{len(entries)+1}\n{a} --> {b}\n{segment.text}\n")
        offset += duration
    path.write_text("\n".join(entries), encoding="utf-8")


def write_ass(path: Path, segments: list[Segment], start: float, duration: float,
              width: int, height: int) -> None:
    size, margin = caption_style(width, height)
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\nWrapStyle: 0\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,Arial,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,"
        f"-1,0,0,0,100,100,0,0,1,3,1,2,{round(width*.07)},{round(width*.07)},{margin},1\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    def ass_time(t: float) -> str:
        centiseconds = round(t * 100)
        hours, remainder = divmod(centiseconds, 360000)
        minutes, remainder = divmod(remainder, 6000)
        seconds, centiseconds = divmod(remainder, 100)
        return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"
    rows = []
    for s in caption_intersections(segments, start, duration):
        text = s.text.replace("\\", "＼").replace("{", "｛").replace("}", "｝")
        text = text.replace("\r", "").replace("\n", r"\N")
        rows.append(f"Dialogue: 0,{ass_time(s.start)},{ass_time(s.end)},Default,,0,0,0,,{text}\n")
    path.write_text(header + "".join(rows), encoding="utf-8-sig")
