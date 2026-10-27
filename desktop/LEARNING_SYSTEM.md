# Auto Edit and the learning library — 0.4 alpha 3

This extends the existing editor. Import, preview, trim, manual projects, clip
review, transcription and approved draft bundles remain available.

## What this milestone does

**Auto Edit:** select a recording and a downloaded local Ollama model, choose
output limits and a folder, then start one run. Studio transcribes if necessary,
requests clip suggestions, selects whole exchanges, builds a chronological main
video and independent portrait Shorts, renders them and checks each output.
You do not need to mark or approve each clip for this experimental workflow.

Alpha 2 requires a model-suggested map of setup, payoff and optional reaction
lines, with an explicit indication of whether more context is needed. Requests
use a constrained JSON response format with allowed source IDs; Studio independently
checks the response. It derives quoted evidence directly from validated role IDs
and any additional evidence IDs, so duplicate bookkeeping is not required from the
model. New list labels quote source snippets. Free-form model explanations remain
visible as **unverified**, and role labels themselves can still be wrong.

Auto Edit skips unreviewed legacy suggestions without a current map, suggestions
requesting more context, and heavily overlapping ranges after boundary expansion.
Rerunning analysis refreshes untouched unreviewed suggestions; approved, rejected
and manually adjusted suggestions remain intact. Older approved ranges remain
usable. This conservative dialogue path requires distinct setup/payoff lines;
it does not detect purely visual or single-line jokes automatically.

Model suggestions are not human approvals. Automatic selection preserves that
distinction, respects rejected ranges, validates quoted source evidence against
the current transcript, skips callbacks whose cited setup is outside the range,
and extends boundaries to retain intersecting transcript lines. It never cuts a
range merely to fill a time budget. Approved ranges get priority, followed by
model order and explicitly shared category preferences. Main ranges merge in
recording order. Each selected range can produce one Short; overlong ranges and
duplicates are skipped and reported. If the ranked selection has no eligible
Short, the highest-priority eligible Short is reserved first, then the remaining
clip/time budget is filled in the usual priority order. This may displace an
approved longer range in Auto Edit; saved approval decisions and the separate
approved-drafts workflow do not change. Rejected overlaps, evidence checks and
whole-line boundary expansion still apply before reservation. Skipped choices
report the reservation. If no complete Short fits both limits, the run stops
without publishing a bundle. Output durations can be below your limit.

Selection checks cancellation during validation, boundary expansion and budget
selection. A failure to save final error/cancellation history no longer masks
the original result; such a history row may appear interrupted after restart.

This is **experimental editorial selection**, not reliable learned comedy or
semantic story construction. A model can still miss good exchanges, invent a
reason, or select material that depends on unrecognized earlier context. Source
timestamps and successful decode checks do not establish an engaging story.
There is no inferred confidence percentage, invented dialogue, semantic hook
judgment, face tracking, copied creator asset, or automatic YouTube upload.

## Story-opening playbook

The optional checkbox in Auto Edit applies a bounded lesson from the first edit:
look for a recurring conversation, keep its setup and real reaction, and open
with a short complete exchange only when the source dialogue links it to another
selected moment. It can insert a short source-dialogue bridge between adjacent
selected moments when transcript lines in the gap repeat a word from each. A
bridge has its own timestamps and source-line references, is context rather than
a humor candidate, and never becomes a standalone Short. The app checks exact
repeated dialogue words and review priority;
it does not infer that two scenes share a deeper theme. When supported, it moves
one range to the front without repeating it later. Shorts keep their independent
source ranges. The export manifest records the possible topic word, opening ID,
main order and reason. Profanity and filler words alone cannot establish a link.
If the source link or a suitable short exchange is missing, the main edit remains
chronological. An ending payoff and comedy quality are **NOT_EVALUATED** until
someone watches the result. Feedback still changes review priority through the
existing opt-in controls; no model weights are retrained.

## Finder and local chat diagnostics

Connecting to Ollama now selects the local-model analysis mode. Analyze reports
its actual method, timestamped dialogue count and number of model windows; empty
model output is distinguished from empty cue matches or missing transcript. Model
proposals without valid source references raise a section/time-specific error;
individual invalid proposals in a partly valid response are counted in the UI.
The chat box sends only typed text and limited in-session conversation history to
the selected loopback Ollama model. It does not read the video, transcript, profile
or past chat sessions. Model replies are unverified.

## Partial model section recovery

When a local model gives source references that fail validation in one analysis
window, Finder records the section and time range, does not cache that response,
and continues to other windows. It saves suggestions only if at least one window
produces valid referenced candidates; an all-invalid run fails explicitly. The
UI and job history say how many sections were skipped. Auto Edit carries those
diagnostics into its export manifest. This protects long runs from one malformed
section but does not certify comic timing, speaker identity, or full-recording
recall. Network, model and transcript failures still stop the job.

## Initial creator profile

PERSONAL_STYLE.md records Anato12's stated taste. The local model prompt now
considers quiet absurdity, friend chemistry, awkward explanations and genuine
reactions ahead of gameplay intensity. A model may provide a subjective 1–5
taste estimate, which changes ordering only after reference validation. It is
not calibrated humor confidence or actual audience feedback. Existing confirmed
own-video notes and opted-in corrections stay in the local database. Prompt
changes invalidate saved model responses; no weights are retrained.

## Sources, observations and preferences

The Learning library accepts the currently selected local video as a tutorial,
another creator's video, or your own finished video. Use authorized local copies.
Transcription is local and optional packages/models must be installed as described
in START_HERE.md. Existing dialogue or imported SRT can be used instead.

It saves searchable dialogue with absolute timestamps; keyword mentions become
**possible** trim/join, portrait, caption or zoom techniques with a fixed purpose
description. FFmpeg measures possible scene changes at 2 fps and 160 pixels wide
with a score threshold of 0.30. These are not verified cuts: motion and flashes
can trigger them and fast cuts can be missed. At most 200 change timestamps and
24 frame samples are retained per indexing pass. Silent/empty-transcript videos
still receive frame references. Sampled frames have not been understood by a
vision model; important demonstrations are not reliably identified yet.

Saved YouTube URLs are **reference_only / NOT_ANALYZED**. This version does not
download, watch or transcribe URLs. Import an accessible authorized local copy to
index it. It never reports a saved URL as an analyzed video.

Examples start as `observed`. You can confirm/reject them, add a correction,
preview the cited range, search them, inspect source history, delete source
knowledge and export the data from Jobs & clip feedback. Confirmation of an
example does not certify an executable technique.

A confirmed, nonempty correction about an **own** video can optionally guide Auto
Edit. The sharing box is off by default and separate from confirmation. Shared
notes join existing feedback in a bounded list of at most eight recent notes,
240 characters each. View the actual context in Jobs & clip feedback. Editing,
revoking or deleting shared notes invalidates model-response caches. Imported
creator/tutorial text never automatically becomes a personal preference. This
is persistent prompt guidance and category ranking, not model-weight training.

Choose an indexed original and an indexed own-video finished source to compare.
Only unique exact transcript matches of six or more words become match records,
with both source fingerprints and both timestamp ranges. Repeated text is
excluded. Results persist in Source history; they do not establish audiovisual
alignment, identify all retained jokes, or automatically change preferences.

## Tested capabilities and technical output checks

The executable library is a fixed allowlist: trim/join, portrait fit, captions and
fixed zoom. Tutorial/model text is data and cannot generate shell commands,
FFmpeg filters, Python code or new executable recipes. Learned observations are
stored separately from capability test results.

Before Auto Edit uses required operations, real synthetic FFmpeg render/decode
tests must pass on this installation. Results bind to the engine executables'
path/size/mtime and the implementation's content hashes; a changed engine/code
causes retesting. This is a practical local compatibility identity, not a
cryptographic attestation of executable bytes. The library can test all supported
operations on request. Execution/decode success is not visual-quality acceptance.
Zoom is available to manual editing and testing, but automatic zoom timing is not
implemented. Auto Edit currently uses trim/join, portrait fit and optional captions.

Every Auto Edit output must have the planned dimensions and duration (within
0.15 seconds), an audio stream, a successful full FFmpeg audio/video decode, and
exact expected SRT content when enabled. These checks do not measure joke quality,
story coherence, face framing, caption transcription accuracy, clipping/loudness,
or audience engagement. Silent sources receive the renderer's silent audio track.

All projects, videos, captions and a `draft-manifest.json` are staged in a new
owned directory. The whole folder is published only after checks and a final
source-identity check pass. Ordinary failure/cancellation removes staged files;
original media, earlier exports, reviews and the open editor timeline stay intact.
The manifest records choices, skips, original/expanded ranges, model identity,
shared preference context, tested operations and per-output quality results.
It contains private source paths, quoted dialogue and preferences; share it deliberately.

## Persistence and recovery

SQLite schema 4 retains learning documents/examples/events and technique-test
history, and adds a persisted exchange map to highlights. Migration preserves
reviews, feedback, learning records and note-sharing consent. The migration transaction is tested with an injected
failure. Older Studio versions refuse this newer profile; use the new version.
Back up the profile with Studio closed before moving it between machines.

Jobs & clip feedback records Auto Edit and learning-index progress and errors. After a stop or app
restart, Resume retries a run using available transcription/model caches; learning
indexing repeats visual sampling and keeps existing confirmed corrections. Video
rendering starts again in a fresh folder. Completed batch rendering does not
resume at the last encoded frame. Forced termination can leave an unpublished
temporary folder; power-loss cleanup and crash-atomic publication/job-history
updates are not implemented. A crash after folder publication but before job
history update can leave a valid bundle with an interrupted job. Check your
chosen output folder before retrying to avoid unnecessary duplicate exports.

Knowledge survives cache clearing. Source-knowledge deletion removes its examples,
corrections, comparison history and future preference influence, while originals
and existing exports remain. Disposable thumbnail cache files can remain until
the recording's app data is deleted. Export local data includes the learning
tables and test history. No recordings or model weights are embedded in the ZIP.

## Remaining acceptance

- Reliable humor selection and story planning: PARTIALLY_IMPLEMENTED for model
  suggestions and a source-linked opening heuristic; semantic story/hook
  understanding and verified ending payoffs are NOT_IMPLEMENTED.
- Tutorial/creator learning: PARTIALLY_IMPLEMENTED. Searchable evidence, sampled
  frames and technical observations exist; semantic visual demonstrations,
  sound-effect recognition, engagement analysis and novel technique synthesis
  are NOT_IMPLEMENTED.
- Own-style learning: PARTIALLY_IMPLEMENTED. Shared confirmed notes and existing
  category feedback affect future analysis; exact dialogue comparison is available.
  Automatic audiovisual alignment and inference of retained comedic patterns are
  NOT_IMPLEMENTED.
- Native Windows/RTX validation, signed installer, genuine long-recording
  unattended quality acceptance: NOT_TESTED in this milestone.

See TEST_RESULTS.md for actual test outcomes. Use High for the remaining semantic
evidence/learning work; Medium is suitable for small UI and documentation fixes.
