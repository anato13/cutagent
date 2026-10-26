# Test results and verification history

## Version 0.4.0a1 — Auto Edit and learning foundation

Final extracted-package suite: **144 passed, 0 failed, 0 skipped in 83.04 seconds**.
Tests ran from the extracted app directory with its code first on PYTHONPATH and
an isolated profile. The final 76-file ZIP matches that extraction except for this
updated verification note. User recordings, profiles and model weights are excluded.

Workspace suite: **144 passed, 0 failed, 0 skipped in 81.45 seconds**. The final
source-data deletion refresh was then verified in the real desktop workflow
(1 test, 10.01 seconds) before the extracted-package suite. Ruff, Git whitespace
and offline lock checks passed. Earlier focused post-publication/history and
relative-profile checks also passed (3 cases, 23.86 seconds).

The new tests use isolated profiles, a fixture local-model HTTP server and real
FFmpeg/Qt. They cover automatic main/Shorts export without fabricated approval,
source/timeline preservation, full decode and caption checks, rejected overlaps,
missing/stale evidence, incomplete callback context, whole-line boundaries,
budget skipping, cancellation/quality failure before publication, fresh-folder
retry after interrupted jobs, capability failure and engine-specific retesting,
and late cancellation/history failure after committed output.

Learning regressions cover schema-2 migration rollback, prior feedback consent,
durable searchable citations, actual PNG frames, correction preservation on
reindex, separate own-note sharing/revocation, data export/deletion, saved URLs
remaining NOT_ANALYZED, exact unique dialogue matches, and persistent failed-job
progress/retry. A real black-to-white video produces one measured scene-change
candidate at 2 seconds; silent-source indexing still creates a frame example.
That synthetic detector check is not recognition of editing demonstrations.

The actual desktop workflow imports a video, indexes it, shows an extracted
frame, saves a shared correction, stores an unviewed URL, connects to the fixture
model, runs Auto Edit, checks its exports and reopens the persisted profile. It
has a 100-second outer process timeout. Screenshots were inspected for the new
scrollable tabs; the earlier editor/finder desktop regressions also passed.

### Genuine-dialogue model check

Ollama with downloaded **qwen3:8b Q4_K_M** (digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`)
ran the new Auto Edit pipeline on an existing 19-line genuine transcript sample
from the user's recording, using a fresh isolated profile. With an empty query
and no manual clip approval, it selected source **457.100–516.100 seconds** and
created a **59-second** main MP4 and a **59-second** Short. Both had the expected
1920×1080 / 1080×1920 dimensions, an audio stream, full successful decode and
matching SRT captions. The original source fingerprint and unreviewed decision
were unchanged. The run took 99.178 seconds on the cloud CPU; this is an observed
run time, not a Windows/GPU benchmark. Two extracted frames were visually checked:
captions were readable and portrait fit preserved the whole source with bars.

A second run supplied a targeted query for that conversation. It selected
478.108–516.092 seconds; boundary preservation expanded the actual output to
461.100–516.100 seconds to keep intersecting transcript lines. Both 55-second
outputs passed the same checks in a 62.116-second run. This query was supplied
through the backend test harness; the Auto Edit UI uses an empty query. Outputs
remained unreviewed and source identity remained unchanged.

This is one successful sampled exchange, not analysis of the entire recording,
human-rated humor acceptance, or evidence of consistent model behavior. Earlier
tests of the same model missed this sample. B20 and broad semantic acceptance
remain open. Private reports/videos stay under `.verification/learning-real/`
and are excluded from the distribution.

**NOT_TESTED:** native Windows file behavior and UI, RTX acceleration, genuine
full-length unattended editing, audience engagement, automatic semantic tutorial
understanding and learned comedy effectiveness. **NOT_IMPLEMENTED:** semantic
hook/story planning, audiovisual original/finished alignment, URL acquisition,
novel executable recipe synthesis, automatic SFX selection and crash-atomic
publication/history updates. Technical mechanics are VERIFIED_WORKING in the
tested Linux cases; the overall requested learning system is PARTIALLY_IMPLEMENTED.

## Version 0.3.0a7 paired export recovery

Final extracted-package suite: **117 passed, 0 failed, 0 skipped in 30.96 seconds**.
The final 67-file source ZIP matches the tested extraction except for this updated
verification note. Recordings, model weights and private profiles are excluded.

Workspace suite: **117 passed, 0 failed, 0 skipped in 30.44 seconds**. Ruff passed.
Fault injection covers failure/cancellation on the second file, cancellation after
both files are installed, refusal of an unapproved overwrite, failed recovery
retaining original backups, and backup-cleanup failures preserving the new pair.
A real FFmpeg export with an injected caption-publication failure restores the
previous MP4/SRT bytes and removes temporary outputs. Existing media and desktop
regressions also pass. Ordinary-error recovery is VERIFIED_WORKING in Linux.
Power loss/process-kill recovery is NOT_IMPLEMENTED. Windows locking, physical
disk faults, GPU performance and AI quality were NOT_TESTED in this pass.


## Version 0.3.0a6 reliability fixes

Workspace suite: **107 passed, 0 failed, 0 skipped in 31.04 seconds**.
After the final new-project default adjustment, the real desktop workflow passed
again (1 test in 1.79 seconds), including import, decoded preview, seeking, export
and empty-project caption-control consistency. Ruff and whitespace checks passed.
Relink regressions verify shortened clips/captions are rejected without changing
the project, duration mismatches are rejected, and valid replacements store actual
metadata. A failed-analysis regression verifies retained progress.
These mechanics are VERIFIED_WORKING in Linux. Native Windows/GPU and AI semantic
quality were NOT_TESTED in this pass. No new performance claim is made. The source
ZIP was rebuilt and integrity checked, without a separate extracted-package suite.


## Version 0.3.0a5 focused bug fixes

Workspace suite: **102 passed, 0 failed, 0 skipped in 30.76 seconds**. Ruff passed.
New regressions cover project saves targeting source paths/hardlinks, ordinary
project overwrite/reopen, and malformed model capabilities rejected before chat.
Source ZIP rebuilt and archive integrity checked; no separate extracted-package
suite was run for this patch. Windows/GPU and semantic quality were not retested.
No additional model benchmark or paid service was used.


## Version 0.3.0a4 real inference and cancellation

Final extracted-package suite: **96 passed, 0 failed, 0 skipped in 30.76 seconds**.
The source ZIP contains 63 source/setup files. Its final application, tests,
launchers, lockfile and other unchanged files match the tested extraction;
only these verification notes and the audit summary were updated afterward.

Workspace suite: **96 passed, 0 failed, 0 skipped in 30.51 seconds**.
Ruff, offline lockfile consistency and Git whitespace checks passed.

Status: transport/search/cache/export mechanics VERIFIED_WORKING on this Linux
CPU environment; automatic humor selection PARTIALLY_IMPLEMENTED. The official
Ollama download and registry requests now succeed after the user's environment
change. This supersedes earlier network-blocked entries below.

Ollama **0.40.11**, Linux amd64, was installed from its official release. Archive
SHA256 matched the release's sha256sum.txt:
`7bedab90dd122661be78798e9f0edf37fccf0cccf2699d2c58ea1a3afdc04b6d`.
Model blobs were SHA256 checked against official registry manifests. The runtime
binds only to 127.0.0.1 with OLLAMA_NO_CLOUD=1. Models and private evidence remain
outside the source distribution; no transcript was sent to a cloud inference API.

Models tested (all Q4_K_M):

- qwen2.5:3b, 3.1B parameters, installed digest
  `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b`.
- qwen2.5:7b, 7.6B parameters, installed digest
  `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`.
- qwen3:8b, 8.2B parameters, installed digest
  `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
  Its advertised thinking mode is disabled for bounded JSON output.

### Genuine-dialogue checks

Three selected excerpts from one real recording used 19, 20 and 4 existing ASR
lines (A/B/C), retaining absolute source timestamps. They are not an independent
labeled dataset, and ASR errors remain. No user humor ratings or accuracy score
were invented. Engineering inspection checked whether explanations matched the
provided transcript; source-audio boundary acceptance remains separate.

| Model / prompt | Wall seconds A / B / C | Candidates after validation and deduplication | Finding |
| --- | --- | --- | --- |
| Qwen2.5 3B / bounded-context-1 | 32.712 / 15.328 / 6.668 | 2 / 2 / 0 | Fragmented exchanges and unsupported explanations; C's single raw proposal had no valid evidence, not a true no-match |
| Qwen2.5 3B / complete-exchanges-2 | 20.470 / 12.713 / 9.201 | 1 / 1 / 2 | Stronger wording alone did not resolve invented interpretations |
| Qwen2.5 7B / complete-exchanges-2 | 43.125 / 25.835 / 5.032 | 1 / 1 / 0 | More complete ranges, but an explanation still invented a relationship reaction |
| Qwen3 8B / complete-exchanges-2 | 35.024 / 20.284 / 5.449 | 0 / 0 / 0 | Conservative empty responses; missed a potentially useful exchange |
| Qwen3 8B / final complete-exchanges-search-3 | 1.953 / 19.554 / 5.407 | 0 / 0 / 0 | Same limitation in the final automatic mode |

Times include differing model-load/prompt-cache states; this is not a controlled
speed ranking. Server token/duration fields are retained per request. The sampled
runs reported at most 1,116 prompt tokens; maximum-budget Unicode/template
capacity was not established. Ollama reported CPU operation and size_vram=0.
This does not establish an 8 GB GPU fit, actual VRAM use or Windows speed.

A specific semantic query under the final prompt found one relevant source range
in **35.336s** with Qwen3 8B. Its generated explanation still needs review,
including speaker attribution; there is no diarization. Prompt instructions now
explicitly distinguish requested relevance from automatic entertainment selection.

### Real app pipeline and media

The actual finder/store pipeline, in a separate disposable profile, found one
unreviewed result in **15.054s** using one Qwen3 request. Reopening the store and
running the same search took **0.022s** with **zero additional chat requests**.
The original source fingerprint and unreviewed status were preserved.

The returned range exported through the application's normal backend to two
**38.0-second** H.264/AAC MP4s, with burned captions and nonempty SRT sidecars:

- 1920x1080 landscape: **14.664s** export time.
- 1080x1920 portrait, keep-whole-frame: **11.942s** export time.

Both files passed complete FFmpeg decode checks. Inspected frames show the
source frame retained and readable captions; portrait keep-whole-frame adds bars
as designed. This is export verification, not approval of pacing, framing or humor.
Private clips, reports, screenshots, databases and model weights are excluded
from the ZIP.

### Cancellation and remaining acceptance

An actual Ollama call cancelled at 1s returned at **5.109s** before the fix and
**1.035s** after it (about 35ms after the request). Ollama logged cancellation and
released the inference slot. HTTP regression fixtures separately stall before
headers and during a partial body; cancellation and total deadlines terminate
both. Initial connection establishment has a five-second socket timeout; active
requests have a 300s chat / 60s metadata deadline and a 2MB response cap.

Reports retain raw rejected proposals, server counters when present, prompt
version and explicit no_proposals/invalid_evidence outcomes. Valid source IDs
prove reference membership only, not that the generated explanation is true.

NOT_TESTED: native Windows setup/playback/EXE, RTX/NVENC/CUDA, full-recording
semantic quality or 60/120-minute gaming inference, calibrated humor accuracy,
user acceptance and a controlled comparison of model performance. The entire
490-line recording was prepared as a private project but was not semantically
analyzed in this milestone. Next work should improve supported explanations,
boundaries and earlier story context before broad unattended-selection claims.


## Version 0.3.0a3 bounded dialogue input

Final extracted-package suite: **82 passed, 0 failed, 0 skipped in 20.40 seconds**.
Ruff and Git whitespace checks passed. The archive contains 61 source/setup files;
tested code is compared byte-for-byte before final packaging.

Workspace suite: **82 passed, 0 failed, 0 skipped in 20.65 seconds**.
Coverage includes a dense two-hour synthetic transcript (14,400 lines), Unicode
and escaped text, oversized line/query errors before any server call, sparse late
timestamps, callback-budget rejection of unsent evidence, and partial-analysis
resume with matching bounded windows. All original editor/export tests remain.

A separate planner-only measurement produced **661 sections** from those 14,400
synthetic lines in **0.0744 seconds**, with maximum content size **4,974 bytes**
and Python peak RSS **18.5 MiB** (Linux getrusage). This includes no media decoding,
ASR or model inference and is not a gaming-recording processing benchmark.

Model requests now ask for 8,192 context / at most 1,200 output tokens. Actual
token counts, server truncation behavior, GPU memory and semantic effectiveness
are NOT_TESTED. The 6,000-byte content limit is conservative rather than an exact
tokenizer bound. Callback links may be omitted and are counted in evaluation
reports; every local transcript row is retained intact in at least one section.

Official Ollama download/registry probes still returned proxy HTTP 403 on
2026-10-26. A network draft adding only ollama.com and registry.ollama.ai was
confirmed saved while preserving existing custom hosts. It requires user review,
save and environment publication; draft persistence is not runtime access.

## Version 0.3.0a2 feedback controls

Final extracted-package run: **76 passed, 0 failed, 0 skipped in 20.56 seconds**.
Ruff and Git whitespace checks passed. The package contains 59 source/setup files,
with recordings, models, databases and private verification data excluded.

Initial full suite: **74 passed, 0 failed, 0 skipped in 20.97 seconds**.
After adding transaction-rollback and private-cache regressions, targeted
feedback/GUI validation passed: **8 passed in 2.08 seconds**.

Verified: v1 database rows/decisions survive upgrade with note sharing disabled;
an injected interruption rolls back the consent column and schema version
together. Category opt-in alone does not share note text. Notes require separate
consent and a reviewed decision, with at most 8 notes × 240 characters in context.
Editing/revoking/deleting shared feedback clears model-response caches while
keeping speech transcripts and approved clips. Private edits preserve model caches.

An actual loopback HTTP fixture receives exactly the explicitly shared note
context, with quoted instruction-like text kept inside JSON user data. Context
edits cause fresh requests. The Qt workflow edits a saved note, enables sharing,
verifies the preview and revokes sharing without losing the note.
These are consent/transport/cache tests, not real-model humor-quality evidence.
No GPU utilization or new long-recording throughput measurements were collected.
Windows/native model quality remain NOT_TESTED; official model downloads were
previously blocked by the managed proxy.

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
