# Bug log

B40 — VERIFIED_WORKING: connecting to Ollama populated model names but left
AI Clip Finder on the default Context cues engine. Analyze could then report
zero without calling Ollama. Connecting now selects local-model mode, and the
result names the actual analysis method and transcript/window counts. A real
qwen2.5:7b sample yielded a reviewable timestamped candidate after direct
model evaluation; the specific user's earlier run has no captured job log.

B41 — VERIFIED_WORKING: an empty cue/model result previously displayed only
"0 candidates", obscuring the method and input. Empty transcript now stops with
a useful message; an invalid source-reference response names its section and
time. Partial invalid proposals are reported. A valid empty model response remains
possible and is not labeled a malfunction.

B39 — OPEN: a local qwen3:8b run over 28 windows of the supplied 28-minute
recording (previous prompt version) yielded three structurally usable candidates,
while two windows had proposals with invalid references. A known photo dispute
appeared in the full transcript and yielded no suggestion in its overlapping
windows, although a smaller isolated sample yielded one. This is a recall and
context-sensitivity concern, not a measured humor-accuracy score. Invalid model
references still stop the current Auto Edit pipeline; safe partial-window handling
needs separate implementation and testing. PERSONAL_STYLE.md is an initial user
preference, not proof this problem is fixed.

B35 — VERIFIED_WORKING (focused regression): a longer top-ranked range could
fill the clip/time budget and block all Shorts even with an eligible shorter
range available. Auto Edit now reserves one whole Short only when needed,
refills the remaining budget and reports displaced choices. Real FFmpeg outputs
and rejection/evidence/boundary/budget constraints are covered.

B36 — VERIFIED_WORKING (focused regression): cancellation was not checked while
Auto Edit selected and expanded ranges. Checks now occur during transcript
validation, boundary scans and budget selection without changing input records.

B37 — VERIFIED_WORKING (injected storage failure): failed/cancelled history
writes could replace the original exception. The original actionable error or
cancellation now survives; interrupted history is still recovered on restart.

B38 — VERIFIED_WORKING (Linux frozen executable and unit checks): capability
checks assumed loose Python source files existed beside
`__file__`, which does not hold in a PyInstaller PYZ archive. Installed code is
now fingerprinted through its loader. Missing code still blocks reuse of old
passes. See TEST_RESULTS.md for packaged execution evidence and platform limits.

B31 — VERIFIED_WORKING: reanalysis previously returned stale unreviewed rows even
after the transcript/model response changed. It now refreshes only untouched
unreviewed suggestions, keeping their IDs and preserving all reviewed or manually
adjusted data. Regression exercises approved, rejected and manually adjusted rows.

B32 — VERIFIED_WORKING: new model-generated labels could present an invented
headline as a clip name. Labels now use quoted transcript snippets; raw model
headlines remain in provenance, and the explanation is explicitly unverified.
This avoids presenting generated headlines as facts; it does not solve B20.

B33 — VERIFIED_WORKING: Auto Edit now rejects missing/stale exchange maps and
explicitly context-dependent proposals, and removes substantial overlap after
boundary expansion. Roles cite source rows directly; a missing duplicate in the
extra evidence list does not discard an otherwise valid source reference.

B34 — VERIFIED_WORKING: falsy malformed model capability metadata (0, false,
empty object/string) no longer masquerades as an empty capability list. Responses
over the four-candidate limit are rejected instead of silently truncated.

Still OPEN: B20, unsupported explanations and wrong role meanings despite valid
references. Structured JSON controls shape, not truth, humor or story quality.

B27 — VERIFIED_WORKING (Linux regression): Auto Edit now extends boundaries to
retain intersecting transcript lines, rejects stale/missing evidence and absent
callback setup, and respects rejected overlaps. This prevents those structural
failures; it does not establish semantic completeness or fix unsupported reasons.

B28 — VERIFIED_WORKING (Linux regression): a committed Auto Edit result is reported
as saved even if Cancel arrives after folder publication. Job-history update
failures report the saved folder separately. Crash-atomic folder/history updates
are NOT_IMPLEMENTED; see recovery limitations before retrying interrupted jobs.

B29 — VERIFIED_WORKING (Linux regression): newly introduced learning tables migrate
transactionally from schema 2. Injected migration failure keeps the old schema and
feedback; ordinary reindexing preserves existing confirmed/rejected corrections.

B30 — VERIFIED_WORKING (Linux regression): relative profile paths are normalized
before FFmpeg changes its working directory, preventing nested/incorrect paths
for capability fixtures and thumbnails.

Open: semantic visual tutorial/creator analysis, supported humor explanations
(B20), reliable automatic hook/story selection, Windows acceptance, and forced-stop
cleanup. Technical checks and example confirmation must not be presented as
evidence that these open issues are solved.

B26 — Export publication could replace an existing MP4 before caption copying/replacement failed, leaving mismatched versions. Both files are now staged first; sibling backups support rollback on ordinary errors and cancellation. Failed recovery preserves originals in named backups and reports their paths. Process termination/power-loss recovery is not implemented.


B23 — Relinking now validates every existing clip and caption against the actual new duration before changing the project. Invalid relinks preserve the entire prior state.

B24 — Failed analysis retains its last completed progress instead of resetting to zero.

B25 — New projects now consistently start with optional SRT export disabled in both saved data and visible controls.


B21 — VERIFIED_WORKING: project saving now rejects a source recording path or hardlink alias before writing. Direct/alias preservation and normal save/reopen regressions added.

B22 — VERIFIED_WORKING: malformed nonempty model capabilities now produce an actionable validation error before inference. Scalar, string and mixed-list regressions added.

B20 remains OPEN: unsupported model explanations are not solved by these fixes.


| ID | Severity / reproduction | Cause and correction | Evidence / limit |
| --- | --- | --- | --- |
| B19 | Medium: cancel during local-model inference | Cancellation was checked only after a blocking response. The transport now shuts down the active socket and enforces a total deadline | Stalled headers/body HTTP regressions; actual Ollama returned at 1.035s for a cancellation at 1s, compared with 5.109s before the fix |
| B20 | High, OPEN: a model cites real IDs but invents an explanation | Reference validation cannot establish semantic support. Real 3B/7B checks exposed this; stricter prompts alone did not resolve it | Preserve raw proposals, review reasons against source dialogue, and keep semantic quality PARTIALLY_IMPLEMENTED |


| ID | Severity / reproduction | Cause and correction | Evidence / limit |
| --- | --- | --- | --- |
| B18 | High: dense/oversized caption text plus feedback in a 90-second window | Time-only grouping imposed no content limit. A shared planner bounds serialized UTF-8 content, preserves complete rows and rejects a line too large to fit | test_model_context.py; actual server truncation/humor impact NOT_TESTED |

New context protection: earlier callback evidence is accepted only if included
in that section's actual request. Omitted links are counted in evaluator reports.
The byte limit does not establish exact tokenizer capacity; native model/GPU
validation remains pending, and dense input can increase the number of requests.

Feedback update verification: schema v1→v2 changes the consent column and version
in one transaction; injected pre-commit interruption preserves v1 rows/schema.
Old category opt-in never grants note sharing. Private-note edits retain cached
model responses; changing shared/ranking feedback invalidates those responses.
Regression coverage: test_feedback.py and the real finder Qt workflow. No new
humor-quality or native Windows fix is claimed. Older releases intentionally
refuse schema 2; use a pre-upgrade backup for rollback.

Alpha 3 defensive checks (no claim of previously shipped defects): the new batch
query bypasses the 500-row display cap, with a 501-approval regression. Overlaps
merge only for the main edit; Shorts use complete approved ranges. Cancellation,
including after one real MP4 has completed, removes the entire unpublished bundle.
Simulated disk-write failure and changed-source checks preserve existing files.
Known new limit: forced process termination may leave a hidden temporary folder;
draft batches restart from scratch and are not represented as resumable analysis jobs.

Alpha 2 corrections:

| ID | Severity / reproduction | Expected vs actual, cause and fix | Regression |
| --- | --- | --- | --- |
| B15 | High: replace weights under the same model name | Old answers were reused because the cache keyed the name. Digest/configuration now participate; mid-request changes fail before caching | Model identity and interrupted-window cache tests |
| B16 | Medium: all proposed evidence IDs are invented | Previously became zero candidates and was cached. Now fails explicitly and is not cached | test_invalid_model_evidence_is_not_cached_as_no_match |
| B17 | Medium: incomplete or nontext chat content | Could accept partial results or throw an attribute error. Now reports incomplete/nontext responses | test_incomplete_or_nontext_model_responses_fail |

| ID | Problem / root cause | Verified correction / remaining limit |
| --- | --- | --- |
| B01 | Qt 6.12 headless multimedia startup crash | Pin 6.8.3; real offscreen GUI checks. Native Windows NOT_TESTED |
| B02 | Repeated seek calls caused playback deadlock | Coalesced seeks and once-only media initialization; hard-timeout GUI regression |
| B03 | Portrait preview showed cropped-away image | Graphics clipping parent; pixel masking regression |
| B04 | Clean speech install lacked ONNX runtime library | Explicit matching sherpa-onnx-core; fresh tiny-model inference |
| B05 | Caption sidecar could overwrite a source | Protect both targets and file identity; real regression |
| B06 | Concatenated AAC introduced cumulative timing drift | PCM intermediates, one final AAC encode; stream duration comparison |
| B07 | Later shell command masked earlier failed test status | Require set -e and separately inspect test completion |
| B08 | Literal substring search matched date inside update | Whole-word matching; new finder regression |
| B09 | Model-window cache omitted source/endpoint identity | Include source fingerprint and endpoint in cache signature |
| B10 | Restoring a thumbnail did not start requested preview | Completion callback restores image and starts range playback |
| B11 | Restarted analysis could unnecessarily retranscribe imported dialogue | Reuse persisted analysis transcript; resume regression |
| B12 | Real long-file ASR returned a blank-audio control marker before speech | Suppress explicit silence/control-only markers; cache version bumped; real inference rerun and controlled pipeline regression. General hallucinations remain possible |
| B13 | Finder's minimum content height squeezed export controls at 910 px window height | Scrollable finder/data panels and minimum form control heights; styled GUI height assertion and screenshot inspection |
| B14 | Integer transcript times changed to floats after the first cache hash, causing redundant model calls on resume | Validate/canonicalize times before forming rows and hashing; interrupted-window cache regression |

Known limitations: semantic humor quality is unverified; no native Windows or GPU
validation; one editor timeline with a project-wide output ratio; local
model quality remains under evaluation; resuming
ASR re-extracts a temporary WAV. No automatic long-form story editor or personal
assistant exists yet. Never silently classify these as verified features.

## Reproduction, severity and regression evidence

The first table records actual behavior, root cause and correction. These rows
add the expected behavior and reproducible check. Fixes are verified in the tested
Linux environment; they are not claims of native Windows acceptance.

| ID | Severity | Reproduction → expected behavior | Regression / evidence |
| --- | --- | --- | --- |
| B01 | High | Start multimedia with Qt 6.12 in cloud → app should start | Pinned 6.8.3; both test_desktop/test_finder_desktop real frame checks |
| B02 | High | Repeated Update selected / seek → UI should keep responding | test_desktop_import_decodes_preview_and_exports |
| B03 | Medium | Fill a portrait frame in wide preview → hide cropped-away regions | Same test checks outside-frame pixels |
| B04 | High | Clean speech install without declared core → inference should load | Matching runtime declared; fresh actual tiny.en run; speech dependency lock |
| B05 | High | Name source output.srt, export output.mp4 with captions → refuse overwrite | test_caption_sidecar_cannot_replace_recording |
| B06 | High | Join several clips → matching audio/video duration | test_join_has_matching_audio_and_video |
| B07 | High | Failed test followed by successful package command → report failed test | Shell workflow uses set -e and separate completion inspection; no runtime test |
| B08 | Low | Search date in dialogue containing only update → no match | test_literal_search_no_fake_match_or_substring |
| B09 | Medium | Same transcript with a different source/server → separate cache identity | Source/endpoint in cache key; controlled adapter test verifies separate endpoint calls; real semantic inference NOT_TESTED |
| B10 | Medium | Adjust range then Preview without its new thumbnail → restore frame and play | test_finder_ui_review_preview_adjust_export_restart |
| B11 | Medium | Resume analysis with stored imported transcript → skip redundant ASR | test_resumed_analysis_reuses_saved_imported_transcript |
| B12 | Medium | Whisper emits BLANK_AUDIO → no spoken caption for control marker | test_transcription_ignores_blank_audio_marker_preserves_reaction plus actual long-file rerun |
| B13 | Medium | Open styled Finder in a 1400×910 window → export controls remain legible | GUI control-height checks and screenshot; scrollable panels |
| B14 | Medium | Interrupt analysis with integer timestamps then resume → reuse the completed window | test_interrupted_model_analysis_reuses_completed_windows_and_separates_endpoints |
