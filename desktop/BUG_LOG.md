# Bug log

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
validation; one editor timeline with a project-wide output ratio; synchronous local
model request cancellation can wait up to its 60-second network timeout; resuming
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
