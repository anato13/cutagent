# Development roadmap

Continue the existing app. Phase 2A is a reliability milestone, not completion of
the entire master request. Statuses apply to this milestone; see TEST_RESULTS.md
for exact checks and NOT_TESTED cases.

| Phase | Status | Deliverable / remaining acceptance |
| --- | --- | --- |
| 1 — inspect and preserve editor | VERIFIED_WORKING | Baseline inspected, 17 baseline tests passed, local recovery commit |
| 2A — persistent clip-review foundation | VERIFIED_WORKING | Linux: 53 tests from the extracted ZIP, real thumbnails/preview/export, durable reviews and interrupted job recovery |
| 2B — contextual humor and semantic search | BLOCKED | Adapter implemented; needs a real downloaded local model, quality evaluation on genuine gaming dialogue and human feedback |
| 3 — automatic long-form drafts / Shorts batches | PARTIALLY_IMPLEMENTED | Independent drafts and optional batch renders from approved ranges; chronological overlap merging. Semantic story assembly/hook selection remains NOT_IMPLEMENTED |
| 4 — personal assistant and general memory | NOT_IMPLEMENTED | Clip feedback is not an assistant or general memory |
| 5 — official read-only YouTube analytics | NOT_IMPLEMENTED | Requires OAuth app configuration and user authorization |
| 6 — thumbnail studio, planning, strategy/business tools | NOT_IMPLEMENTED | Earlier manually created assets do not constitute application features |
| 7 — full product reliability / Windows acceptance | PARTIALLY_IMPLEMENTED | Linux tests and synthetic 30s–120min checks pass; Windows, GPU and genuine 60/120-minute gaming acceptance remain |
| Last — image generation studio | NOT_IMPLEMENTED | Intentionally deferred until higher priorities are completed and accepted |

Next: run a real local 3B–8B quantized conversational model suitable for the
RTX 3060 Ti, record exact model/version and VRAM use, and evaluate supported
setup/punchline/reaction/callback candidates on genuine dialogue. Start with a
short labeled sample; measure missed/unsupported suggestions and boundary quality.
Do not call cue matching or a successful HTTP fixture contextual humor intelligence.

Alpha 2 adds CHECK_LOCAL_AI.bat and evaluate_model to collect actual model identity,
timing, supported candidates and blank human-review fields from a saved project.
Installed model changes invalidate caches; incomplete/unsupported replies fail
explicitly. Official Ollama downloads returned proxy HTTP 403 here, so phase 2B
remains BLOCKED for real inference. Use the check on a machine with a downloaded
model. High is appropriate for this bounded implementation and testing work.

Alpha 3 adds independent draft bundles from approved highlights for one source:
chronological main edit, merged overlaps, one complete range per Short, optional
MP4/caption rendering, manifest and cancellation cleanup. Overlong ranges are
reported as skipped Shorts rather than truncated. The current open project stays
unchanged. Batches are not resumable after process termination. This advances the
review/export workflow while semantic inference is blocked; phase 2B is not complete.

Then verify native Windows import, seeking, audio, project save/reopen and both
exports on the user's hardware. Preserve approved clips before improving automatic
draft editing. Separate main/Shorts projects are needed today: Add to Shorts changes
the current project's output ratio and appends a clip; there are not two independent
timelines in one editor window. The new draft button creates separate project files
without changing the open timeline. Feedback supplies category preferences, not fine-tuning.

Recommended reasoning: Extra High for model/evidence integration and interrupted
job correctness; High for ordinary UI/docs once those interactions settle. Ultra
has no demonstrated need at this milestone. The app cannot inspect Codex usage.
