# Project audit — 2026-10-26

Alpha 3 continues from b5e8e3d and adds approved-draft assembly and optional batch
exports. Projects remain JSON version 1; SQLite schema is unchanged. No dependencies
were added. The builder snapshots the source/transcript, checks its fingerprint,
writes in an owned temporary directory and publishes a unique folder only after
success. Ordinary cancellation/errors remove partial outputs. Abrupt termination
may leave a temporary folder and is not a resumable batch.

Final alpha-3 validation: 69 tests passed from the extracted distribution, including
real captioned exports, cancellation after one rendered output, and the GUI's
unchanged-project check. Native Windows/GPU and semantic-model quality remain
unverified. The approved-draft milestone is preserved on local branch
anato12-approved-drafts-0.3a1; no remote push is part of this checkpoint.

Alpha 2 continues from checkpoint 04d6e61. Added a separate local-model evaluation
command and Windows launcher, installed-weight/configuration cache identity,
and explicit rejection of incomplete or unsupported model results. HTTP fixtures
verify mechanics; real inference is blocked by proxy HTTP 403 for the official
Ollama download and registry. The existing editor and review database are preserved.

## Recovery and scope

The existing app was inspected and its 17 tests passed before this milestone.
Its previously uncommitted implementation was preserved in commit `2e02f7f`,
also named by local branch `anato12-before-master-v2`. No remote push occurred.
A second source-only recovery archive is outside the repository at
`/workspace/anato12-recovery/pre-master-v2.tar.gz`, SHA256
`3b8ff5bf2590fe8dead3fcf2e30bc94a587f9ac0322e5681f65bfedac3f65b90`.
The original repository history and CutAgent CLI remain intact.

The desktop app is Python/PySide6, not Electron. Its editor already imports and
previews local files, stores JSON edit decisions, trims and joins clips with
FFmpeg, crops/zooms, and exports 16:9 or 9:16 H.264/AAC MP4s. Speech is optional
CPU Whisper through sherpa-onnx. No account, subscription or upload is required.
Project files reference original paths; moving a recording requires relinking.

## Baseline status

| Feature | Status | Evidence / limit |
| --- | --- | --- |
| Import, preview, trim, ordered export | VERIFIED_WORKING | Real FFmpeg and Linux offscreen Qt workflow |
| Both export ratios, fixed zoom, crop/fill/fit | VERIFIED_WORKING | Media metadata, decode and preview masking checks |
| SRT import/export and burned captions | VERIFIED_WORKING | Exact trim-relative offsets and real export |
| Source protection and export cancellation | VERIFIED_WORKING | Regression tests include caption sidecar target |
| CPU transcription | VERIFIED_WORKING | Real tiny/base English model runs on short genuine speech; quality varies |
| Legacy Potential moments tab | PARTIALLY_IMPLEMENTED | Conservative text cues; not contextual humor AI |
| Windows launchers/build workflow | IMPLEMENTED_UNTESTED | Dependencies resolved; no native Windows session/EXE run |
| NVIDIA acceleration | NOT_IMPLEMENTED | Current speech/export use CPU; no usable GPU in this environment |

## Phase 2A additions

SQLite stores analysis caches, real source/evidence references, candidate decisions,
manual adjustments, opt-in clip feedback and durable job state. The new AI Clip
Finder offers cue analysis, literal transcript search and an explicit loopback
Ollama adapter. Actual semantic-model quality remains unverified. Full details and
final checks belong in TEST_RESULTS.md and DEVELOPMENT_ROADMAP.md.

Sources use a bounded first/last 1 MiB sample plus resolved path, size and
mtime_ns as their cache identity. This avoids hashing hours of video during each
selection. It is not a full-file content hash and cannot detect adversarial
middle-of-file edits that preserve all sampled bytes and metadata.

Transcription reads 28-second chunks at a 27-second stride. Full mono 16 kHz
PCM audio is prepared on disk (about 220 MiB for two hours), never wholly in RAM.
Completed chunks and analysis windows are cached. Resuming a partially completed
transcription currently prepares the WAV again, then skips completed inference.
Imported/edited project transcripts take priority over cached automatic dialogue.

No local Ollama server or NVIDIA device has been supplied here. Contract fixtures
can verify request/schema/error behavior, but cannot establish humor quality,
model fit in 8 GB VRAM, GPU speed or Windows playback. Those are explicit blockers
for complete phase-2 acceptance, not reasons to label later phases complete.

Phase 2A verification completed: 53 tests passed from a fresh source ZIP, including two real Qt workflows,
five real synthetic duration cases through 120 minutes, and persisted review/job
recovery checks. A separate two-hour mostly silent recording also passed actual
tiny.en CPU transcription with interruption/chunk resume. See TEST_RESULTS.md for
fixture limitations and measured memory/timing. The full semantic clip-finder
milestone remains PARTIALLY_IMPLEMENTED.

The completed source milestone is preserved by local branch
`anato12-clip-review-0.2a1`. See Git history for its exact commit; no push or
deployment is part of this checkpoint. The packaged app includes the audit,
development rules, lessons, bug log, test results and roadmap.
