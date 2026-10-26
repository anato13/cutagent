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
