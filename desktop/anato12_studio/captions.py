"""Import plain UTF-8 SRT captions."""
from pathlib import Path
import re

from .model import Segment, parse_time


def read_srt(path: Path, duration: float) -> list[Segment]:
    if path.stat().st_size > 20_000_000:
        raise ValueError("This caption file is too large.")
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    pattern = re.compile(
        r"(?m)^\s*(\d{1,3}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*"
        r"(\d{1,3}:\d{2}:\d{2}[,.]\d{1,3})[^\n]*\n(.*?)(?=\n\s*\n|\Z)", re.S)
    segments = []
    for match in pattern.finditer(text):
        start, end = [parse_time(t.replace(",", ".")) for t in match.group(1, 2)]
        if start >= duration:
            continue
        segment = Segment(start, min(end, duration), match.group(3).strip())
        segment.validate(duration)
        if segment.text:
            segments.append(segment)
    if not segments:
        raise ValueError("No captions were found within this recording. Use a UTF-8 .srt file "
                         "whose timestamps match the original recording.")
    return sorted(segments, key=lambda s: s.start)
