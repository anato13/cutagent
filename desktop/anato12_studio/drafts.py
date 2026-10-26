"""Create independent, editable drafts using only explicitly approved ranges."""
import copy
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import tempfile
import uuid

from .model import Clip, Project, number
from .store import fingerprint
from .video import ExportPlan, export_video


@dataclass
class DraftOptions:
    max_short_seconds: float = 60
    short_fit: str = "fit"
    burn_captions: bool = False
    save_srt: bool = False
    render: bool = False

    def validate(self):
        self.max_short_seconds = number(self.max_short_seconds, 1, 180, "Maximum Short length")
        if self.short_fit not in {"fit", "fill"}:
            raise ValueError("Choose fit or fill framing.")
        if any(type(v) is not bool for v in (self.burn_captions, self.save_srt, self.render)):
            raise ValueError("Invalid draft caption/render option.")


def assemble(media, source, highlights, options):
    """Chronological main cut merges overlaps; Shorts keep complete approved ranges."""
    options.validate()
    approved = [h for h in highlights if h["source"] == source and h["status"] == "approved"]
    if not approved:
        raise ValueError("Approve at least one highlight for this recording first.")
    if (options.burn_captions or options.save_srt) and not media.transcript:
        raise ValueError("Add captions before creating drafts with captions enabled.")
    items = []
    for item in approved:
        clip = Clip(media.id, item["start"], item["end"], item["title"])
        clip.validate(media)
        items.append((clip, item["id"]))
    items.sort(key=lambda pair: (pair[0].start, pair[0].end, pair[1]))
    main = Project(media={media.id: copy.deepcopy(media)}, burn_captions=options.burn_captions,
                   save_srt=options.save_srt)
    shorts, skipped, included, seen = [], [], [], set()
    for clip, identifier in items:
        included.append(identifier)
        if main.clips and clip.start <= main.clips[-1].end:
            previous = main.clips[-1]
            previous.end = max(previous.end, clip.end)
            if previous.name != clip.name:
                previous.name = (previous.name + " / " + clip.name)[:180]
        else:
            main.clips.append(copy.deepcopy(clip))
        start, duration = clip.frame_range()
        signature = (start, duration)
        if signature in seen:
            skipped.append({"highlight": identifier, "reason": "Duplicate frame range"})
            continue
        seen.add(signature)
        if duration > options.max_short_seconds + .00001:
            skipped.append({"highlight": identifier,
                            "reason": "Approved range exceeds the selected Short limit; no automatic truncation"})
            continue
        short_clip = copy.deepcopy(clip)
        short_clip.fit = options.short_fit
        shorts.append((identifier, Project(media={media.id: copy.deepcopy(media)}, clips=[short_clip],
                         profile="Shorts · 9:16", burn_captions=options.burn_captions,
                         save_srt=options.save_srt)))
    return main, shorts, {"approved_highlights": included, "shorts_skipped": skipped}


def create_bundle(media, source, highlights, parent, options, ffmpeg, runner, progress):
    runner.check()
    if fingerprint(media.path) != source:
        raise ValueError("The recording changed. Reimport and review it before making drafts.")
    main, shorts, details = assemble(media, source, highlights, options)
    parent = Path(parent).resolve()
    if not parent.is_dir():
        raise ValueError("Choose an existing folder for the draft bundle.")
    name = "Anato12-drafts-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:12]
    destination = parent / name
    plans = [("YouTube.anato12.json", main, None)]
    plans += [(f"Short-{i:03}.anato12.json", project, identifier)
              for i, (identifier, project) in enumerate(shorts, 1)]
    # Work only inside a newly owned temporary directory. Publish after all work succeeds.
    with tempfile.TemporaryDirectory(prefix=".anato12-drafts-", dir=parent) as temporary:
        working = Path(temporary)
        manifest = {"version": 1, "source_fingerprint": source, "source_path": media.path,
                    "assembly": "Approved ranges in recording order; overlapping main ranges merged.",
                    "short_framing": options.short_fit, "max_short_seconds": options.max_short_seconds,
                    **details, "outputs": []}
        for i, (filename, project, identifier) in enumerate(plans):
            runner.check()
            project.save(working / filename)
            entry = {"project": filename, "highlight": identifier, "profile": project.profile,
                     "duration_seconds": sum(c.frame_range()[1] for c in project.clips)}
            if options.render:
                video = filename.removesuffix(".anato12.json") + ".mp4"
                export_video(ExportPlan(project.media, project.clips, working / video,
                    project.profile, project.burn_captions, project.save_srt), ffmpeg, runner,
                    lambda value, message: progress((i+value)/len(plans),
                                                    f"{i+1}/{len(plans)} · {message}"))
                entry["video"] = video
                if project.save_srt:
                    entry["captions"] = Path(video).with_suffix(".srt").name
            manifest["outputs"].append(entry)
            progress((i+1)/len(plans), f"Prepared {filename}")
        runner.check()
        if fingerprint(media.path) != source:
            raise ValueError("The recording changed during draft creation. Drafts were not published.")
        (working / "draft-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                                    encoding="utf-8")
        (working / "READ_ME.txt").write_text(
            "Open YouTube.anato12.json in Studio for the main edit.\n"
            "Each Short-*.anato12.json is an independent portrait edit.\n"
            "Preview framing, dialogue and clip boundaries before publishing.\n"
            "Drafts reference the original recording; keep it at its current path.\n"
            "See draft-manifest.json for included highlights and skipped Shorts.\n", encoding="utf-8")
        if destination.exists():
            raise FileExistsError("The destination already exists. Retry to create a new folder.")
        working.rename(destination)
    return {"directory": str(destination), "shorts": len(shorts), "skipped": len(details["shorts_skipped"]),
            "main_clips": len(main.clips), "rendered": options.render}
