# Validation of version 0.1.0

Verified in the Linux cloud workspace using Python 3.12.14, PySide6 6.8.3 and
FFmpeg/FFprobe 7.1.5:

- 17 automated tests passed.
- The actual Qt window imported a generated MP4, decoded a video frame for preview,
  selected a range, created/updated a clip, and exported a real 9:16 MP4.
- Real FFmpeg integration tests exported 16:9 and 9:16, joined multiple clips with
  matching audio/video duration, handled recordings without audio, and burned captions.
- Source overwrite prevention, preserving an existing export on cancellation,
  project round trips, subtitle offsets, SRT import and suggestion deduplication passed.
- Speech-model extraction and download cancellation tests passed.
- A fresh official tiny.en model download/extraction and actual local CPU
  transcription passed. A cached base.en model also produced timestamped dialogue.
  Recognition mistakes occurred, so reviewable/editable text is part of the app.
- Dependency resolution found binary wheels for the Windows x64 / Python 3.12
  core and speech setup, including the separate ONNX runtime package.
- The packaging hook discovered the speech ONNX runtime shared library.

Not verified here:

- Native Windows execution, hardware audio playback, a Windows EXE build or installer.
- The supplied Windows CI workflow has not been executed by this task.
- Suggestion quality as a humor detector; suggestions are text cues for human review.

The source ZIP deliberately excludes recordings, model weights, virtual
environments, temporary verification outputs, and existing repository/Git metadata.
