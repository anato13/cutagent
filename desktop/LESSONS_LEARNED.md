# Engineering lessons

Use structured output for shape, then independently validate source references.
An actual model can obey the JSON schema and still misidentify the payoff or
invent the reason. Keep raw interpretations visible as unverified, use quoted
transcript labels, and leave human quality fields unset until reviewed.

Avoid asking a model to maintain redundant citation lists. A validated setup,
payoff or reaction ID is already a citation; derive its saved evidence from the
supplied source row. Do not invent text, accept unknown IDs, or rewrite the raw
response to hide what the model actually returned.

Reanalysis must refresh untouched suggestions without erasing decisions. Preserve
identity and all reviewed/manual changes while updating stale, unreviewed rows.
Overlapping dialogue boundaries can create duplicate Shorts after initial model
deduplication, so check overlap again after expanding the selected ranges.

Automatic selection is not approval. Keep its provenance distinct, validate
evidence against the current transcript, preserve complete boundary lines, and
reject a callback when the cited setup is absent. Budget limits should skip whole
exchanges rather than truncate a setup or reaction.

Persist observations, confirmed preferences and executable capability tests
separately. A transcript mentioning "zoom" is not proof of a demonstrated zoom;
a scene-score spike is not necessarily a cut; matching words are not audiovisual
alignment. Imported text must never become executable commands or silently become
personal preferences. Deletion/revocation must remove future prompt influence.

Check staged exports before publishing an automatic bundle. Full decode and
duration/dimension checks prove technical properties, not humor or story quality.
Once publication has completed, a late cancellation cannot honestly promise that
no output was created. Record both the completed files and any job-history failure.

Atomic replacement of one file does not make an MP4/SRT pair transactional. Stage both before touching old outputs, preserve originals through all file swaps, and test failures between swaps. Recovery itself can fail: retain backups, report their locations, and do not mask that error with a later cleanup failure.


A similar recording duration is not enough to validate a relink: even a half-second difference can invalidate a final clip or caption. Validate a detached candidate before replacing live state, then store its actual duration. Preserve completed progress on failures, and keep model defaults consistent with controls.


Source protection belongs in project persistence as well as video export. File-dialog filters cannot protect API callers, unusual extensions or hardlink aliases. Validate optional model metadata before using membership operations.


A real model can cite valid transcript IDs while inventing the explanation.
Inspect the reason against its evidence and preserve raw rejected proposals.
Successful HTTP/schema tests establish mechanics, not story comprehension or
humor. Stronger instructions alone did not make the tested small models reliable.

Checking cancellation only after a synchronous response makes Cancel wait for
generation. A watcher now shuts down the connected loopback socket, including
when headers or a partial body stall; no abandoned inference thread is left
waiting in the application. Keep a total deadline, response-size cap, TLS
verification and redirect rejection alongside cancellation.

Time limits alone cannot bound a model request: word-level captions, Unicode,
shared notes and callback references all add content. Use one message builder for
planning and sending, preserve complete source rows, and fail with an exact source
location when one row cannot fit. Validate model evidence against the references
actually supplied. Tests cover 14,400 dense synthetic rows, UTF-8 sizing, omitted
references and interrupted resume. A content-byte cap is not a measured token count.

Note text needs its own consent, separate from category ranking. Extending a
previous consent flag would silently change what old feedback sends to a model.
Schema 2 adds a default-off flag, with an interrupted-migration rollback test.
Bound note context, preview exactly what is shared and invalidate model-response
caches when shared preferences change. Private edits should not discard expensive
analysis caches. Editing feedback does not retrain model weights or rewrite clips.

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
