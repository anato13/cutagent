"""Conservative, inspectable cues for possible funny/reaction moments."""
from dataclasses import dataclass
import re
from .model import Segment


@dataclass
class Moment:
    start: float
    end: float
    reason: str
    text: str
    score: int


CUES = [
    (r"\b(laughs?|laughing|laughter|lol|lmao|hilarious)\b", 5, "Laughter cue"),
    (r"\b(no way|what just happened|are you kidding|oh my god|oh my gosh|what the heck)\b",
     4, "Surprised reaction"),
    (r"\b(i can't believe|you did what|did that just|unbelievable|wait a minute|plot twist)\b",
     4, "Possible surprise"),
    (r"\b(oops|my bad|i messed up|i'm dead|we're dead|that was close|nice try)\b",
     3, "Possible gaming reaction"),
]


def suggest_moments(segments: list[Segment], duration: float, limit: int = 20) -> list[Moment]:
    candidates = []
    ordered = sorted(segments, key=lambda s: s.start)
    for i, segment in enumerate(ordered):
        if not segment.text.strip():
            continue
        score, reason = 0, ""
        for pattern, points, label in CUES:
            if re.search(pattern, segment.text, re.I):
                score += points
                reason = reason or label
        if re.search(r"[!?]{2,}", segment.text):
            score += 2
            reason = reason or "Emphatic reaction"
        # Do not assign a score for generic words such as "bro" or ordinary speech.
        if score < 3:
            continue
        start = max(0, segment.start - 4)
        end = min(duration, max(segment.end + 5, start + 10))
        # Keep an adjacent setup line if close enough; avoid disconnected punchlines.
        if i and 0 <= segment.start - ordered[i-1].end <= 2:
            start = min(start, ordered[i-1].start)
        if end - start > 40:
            start = max(0, segment.start - 4)
            end = min(duration, start + 40)
        candidates.append(Moment(start, end, reason, segment.text, score))
    chosen = []
    for candidate in sorted(candidates, key=lambda m: (-m.score, m.start)):
        overlap = any(max(0, min(candidate.end, m.end) - max(candidate.start, m.start)) >
                      min(candidate.end-candidate.start, m.end-m.start) * .5 for m in chosen)
        if not overlap:
            chosen.append(candidate)
        if len(chosen) == limit:
            break
    return sorted(chosen, key=lambda m: m.start)
