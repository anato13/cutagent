"""Drive a real desktop workflow in a child process with a hard hang timeout."""
import os
from pathlib import Path
import subprocess
import sys
import time


def wait_until(app, predicate, seconds=25):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(.01)
    raise AssertionError("Desktop operation timed out")


def run_desktop(recording, destination):
    from PySide6.QtWidgets import QApplication, QFileDialog
    from anato12_studio.model import timestamp
    from anato12_studio.window import MainWindow
    app = QApplication([])
    window = MainWindow()
    failures, exported, frames = [], [], []
    window.fail = failures.append
    window._exported = exported.append
    window.show()
    window.player.video.videoSink().videoFrameChanged.connect(
        lambda frame: frames.append(frame.startTime()) if frame.isValid() else None)
    try:
        window.import_files([str(recording)])
        wait_until(app, lambda: window.job is None)
        assert not failures and window.current_media() is not None
        window.player.player.play()
        wait_until(app, lambda: len(frames) > 0)
        window.player.player.pause()
        window.range.start.setText(timestamp(.5))
        window.range.end.setText(timestamp(1.5))
        window.range_changed()
        window.add_clip()
        assert len(window.project.clips) == 1
        window.inspector.profile.setCurrentText("Shorts · 9:16")
        window.inspector.fit.setCurrentIndex(1)
        window.inspector.zoom.setValue(1.1)
        window.update_clip()
        assert window.project.clips[0].name == "Clip 1"
        # Exercise rapid UI updates: these must coalesce rather than seek recursively.
        for _ in range(5):
            window.update_clip()
        wait_until(app, lambda: abs(window.player.player.position() - 500) < 50)
        frames.clear()
        window.player.play_range()
        wait_until(app, lambda: any(t >= 450000 for t in frames))
        window.player.player.pause()
        # A portrait export must mask the cropped-away video in a wide preview widget.
        from PySide6.QtCore import QPointF
        left_edge = window.player.view.mapFromScene(QPointF(0, 0)).x()
        if left_edge > 20:
            preview = window.player.view.viewport().grab().toImage()
            color = preview.pixelColor(left_edge // 2, preview.height() // 2)
            assert (color.red(), color.green(), color.blue()) == (11, 14, 20)
        QFileDialog.getSaveFileName = lambda *a, **k: (str(destination), "")
        window.export()
        wait_until(app, lambda: window.job is None)
        assert not failures, failures
        assert exported == [str(destination)]
        window.grab().save(str(destination.with_suffix('.png')))
    finally:
        if window.job:
            window.cancel_job()
            wait_until(app, lambda: window.job is None)
        window.dirty = False
        window.close()
        app.processEvents()


def test_desktop_import_decodes_preview_and_exports(tmp_path, recording, binaries):
    from anato12_studio.video import probe
    destination = tmp_path / "desktop-short.mp4"
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_MEDIA_BACKEND="ffmpeg", PYTHONPATH=str(root))
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), str(recording), str(destination)],
                            cwd=root, env=env, capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr
    metadata = probe(str(destination), binaries[1])
    assert (metadata["width"], metadata["height"]) == (1080, 1920)
    assert abs(metadata["duration"] - 1) < .06


if __name__ == "__main__":
    run_desktop(Path(sys.argv[1]), Path(sys.argv[2]))
