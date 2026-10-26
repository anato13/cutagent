# Engineering lessons

Approved batch workflows need their own complete source query, rather than
reusing a display-limited table. Keep output filenames controlled (titles are
metadata), preserve the open timeline and write multi-file work in an owned
temporary directory. Publish only after all requested outputs succeed. The
501-approval, actual batch export, mid-batch cancellation and GUI snapshot checks
cover these boundaries. Do not equate chronological assembly with story understanding.

Alpha 2: a model name does not identify its installed weights. Resolve the digest
and configuration before using cached results, and verify again after inference.
Invalid evidence is a failed model answer, not proof that no clip matches. Do not
cache those failures. Controlled replacement/response tests verify these fixes;
real semantic quality still needs separate human evaluation.

1. Qt multimedia behavior must be exercised, not inferred from compilation.
   PySide6 6.12 crashed during headless audio startup; 6.8.3 is pinned after real
   decode/export checks. This does not prove all native Windows drivers work.
2. Repeated synchronous setPosition calls during clip updates deadlocked Qt.
   A 35 ms coalescing timer, redundant-seek suppression and one-time loaded-media
   initialization fixed the reproduced workflow. GUI regressions run in a child
   with a hard timeout and verify actual decoded frames after seeking.
3. A QGraphicsScene sceneRect does not clip its video child. A clipping rectangle
   parent is required for an honest portrait preview; the regression checks pixels
   outside the crop, not just mathematical crop dimensions.
4. sherpa-onnx needs the matching sherpa-onnx-core runtime explicitly declared.
   A clean uv sync removed an undeclared runtime and broke actual inference.
   Matching 1.13.8 packages plus a real tiny-model run verified the correction.
5. Protect every export target, including SRT sidecars and hardlinks. Source
   protection limited to the MP4 could replace an unusually named recording.
6. Use PCM intermediates and encode AAC once after concatenation. Joining
   separately encoded AAC clips accumulated padding and audio/video drift.
7. A model may propose segment IDs; only the application derives timestamps and
   evidence quotes. Invalid IDs are discarded. Ranks are review order, not
   calibrated confidence. Fixture responses cannot establish semantic quality.
8. Feedback is opt-in and reversible. Compute preference weights from retained
   confirmed decisions so deleting feedback removes its influence.
9. A successful later shell command can hide a failed earlier check. Use set -e,
   inspect each process status, and never announce test success from package output.
10. Workspace download links were unusable in this chat. A verified temporary
    host was used only after user authorization. Do not upload private recordings
    or confuse a filesystem path with a delivered chat attachment.
11. Quiet long-file checks can expose control markers that short speech clips miss.
    Actual tiny.en returned BLANK_AUDIO before the late speech. Filter explicit
    control-only silence markers, preserve laughter/reaction evidence, bump the
    affected cache version and rerun actual inference. Do not claim this fixes
    arbitrary hallucinated words.
12. Test the styled interface at its intended window size. New review controls
    squeezed the nested export form, hiding its text. Scrollable review/data
    panels and explicit form control minimum heights corrected the layout;
    the GUI regression checks heights and the screenshot was inspected.
13. Normalize timestamp types before hashing transcript windows. Validation
    converted integer times to floats after the first hash, making an identical
    resumed window miss its cache. A controlled interruption/retry test reproduced
    the extra model call; validating first preserves completed responses and also
    verifies that different endpoints receive separate cache entries.
