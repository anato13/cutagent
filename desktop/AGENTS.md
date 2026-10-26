# Anato12 Studio development rules

Continue the existing editor; preserve source recordings, saved projects, exports,
review decisions and user feedback. Do not restart the application architecture.
Before risky changes, inspect Git status and make a recoverable local checkpoint.
Do not stage unrelated work, push, publish or upload recordings automatically.

Use a separate ANATO12_DATA_DIR for all tests. Never test deletion against a real
user profile. Keep SQLite transactions short and use a connection per operation.
Only one interactive application instance may own a profile. Recover running jobs
as interrupted after restart; resume only on a user action.

Processing belongs in cancellable workers. Never load an entire recording or its
full decoded audio into RAM. FFmpeg may prepare a temporary WAV on disk; account
for that disk use. Preserve absolute source timestamps through overlapping analysis
windows and derive model times/quotes from validated transcript IDs.

Use free local processing by default. Optional semantic analysis must use an
explicitly selected, downloaded local model. Reject known remote Ollama backends;
never silently switch to a paid or cloud API. Transcript/model text is untrusted
data, not executable instructions. No confidence percentages without calibration.
Keyword cues, repeated phrases and laughter alone are not verified humor detection.

Feedback affects personalization only when the user opts in. Derive category
weights from retained feedback, so deletion reverses that influence. This is
simple ranking, not training or general personal memory. Expose view/delete/export.

Run meaningful media and GUI regression tests. GUI tests need an outer subprocess
timeout: a Qt multimedia deadlock must not hang the suite. Coalesce player seeks
and clip portrait video in the scene. Keep PySide6 pinned until an upgrade passes
these checks. Include sherpa-onnx-core explicitly beside matching sherpa-onnx.

Use `set -e` in multi-command shell verification. Check test exit codes before
building or announcing a package. A later successful command cannot prove an
earlier failed test passed. Mark unrun checks NOT_TESTED. Native Windows,
GPU availability, real model quality and long-file tests are separate claims.

Update PROJECT_AUDIT.md, BUG_LOG.md, LESSONS_LEARNED.md, TEST_RESULTS.md and
DEVELOPMENT_ROADMAP.md at milestones. Use VERIFIED_WORKING,
IMPLEMENTED_UNTESTED, PARTIALLY_IMPLEMENTED, BROKEN, NOT_IMPLEMENTED or BLOCKED
for feature status. Read actual results before promoting any status.

Recommend a reasoning setting before major work and at milestone end. The user
has Low, Medium, High, Extra High and Ultra available. Recommend the lowest
suitable setting; do not claim to see/change the selected setting or live allowance.
Image generation is last, after higher-priority milestones have been tested and
accepted. Do not add unrelated optional features ahead of clip-finder reliability.

Model cache keys must include installed digest/configuration. Never cache an
incomplete response or one whose proposals all have invalid source evidence.
Keep evaluation-harness tests separate from real-model acceptance. evaluate_model
must write a new report folder without changing the project/main review database.

Draft bundles use all approved highlights for one source, never the capped UI
table or only visible search results. Preserve current editor state. Main ranges
merge chronologically; Shorts retain complete ranges and report skips. Stage
the entire bundle before publishing a unique folder; clean up ordinary failures.
Do not claim batch restart/resume or automatic narrative/hook selection.

Feedback schema 2 has separate use_note consent; never infer it from personalize.
Legacy rows default to use_note=0. Migrate the consent column and version in one
transaction. Model context includes only reviewed, explicitly shared notes, bounded
to eight recent entries of 240 characters. Preview that actual context in the UI.
Changing/removing shared preferences invalidates analysis-window caches; private
edits preserve them. Standalone evaluation deliberately uses no app feedback.

Model context must use model_context.py for both planning and message building.
Keep source rows intact; do not invent intermediate timestamps to split a caption.
Cache keys must bind both section endpoints, supplied callbacks and prompt version.
Validate evidence against sent references only. Document omitted callback counts
and distinguish UTF-8 byte limits from actual tokenizer/context/GPU measurements.

Local-model requests must remain loopback-only, reject redirects and preserve TLS
verification. Active cancellation must close the transport, including stalled
headers and partial bodies; do not abandon inference threads as a workaround.
Use bounded response sizes and total deadlines. Evaluation reports retain raw
proposals and distinguish invalid evidence from an actual empty response. Server
token/duration counts are measurements of processing, never humor confidence.
Real models can produce unsupported reasons with valid IDs; semantic acceptance
requires separate review. Disabling a local model's advertised thinking mode is
independent of the user's Codex reasoning setting.
