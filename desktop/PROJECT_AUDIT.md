# Project audit — 2026-10-26

Version 0.3.0a7 continues from 59cbc0b with recoverable MP4/SRT publication. Prior outputs are renamed to sibling backups, then restored if publication fails or is cancelled. Successful publication removes backups where permitted. No dependency, project or database schema changes. This is ordinary-error recovery, not atomic multi-file persistence across power loss.


Version 0.3.0a6 continues from b925fbc: transactional relinking validation, retained failure progress, and consistent new-project caption defaults. No dependency/schema change. Native Windows/GPU acceptance remains NOT_TESTED; semantic quality remains PARTIALLY_IMPLEMENTED.


Version 0.3.0a5 continues from 2cc680f. Adds source-file protection to project saving and explicit malformed model-capability errors. No dependency or schema changes. AI quality remains PARTIALLY_IMPLEMENTED; Windows/GPU acceptance remains NOT_TESTED.


Version 0.3.0a4 continues from 1c1246c. The published network change now permits
official Ollama/runtime downloads; the previous network blocker is resolved.
Ollama 0.40.11 runs explicitly on loopback with cloud features disabled. Runtime
and model layers were checksum verified and stay outside the source distribution.

Real-model testing now distinguishes transport success, valid source references,
and semantic quality. Valid IDs alone did not prevent unsupported explanations.
The adapter closes active sockets on cancellation, enforces a total request
deadline, and retains bounded server timing/token measurements. The evaluator
records original proposals and distinguishes invalid evidence from empty output.
The shared prompt requests complete exchanges and has a new cache version.
Thinking-capable local models use non-thinking mode to reserve the output budget
for review JSON; this does not change Codex's reasoning setting. No dependencies,
project format or database schema changed. See the latest TEST_RESULTS.md entry
for measurements and unverified acceptance requirements.

Final extracted-package verification: 96 tests passed, 0 failed, 0 skipped.
This milestone is preserved on local branch anato12-real-model-0.3a4, with a
complete Git recovery bundle outside the checkout. No remote push was performed.

The sections below preserve earlier milestone evidence and blockers at that time.

Version 0.3.0a3 continues from fcb652f. Model analysis and the standalone evaluator
now share a bounded-window planner and message construction. Complete rows keep
source identity/timestamps, callback references are restricted to what was sent,
and caches include section endpoints, supplied callbacks and prompt version.
No new dependencies or database/project-schema changes. A saved network draft
adds the two official Ollama hosts; live access remains blocked pending user action.

Final package verification: 82 tests passed. Checkpoint branch:
anato12-context-0.3a3. The configuration draft was independently read back at
revision 5: restricted network mode, package-manager presets and all six prior
custom hosts were retained; only ollama.com and registry.ollama.ai were added.
Saving is confirmed; application/publication/runtime access is not.

Version 0.3.0a2 continues from 13b867b with a schema-2 consent column on feedback,
defaulting to disabled for every existing row. Consent-column/version migration
is transactional. No project-file format or dependency changes. Local-model
context now includes separately opted-in bounded notes, and the UI supports
editing/revoking them and inspecting the actual context. Ordinary category
ranking remains independently optional. Semantic effectiveness remains unverified.

Final package verification: 76 tests passed, including legacy migration/rollback,
note-consent transport and real Qt editing/revocation. Checkpoint branch:
anato12-feedback-0.3a2. No remote push or new dependency is included.

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
