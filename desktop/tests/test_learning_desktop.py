"""Real Qt learning/Auto Edit workflow in an isolated, hard-timeout process."""
from dataclasses import asdict
import os
from pathlib import Path
import subprocess
import sys

from test_desktop import wait_until
from test_local_model import endpoint  # noqa: F401


def run_learning(recording, output, url):
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
    from anato12_studio.__main__ import STYLE
    from anato12_studio.model import Segment
    from anato12_studio.window import MainWindow
    app = QApplication([])
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    w = MainWindow()
    failures = []
    w.fail = failures.append
    w.show()
    try:
        w.import_files([str(recording)])
        wait_until(app, lambda: w.job is None)
        assert not failures, failures
        media = w.current_media()
        media.transcript = [Segment(.1, 1, 'Keep this whole setup with captions'),
                            Segment(1.5, 3, 'Then keep the reply and the reaction')]
        w.refresh_transcript()
        learning = w.learning_controller
        learning.kind.setCurrentIndex(2)
        w.tabs.setCurrentWidget(learning.library_tab)
        learning.index_selected()
        wait_until(app, lambda: w.job is None)
        assert not failures and learning.examples.rowCount() == 2, failures
        learning.examples.selectRow(0)
        app.processEvents()
        assert not learning.frame.pixmap().isNull()
        learning.status.setCurrentText('confirmed')
        learning.note.setText('Preserve the setup before the reply')
        learning.share.setChecked(True)
        learning.correct()
        assert learning.store.model_preferences()['notes'][0]['note'] == 'Preserve the setup before the reply'
        # URL saving does not pretend it was viewed or create examples.
        learning.url.setText('https://www.youtube.com/watch?v=unavailable')
        learning.save_url()
        assert learning.examples.rowCount() == 0 and 'NOT_ANALYZED' in learning.details.toPlainText()
        learning.documents.setCurrentIndex(0)
        w.grab().save(str(output / 'learning-ui.png'))
        w.finder.url.setText(url)
        w.finder_controller.connect_model()
        wait_until(app, lambda: w.job is None)
        assert w.finder.model.currentText() == 'fixture-local'
        assert w.finder.engine.currentIndex() == 1  # Connecting selects Ollama for Analyze.
        w.finder.chat_input.setText('How should I start a video?')
        w.finder.ask_ai.emit()
        wait_until(app, lambda: w.job is None)
        assert 'AI: Local chat reply' in w.finder.chat_output.toPlainText()
        QFileDialog.getExistingDirectory = lambda *a, **k: str(output)
        QDesktopServices.openUrl = lambda *a: True
        before = asdict(w.project)
        was_dirty = w.dirty
        w.tabs.setCurrentWidget(learning.auto_tab)
        learning.ranges.setValue(1)  # This four-second fixture has one complete exchange.
        learning.burn.setChecked(True)
        learning.srt.setChecked(True)
        learning.run_button.click()
        wait_until(app, lambda: w.job is None, seconds=60)
        assert not failures, failures
        assert 'Technical checks passed' in learning.auto_result.text()
        assert len(list(output.glob('Anato12-auto-*'))) == 1
        assert asdict(w.project) == before and w.dirty == was_dirty
        assert learning.store.jobs()[0]['status'] == 'completed'
        w.finder_controller.refresh_all()
        w.finder.table.selectRow(0)
        app.processEvents()
        evidence_text = w.finder.details.toPlainText()
        assert 'Model explanation (unverified)' in evidence_text
        assert 'Model-suggested roles' in evidence_text and 'Setup:' in evidence_text
        assert 'Keep this whole setup with captions' in evidence_text
        w.grab().save(str(output / 'auto-ui.png'))
    finally:
        if w.job:
            w.cancel_job()
            wait_until(app, lambda: w.job is None)
        w.dirty = False
        w.close()
        app.processEvents()
    restarted = MainWindow()
    try:
        learned = restarted.learning_controller.store
        assert len(learned.learning_documents()) == 2
        assert learned.model_preferences()['notes'][0]['note'] == 'Preserve the setup before the reply'
        assert learned.jobs()[0]['status'] == 'completed'
        source = next(d['source'] for d in learned.learning_documents() if d['source'])
        restarted.finder_controller.source = source
        QMessageBox.question = lambda *a, **k: QMessageBox.StandardButton.Yes
        restarted.finder_controller.data_action('source')
        assert len(restarted.learning_controller.docs) == 1  # the unviewed URL remains
        assert restarted.learning_controller.examples.rowCount() == 0
        assert learned.model_preferences()['notes'] == []
    finally:
        restarted.close()
        app.processEvents()


def test_learning_and_auto_ui_keep_editor_and_survive_restart(tmp_path, recording, binaries, endpoint):  # noqa: F811
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_MEDIA_BACKEND='ffmpeg', PYTHONPATH=str(root),
               ANATO12_DATA_DIR=str(tmp_path / 'profile'))
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), str(recording), str(tmp_path), endpoint[0]],
                            cwd=root, env=env, capture_output=True, text=True, timeout=100)
    assert result.returncode == 0, result.stdout + result.stderr


if __name__ == '__main__':
    run_learning(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
