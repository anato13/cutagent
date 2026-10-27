# Project audit — 2026-10-26

## 0.4.0a6 — bounded recovery from invalid analysis windows

Continues from 124caf3 with a recoverable branch and local Git bundle. A long
recording could stop at an early invalid model-reference window before later
valid windows were analyzed. Finder now skips only those invalid-reference
windows, never caches their responses, and reports each skipped section. If no
validated proposal survives, it fails with an actionable error. Auto Edit keeps
the diagnostic in its manifest. Import, transcription, review decisions, stored
feedback and media export code are unchanged. This is source-reference recovery,
not verified humor understanding or full editorial autonomy. See TEST_RESULTS.md.

## 0.4.0a5 — finder diagnosis and local conversation

A connected model was listed in the UI while the Analyze engine remained on
Context cues. Connecting now selects Local Ollama. The completed job reports
the actual method, timestamped transcript count and context-window count; a
missing transcript and invalid model references have actionable errors. The
bounded session chat uses only the selected loopback local model and typed
messages. No source media is sent by chat. Video import, speech and export paths
are unchanged. See TEST_RESULTS.md for real qwen2.5:7b evidence and remaining
humor-quality limits.

## 0.4.0a4 — initial Anato12 humor profile

Anato12's stated preferences are documented in PERSONAL_STYLE.md and used in
the local model's selection prompt. Candidates may carry a provisional 1–5 taste
estimate; it affects ordering only after the source-reference checks pass. This
is a subjective model rating, not calibrated humor confidence or measured viewer
engagement. Existing opted-in feedback and own-video notes remain separate and
continue to influence future requests. No model weights are trained.

Prompt/schema/cache versions changed, so old model-window responses cannot be
reused under the new style. Source, feedback, approval, project and database
formats are unchanged. Existing Auto Edit operations remain as documented in
0.4.0a3 below. Speaker identification, audio/visual joke understanding,
automatic hook/story construction, thumbnails and title/description drafting
remain future work or experimental; see PERSONAL_STYLE.md.

## 0.4.0a3 — complete Shorts and packaged capability checks

Continues from da9bf15, preserved in `anato12-before-short-selection` and a
complete local recovery bundle. No dependency, project-format, database-schema
or model-prompt change. Existing reviewed decisions and approved-draft exports
are preserved.

Auto Edit now keeps the normal ranked selection when it can produce both
formats; otherwise it reserves the highest-priority eligible complete Short and
refills the remaining budget. This may displace a longer approved exchange for
this run without altering its saved review. Evidence, rejection, whole-line,
overlap and duration checks still apply. Skip reasons explain the reservation.
Selection now checks cancellation during validation, boundary expansion and
budget choice. Errors saving failed/cancelled job history no longer mask the
original failure or cancellation.

Capability identity now reads installed code through the Python module loader,
so a PyInstaller archive does not need loose `.py` files. Code/engine changes
still require fresh operation tests; unavailable code identity fails explicitly.
The frozen Linux harness passed all four real operation tests and reused the
same passes after process restart. See TEST_RESULTS.md for exact source and
packaged verification. Native Windows/RTX
acceptance remains NOT_TESTED. Automatic humor and story quality remain
PARTIALLY_IMPLEMENTED; this release does not add semantic story planning.

## 0.4.0a2 — exchange references and reanalysis reliability

Continues from 484b867; a pre-change branch and complete recovery bundle preserve
alpha 1. SQLite schema 4 adds highlight exchange maps in the existing migration
transaction; project JSON and dependencies are unchanged. Old reviewed and manually
adjusted rows are preserved. Untouched unreviewed rows now refresh on reanalysis.

New local-model requests include a JSON response schema constrained to supplied
IDs, with independent client-side checks for role references, order and context
assessment. New labels use source transcript snippets. Unverified model prose is
explicitly labeled in the UI. Auto Edit skips legacy/stale maps, requests for more
context and substantial overlap after boundary expansion. The manifest includes
actual setup/payoff/reaction quotes without certifying their semantic labels.

Reference validation, persistence, migration rollback and the real Qt/FFmpeg flow
are VERIFIED_WORKING in Linux tests. Actual qwen3:8b inference with the final
contract produced checked 55-second main and portrait videos from one genuine
sample. Broad semantic quality remains PARTIALLY_IMPLEMENTED: a valid map can
still contain a mistaken interpretation, and two other samples produced no
candidates. See TEST_RESULTS.md for exact measurements and remaining limits.

## 0.4.0a1 — autonomous editing and persistent learning foundation

Continues from b7c03d7; the prior state is preserved in branch
`anato12-before-autonomous-learning` and a complete local recovery bundle.
No architecture restart, remote push, paid API or new dependency. Project JSON
stays version 1. SQLite schema 3 adds learning tables with transactional migration.

| Area | Status | Scope |
| --- | --- | --- |
| Existing editor / approved drafts | VERIFIED_WORKING | Regression-tested in Linux; original workflows retained |
| Auto Edit orchestration and technical checks | VERIFIED_WORKING | Fixture-model Qt/FFmpeg end-to-end tests; unattended selection, rendering, full decode and staged publication |
| Automatic funny-moment and story quality | PARTIALLY_IMPLEMENTED | Existing local model proposes ranges; conservative extraction, chronological assembly, no semantic hook/story planner |
| Persistent learning library | VERIFIED_WORKING | Local source indexing, search, timestamps, sampled frames, corrections, deletion/export and shared own-video notes |
| Tutorial / creator understanding | PARTIALLY_IMPLEMENTED | Technique-word hypotheses and measured possible scene changes; no semantic visual demonstration or engagement understanding |
| Original/finished comparison | PARTIALLY_IMPLEMENTED | Unique exact transcript matches with both source references/times; no audiovisual alignment or learned keep/discard classifier |
| YouTube URL ingestion | PARTIALLY_IMPLEMENTED | Saves clearly labeled unviewed references; downloading/viewing URLs is NOT_IMPLEMENTED |
| Executable technique tests | VERIFIED_WORKING | Fixed recipes, real synthetic render/decode tests tied to installed engine/code; observations cannot enable code |
| Recovery | PARTIALLY_IMPLEMENTED | Durable jobs, cached analysis retry, failed/cancelled stage cleanup; no encoded-batch continuation or power-loss guarantee |

See LEARNING_SYSTEM.md for architecture and TEST_RESULTS.md for the actual
acceptance evidence. Model quality, Windows/RTX execution and genuine full-length
unattended editing remain separate unresolved acceptance requirements.

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

## 2026-10-27 local AI intelligence increment

The existing desktop editor remains in place. Checkpoint `dedcc58` and local
branch `anato12-before-intelligence-upgrade` preserve the prior Studio plus
standalone Personal AI baseline. No user project, recording, model, or existing
review database was modified for this upgrade.

| Capability | Status | Evidence / limit |
| --- | --- | --- |
| Four routing modes and manual installed-model override | VERIFIED_WORKING | Pure routing tests and local model catalog; routing is a heuristic, not a quality guarantee |
| Explicit single-model install option and progress | PARTIALLY_IMPLEMENTED | Simulated pull/progress, storage checks and registry pages verified; real Windows pull NOT_TESTED |
| Qwen3 8B contextual inference | PARTIALLY_IMPLEMENTED | One source-valid candidate on a synthetic exchange; no human-reviewed recording acceptance |
| Qwen3 14B / Gemma 3 12B | IMPLEMENTED_UNTESTED | Official tags available; neither installed here, so generation and RTX fit NOT_TESTED |
| Single-frame local vision path | PARTIALLY_IMPLEMENTED | FFmpeg JPEG extraction and vision API contract tests; actual Gemma vision NOT_TESTED |
| Personal AI memory bridge | VERIFIED_WORKING | Live local API switched Qwen2.5 7B to Qwen3 8B in one saved conversation with the same retrieved memory ID |
| Model process/resource display | PARTIALLY_IMPLEMENTED | Ollama token timings, loaded-model data and host RAM measured in Linux; RTX VRAM/NVIDIA monitoring on Windows NOT_TESTED |
| Humor quality on actual Anato12 recordings | BLOCKED | No reviewable real-recording comparison in this milestone |

Confirmed Personal AI humor/editing notes enter the bounded clip-analysis prompt
only after the user enables the new checkbox. They are preferences, not evidence
or retrained weights. The prompt version and cache key include the changed context
and model configuration, so revoked notes or model switches cannot reuse stale
window answers. Studio chat can use the separate Personal AI service for durable
history; when disabled, chat remains session-only but survives model switches
within that session. Auto Edit uses the same installed-model routing.

## 2026-10-27 multi-moment Finder correction

The user's report is that a full timestamped transcript yields one Finder moment,
so Auto Edit uses that moment for both the main video and a Short. The selector
and bundle builder accept multiple distinct candidates; the shortage arises
before assembly. This environment does not contain the user's current Studio
project or its Finder logs, so that project's model responses remain unverified.

| Capability | Status | Evidence / limit |
| --- | --- | --- |
| Sparse-window advance | VERIFIED_WORKING | A 30-second-plus dialogue gap no longer creates a redundant partial window; unchanged IDs/times covered in regression |
| Second distinct-dialogue review | PARTIALLY_IMPLEMENTED | Local-model focus, excluded IDs, separate identity-aware cache and citation validation covered by fixtures; real user recording NOT_TESTED |
| Multi-moment export safeguard | VERIFIED_WORKING | Auto Edit refuses a requested multi-range export when only one complete range survives; FFmpeg fixture verifies no bundle is published |
| Real humor recall / finished multi-moment Anato12 video | BLOCKED | Requires the actual recording, reviewable source-timestamped suggestions and human playback review |

The Finder UI reports first- and second-pass sections and newly validated
distinct moments. Requests remain cancellable and the source/reviews are not
rewritten. The second pass may still return no additional supported exchange;
it must not invent moments to satisfy a target count.

An older real Anato12 recording supplied a bounded acceptance sample: 82
phrase-timestamped lines from five source regions yielded two cited Qwen3
suggestions at 323.92–356.42s and 422.18–506.092s. The second was discovered
in the coverage pass. Both passed automatic complete-range checks, and FFmpeg
rendered a two-range main MP4 plus one complete Short with full-decode checks.
This verifies **technical multi-moment assembly on that sample**. The whole
recording, the user's current Windows project, humor quality and publication
readiness remain NOT_TESTED. The other chosen exchange exceeded the 60-second
Short limit and was reported as skipped.
