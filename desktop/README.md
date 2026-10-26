# Anato12 Studio

A native, local-first desktop editor for Anato12's YouTube recordings.

**New to setup? Open [START_HERE.md](START_HERE.md).** On Windows, extract the folder,
install Python 3.12/3.13, run `SETUP.bat`, then `START_ANATO12.bat`.

## What works

- Experimental Auto Edit: one run from a selected recording/local model to a
  checked main MP4 and Shorts, with complete-range selection, rejected-range
  protection, operation tests and a per-output report. Editorial quality is unverified.
- Persistent learning library: local-video transcripts, sampled frames, possible
  scene-change measurements, timestamped references, searchable examples,
  corrections, separately shared own-video preferences and exact dialogue comparison.
  YouTube URLs are stored as references only. See [LEARNING_SYSTEM.md](LEARNING_SYSTEM.md).

- Import MP4/MOV/MKV/WebM recordings; inspect metadata with FFprobe.
- Native Qt preview, seeking, volume, in/out points and selected-range playback.
- A clip list with inclusion checkboxes, naming, reordering and saved projects.
- FFmpeg export to 16:9 YouTube MP4 or 9:16 Shorts MP4, fit/fill framing, focal
  position and per-clip zoom.
- Cancellable jobs, source-file protection and temporary intermediate files.
- Optional local English Whisper transcription with timestamped, editable dialogue.
- UTF-8 SRT import/export and optional burned captions.
- Reviewable moment suggestions based on explicit transcript cues.
- Persistent AI Clip Finder: contextual cue candidates, actual frame thumbnails,
  preview, manual ranges, approvals/rejections, selected-clip export and editor insertion.
- Create independent YouTube and Shorts project bundles from approved highlights,
  with overlap merging, complete-range Shorts, optional batch MP4/caption rendering,
  cancellation cleanup and an output/skip manifest.
- Durable SQLite jobs/caches, restart recovery, literal transcript search and
  explicitly opted-in category feedback with view/delete/export controls.
- Separately opted-in note preferences for local-model analysis; edit/revoke them
  and inspect the bounded personalization preview. Existing notes remain unshared.
- Optional loopback Ollama adapter for downloaded local models. Real CPU inference
  has run; genuine-dialogue checks found missed exchanges and unsupported explanations.
  Reliable humor/story quality remains unverified.

The core editor does not depend on speech packages, credentials or a model. The app
uses CPU encoding/speech inference and works without a GPU. Recordings stay local.
The optional model adapter sends transcript windows to the configured loopback
server only; use downloaded models. Known cloud-backed models are rejected.
Model/package downloads need internet access on first use.

## Development

```bash
cd desktop
uv sync --extra dev --extra speech --frozen
uv run python -m anato12_studio
uv run pytest -q
```

Without uv:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev,speech]"
python -m anato12_studio
python -m pytest -q
```

FFmpeg and FFprobe must be on PATH or configured in Settings. Overrides
`ANATO12_FFMPEG` and `ANATO12_FFPROBE` accept exact executable paths.

Qt 6.8.3 is pinned. The newest available Qt build caused a multimedia startup
failure in the cloud test machine; the pinned version passed actual decoded-frame
preview and export tests. Windows is the distribution target; cloud verification
runs on Linux, so native Windows execution remains a separate check.

Tests generate their own small recordings, export both aspect ratios, decode the
outputs, verify joined audio/video durations, burn captions, drive the actual
desktop import/preview/export flow, and exercise source protection/cancellation.
No user recordings or model weights are in the repository or distribution.

## Windows distribution

`BUILD_WINDOWS.bat` uses `Anato12Studio.spec` to create a folder-based PyInstaller app.
The workflow `.github/workflows/desktop-windows.yml` is provided to test and build
that app on a Windows GitHub runner when invoked or when these changes are pushed.
It has not been run by this cloud task.

The downloadable source ZIP also contains a standalone workflow at
`.github/workflows/windows.yml`, configured for the app folder as a repository root.
Run `python package_source.py` to recreate the source ZIP in `dist`.

See [VALIDATION.md](VALIDATION.md) for the completed checks and platform limits.

See [TEST_RESULTS.md](TEST_RESULTS.md), [PROJECT_AUDIT.md](PROJECT_AUDIT.md) and
[DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) for the current milestone.

## Current limits

Version 0.4.0a1 adds experimental Auto Edit and the learning foundation described
in LEARNING_SYSTEM.md. It does not yet understand tutorial demonstrations,
reliably learn comedic structure, or construct semantic hooks/stories. Saved URLs
are unviewed references. Native Windows acceptance remains outstanding.

The retained 0.3.0a4 work added cancellable local-model connections, total request deadlines,
and reports containing raw proposals plus server token/timing measurements.
Official model downloads now work in the development environment. Real CPU
inference was tested with Qwen2.5 3B/7B and Qwen3 8B, but valid transcript IDs
did not prevent unsupported explanations. Automatic humor selection remains
PARTIALLY_IMPLEMENTED and requires source review; no model has passed human
acceptance. See TEST_RESULTS.md for the actual comparisons and limitations.

The revised prompt asks for complete exchanges and treats targeted search
separately from humor selection. Advertised thinking mode is disabled for the
local model's bounded JSON response; this does not alter Codex reasoning settings.
Approved drafts, separate feedback-note consent, and content-bounded context
remain available. CHECK_LOCAL_AI.bat saves private evaluation evidence beside
your project. Windows execution, RTX performance and full-length semantic
acceptance still need verification.

- English transcription, approximate phrase timestamps, no speaker diarization.
- Default moment ranking is a text heuristic, not a validated humor detector.
  Semantic analysis requires an installed local Ollama model; small genuine-dialogue
  checks found both unsupported suggestions and missed exchanges. Review every result.
- Add to main/Shorts appends to one editor timeline and switches its output ratio.
  The new approved-draft button creates those separate projects automatically.
  This is chronological assembly from user decisions; story/hook selection,
  face tracking and a general personal assistant are not implemented.
- Feedback and shared own-video notes provide bounded ranking and prompt guidance,
  not model-weight training.
- Hard cuts and fixed per-clip zoom; no animated keyframes, transitions, waveform
  editor, multitrack compositing or automatic face tracking yet.
- Output is 30 fps at the two fixed 1080p aspect-ratio presets. Export cannot add
  detail to low-resolution recordings.
- Preview codec support depends on Qt/OS drivers. FFmpeg export support is broader.
- No signed installer or Windows EXE has been built in the Linux cloud environment.

## Components

`model.py` — project validation and caption timing  
`video.py` — FFmpeg discovery/probing/rendering  
`player.py` — Qt multimedia preview and framing  
`window.py`, `panels.py`, `actions.py` — editing UI and background jobs  
`speech.py` — optional Whisper ONNX model download/inference  
`moments.py` — conservative, reviewable transcript cues

`finder.py`, `local_model.py` — overlapping context, evidence validation and local-model adapter

`store.py`, `finder_jobs.py` — transactional reviews, caches and resumable jobs

`finder_ui.py`, `finder_controller.py` — clip finder and feedback/job controls

`auto_edit.py`, `quality.py` — automatic selection, tested capabilities and output checks

`knowledge.py`, `learning_visual.py`, `learning_ui.py` — persistent examples,
scene-change observations, corrections and learning/Auto Edit controls

See [THIRD_PARTY.md](THIRD_PARTY.md) for open-source dependencies.
