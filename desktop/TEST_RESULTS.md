# Test results — phase 2A

## Alpha 3 approved-draft update

Final extracted-package validation: **69 passed, 0 failed, 0 skipped in 19.98
seconds**. Ruff and Git whitespace checks passed. The styled draft dialog was
inspected visually. The archive contains 58 source/setup files and excludes
recordings, model weights, databases and private verification outputs.

First complete run: **68 passed, 0 failed, 0 skipped in 19.70 seconds**.
After adding actual mid-batch render cancellation and the completion-folder action,
the affected draft/GUI tests passed: **8 passed in 4.93 seconds**.

New evidence: real main/Short MP4s have correct ratios, durations, audio and SRT
offsets; burned captions render. Three tiny synthetic outputs took 2.36 seconds
in the targeted integration test (including project/probe checks), not a benchmark
for long gaming recordings. CPU processing only; GPU utilization NOT_MEASURED.

Tests verify main-range overlap merging, exact duplicate Shorts suppression,
whole-range duration-limit skipping, separate editable caption objects, source
change rejection, all 501 approved records beyond the display limit, and unchanged
open-project/dirty state through the real Qt action. Cancellation after the first
MP4 finishes publishes no partial bundle. Simulated ENOSPC also cleans up without
changing existing files. Physical disk exhaustion/power loss/native Windows remain
NOT_TESTED. Full semantic story selection and real-model humor quality remain
unverified; these drafts use explicit user approvals.

## Alpha 2 model-readiness update

Workspace validation: **62 passed, 0 failed, 0 skipped in 16.85 seconds**.
Final extracted alpha-2 package: **62 passed, 0 failed, 0 skipped in 17.00 seconds**.
Ruff and Git whitespace checks passed. The source archive contains 56 files and
excludes recordings, models, databases and private verification artifacts.
New checks cover installed-model replacement, configuration identity, invalid
evidence excluded from cache, mid-request model replacement, incomplete/nontextual
responses, and evaluation reports preserving completed evidence after failure.
Evaluation tests use controlled HTTP responses, not real semantic inference.

Actual download attempts to ollama.com and registry.ollama.ai were rejected by
the managed proxy with **HTTP 403** on 2026-10-26. No network policy was bypassed.
Real Ollama inference remains BLOCKED here. Windows launcher/GPU acceptance
remain NOT_TESTED. The evaluator makes those local checks reproducible once
a downloaded model is available; it measures wall time, not GPU usage.

The historical alpha-1 measurements below apply to their stated fixtures.

Baseline before changes: **17 passed in 5.69 s** on Linux, Python 3.12.14,
PySide6 6.8.3 and FFmpeg 7.1.5. After first finder integration, the same 17 tests
passed in 5.78 s. These are genuine process outputs, not estimates.

Final suite from a fresh extracted source ZIP: **53 passed, 0 failed, 0 skipped
in 15.54 s**. The preceding 52-test run passed in 15.80 s. After the small-window
layout correction, both GUI tests passed again (2 in 2.67 s). A final additional
model-window resume regression exposed a timestamp normalization cache miss;
the correction passed all 18 finder tests and the full extracted-package suite.
Ruff and Git whitespace checks passed.

Package verification: 53 source/setup files, valid ZIP CRCs, all six mandatory
project documents included. No recordings, private verification media, model
weights, database, virtual environment or Git metadata are distributed. Code
and test bytes in the final ZIP are compared with the tested extracted files.
This is a source/launcher ZIP; no native Windows EXE was built.

Executed command: `.venv/bin/python -m pytest -q -s tests --durations=8`.
Dependencies: Python 3.12.14, PySide6 6.8.3, FFmpeg/FFprobe 7.1.5,
sherpa-onnx and sherpa-onnx-core 1.13.8. Platform: Linux x86_64.

## Verified behavior

- Two actual Qt workflows, each inside a subprocess with a hard hang timeout.
  The original editor imports, decodes, seeks repeatedly, masks portrait preview
  and exports. The finder creates a real thumbnail, adjusts and approves a clip,
  stores opt-in feedback, previews actual frames, appends clips to both format
  selections, exports ONLY its one selected range despite a longer timeline,
  clears stale source rows on New Project and retrieves the review after restart.
- Real FFmpeg exports for both aspect ratios, joined stream durations, silent
  sources, burned captions, trim-relative SRT, cancellation and source protection.
- SQLite reopen, newer-schema refusal, preserving reviewed/manual decisions on
  reanalysis, opt-in/out/deletion behavior, source-data deletion preserving source
  video, clearing caches preserving feedback, source-change invalidation.
- Actual child process exits abruptly after committing a running job. A fresh
  Store reopens it and recovers the state as interrupted with retained progress.
- Actual thumbnail extraction and cancelled/failed job states; resumed analysis
  reuses saved imported dialogue without invoking speech recognition.
- A controlled adapter fails during its second context window. Retry reuses the
  completed first response, and a different endpoint receives separate calls.
  This is cache/recovery validation, not actual model inference.
- Overlapping absolute-time windows, sparse late-recording segments, deduplication,
  callback evidence and whole-word literal search. Laughter/profanity/volume alone
  do not establish a cue-mode humor candidate.
- Model-proposed invented IDs/times cannot create source evidence. Non-loopback
  endpoints, redirects and declared cloud backends are rejected. Real loopback
  HTTP fixture requests exercise JSON schema, server outage and malformed JSON.
  This is HTTP-contract evidence, not actual model inference.
- Simulated ENOSPC during JSON data export preserves the existing destination
  and removes the partial temporary file. This is fault injection, not a physical
  full-drive test.

## Real long synthetic media

Each case creates and probes an actual MP4, imports its source identity, analyzes
a supplied timestamped transcript near the end, exports a one-second late range,
checks both stream durations/SRT offsets and decodes the finished output.
Frames are static 64×36 at 1 fps; audio is silence. This deliberately tests
duration/timing, not gaming detail or ASR accuracy.

| Source duration | File bytes | Total test wall time | One-second 1080p export wall time |
| --- | ---: | ---: | ---: |
| 30 s | 4,793 | 0.747 s | 0.362 s |
| 5 min | 29,077 | 0.742 s | 0.329 s |
| 20 min | 110,585 | 0.966 s | 0.351 s |
| 60 min | 327,280 | 1.598 s | 0.329 s |
| 120 min | 658,256 | 2.667 s | 0.348 s |

## Full two-hour audio preparation / actual CPU model

A separate **7,200 s MP4** contains silence plus a 13-second genuine speech sample
starting at 7,180 s. Its 3,348,958-byte compressed size does not represent a normal
gaming recording. The full file went through FFmpeg mono WAV preparation and
28-second ASR windows at 27-second stride, using the actual int8 tiny.en model.

- Cancelled after 130 completed chunks: **14.391 s** until cancellation.
- Resume re-extracted WAV, reused all 130 chunks and completed: **14.575 s**.
- Full transcript cache hit, with an intentionally unusable FFmpeg name: **0.003 s**.
- Four retained transcript/reaction lines had absolute times between 7,182–7,193 s.
- Linux getrusage peak Python RSS: **372.68 MiB**; maximum individual child
  peak RSS: **252.37 MiB**. These are separate process peaks, not a summed system
  memory estimate. No GPU measurement was available.
- Recognition text contained errors. An initial run exposed a [BLANK_AUDIO]
  placeholder before the speech. Explicit control-only silence markers are now
  filtered, the transcript cache version was bumped, and actual inference was
  rerun. The controlled-recognizer regression also retains genuine reaction
  markers. This does not solve arbitrary speech-model hallucinations.

## Feature status at this milestone

| Feature | Status |
| --- | --- |
| Existing core editor and captions on Linux | VERIFIED_WORKING |
| Durable reviews, feedback, literal search, cue analysis, preview/export | VERIFIED_WORKING |
| ASR cache/chunk resume on the measured fixture | VERIFIED_WORKING |
| Loopback model adapter | PARTIALLY_IMPLEMENTED (HTTP contract verified; actual model inference NOT_TESTED) |
| Full contextual humor quality / semantic-search acceptance | BLOCKED (needs real local model plus human-reviewed genuine examples) |
| Complete phase-2 product acceptance | PARTIALLY_IMPLEMENTED |

## Explicit NOT_TESTED cases

- Native Windows launcher, playback drivers and compiled EXE.
- RTX 3060 Ti utilization, NVENC/CUDA success and 8 GB VRAM capacity.
- Actual Ollama semantic inference and genuinely funny ranking quality.
- Genuine uninterrupted 60/120-minute gaming speech recognition and semantic review.
- Power loss during filesystem/SQLite writes, physically full disk, hardware faults.
  Abrupt application-worker exit and simulated JSON-write ENOSPC were tested.
- Official OAuth/YouTube APIs and later roadmap phases (NOT_IMPLEMENTED).

Synthetic long-file tests, local HTTP contract fixtures and short genuine speech
tests must be reported separately. Passing one does not imply the others passed.
