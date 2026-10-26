"""Actual clip-finder UI actions/export/restart in a hard-timeout Qt process."""
import os
from pathlib import Path
import subprocess
import sys

from test_desktop import wait_until


def run_finder(recording, destination):
    from PySide6.QtWidgets import QApplication, QFileDialog
    from anato12_studio.finder_jobs import thumbnail_path
    from anato12_studio.model import Segment
    from anato12_studio.window import MainWindow
    from anato12_studio.__main__ import STYLE
    app = QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    failures, exports, frames = [], [], []
    window.fail = failures.append
    window._exported = exports.append
    window.show()
    def select_first():
        window.finder.table.selectRow(0)
        app.processEvents()
    try:
        window.import_files([str(recording)])
        wait_until(app, lambda: window.job is None)
        assert not failures, failures
        media = window.current_media()
        media.transcript = [Segment(.1, .7, "Did you open the door?"),
                            Segment(.8, 1.5, "No actually that was the wrong door"),
                            Segment(1.6, 2.2, "Wait what?"),
                            Segment(2.3, 3.2, "[laughing] Oh my god")]
        window.refresh_transcript()
        window.finder.analyze.emit()
        wait_until(app, lambda: window.job is None)
        assert not failures, failures
        assert window.finder.table.rowCount() == 1
        select_first()
        controller = window.finder_controller
        identifier = controller.current()["id"]
        assert thumbnail_path(controller.store, controller.current()).exists()
        assert not window.finder.thumbnail.pixmap().isNull()
        window.finder.start.setValue(.5)
        window.finder.end.setValue(1.5)
        window.finder.title.setText("Chosen moment")
        window.finder.action.emit("save")
        window.finder.action.emit("approve")
        assert controller.current()["status"] == "approved"  # selection survives refresh
        window.finder.feedback.setText("Keep the conversational setup")
        window.finder.personalize.setChecked(True)
        window.finder.action.emit("feedback")
        assert controller.store.preferences() == {"misunderstanding": 1}
        window.tabs.setCurrentWidget(window.finder)
        app.processEvents()
        assert window.inspector.profile.height() >= 30
        assert window.inspector.fit.height() >= 30
        window.grab().save(str(destination.with_suffix(".png")))
        window.player.video.videoSink().videoFrameChanged.connect(
            lambda frame: frames.append(frame.startTime()) if frame.isValid() else None)
        window.finder.action.emit("preview")
        wait_until(app, lambda: any(t >= 450000 for t in frames))
        window.player.player.pause()
        window.finder.action.emit("main")
        window.finder.action.emit("shorts")
        assert len(window.project.clips) == 2 and "9:16" in window.project.profile
        # Export only the selected highlight, despite two clips in the timeline.
        QFileDialog.getSaveFileName = lambda *a, **k: (str(destination), "")
        window.finder.action.emit("export")
        wait_until(app, lambda: window.job is None)
        assert exports == [str(destination)] and not failures, failures
        # Create independent drafts without altering this open, unsaved timeline.
        from dataclasses import asdict
        from anato12_studio.finder_ui import DraftDialog
        from anato12_studio.model import Project
        before = asdict(window.project)
        was_dirty = window.dirty
        bundles = []
        controller._drafts_ready = bundles.append
        DraftDialog.exec = lambda self: DraftDialog.DialogCode.Accepted
        QFileDialog.getExistingDirectory = lambda *a, **k: str(destination.parent)
        window.finder.drafts.emit()
        wait_until(app, lambda: window.job is None)
        assert not failures and len(bundles) == 1, failures
        assert asdict(window.project) == before and window.dirty == was_dirty
        bundle = Path(bundles[0]["directory"])
        assert Project.load(bundle / "YouTube.anato12.json").profile == "YouTube · 16:9"
        assert Project.load(bundle / "Short-001.anato12.json").profile == "Shorts · 9:16"
        # A new project clears old-source candidates; persisted review remains.
        window.dirty = False
        window.new_project()
        assert window.finder.table.rowCount() == 0
        assert controller.store.highlight(identifier)["status"] == "approved"
    finally:
        if window.job:
            window.cancel_job()
            wait_until(app, lambda: window.job is None)
        window.dirty = False
        window.close()
        app.processEvents()
    second = MainWindow()
    second.fail = failures.append
    try:
        second.import_files([str(recording)])
        wait_until(app, lambda: second.job is None)
        second.finder.table.selectRow(0)
        saved = second.finder_controller.current()
        assert (saved["id"], saved["status"], saved["start"], saved["end"]) == (identifier, "approved", .5, 1.5)
        assert len(second.finder_controller.store.feedback()) == 1
        assert not failures, failures
    finally:
        second.dirty = False
        second.close()
        app.processEvents()


def test_finder_ui_review_preview_adjust_export_restart(tmp_path, recording, binaries):
    from anato12_studio.video import probe
    destination = tmp_path / "chosen.mp4"
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_MEDIA_BACKEND="ffmpeg", PYTHONPATH=str(root),
               ANATO12_DATA_DIR=str(tmp_path / "profile"))
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), str(recording), str(destination)],
                            cwd=root, env=env, capture_output=True, text=True, timeout=50)
    assert result.returncode == 0, result.stdout + result.stderr
    metadata = probe(str(destination), binaries[1])
    assert abs(metadata["duration"]-1) < .06 and metadata["has_audio"]
    assert (metadata["width"], metadata["height"]) == (1080, 1920)


if __name__ == "__main__":
    run_finder(Path(sys.argv[1]), Path(sys.argv[2]))
