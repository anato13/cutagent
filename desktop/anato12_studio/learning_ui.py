"""Auto Edit and the local learning library in the existing desktop window."""
import copy
from dataclasses import asdict
import json
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from .auto_edit import AutoOptions, run_auto_edit
from .knowledge import RECIPES, compare_transcripts, run_learning_job
from .model import Media, Segment, timestamp
from .panels import table
from .quality import ensure_capabilities
from .store import fingerprint


def button(layout, text, callback):
    widget = QPushButton(text)
    widget.clicked.connect(callback)
    layout.addWidget(widget)
    return widget


def scroll_panel(widget):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    return scroll


class LearningController:
    def __init__(self, window):
        self.w = window
        self.store = window.finder_controller.store
        self.auto = QWidget()
        layout = QVBoxLayout(self.auto)
        notice = QLabel('AUTO EDIT · Experimental\nSelect a recording and an installed local model in AI Clip Finder. '
                        'One run selects complete exchanges, renders YouTube + Shorts, and checks every output. '
                        'Comedy and story quality still need evaluation. No upload to YouTube.')
        notice.setWordWrap(True)
        layout.addWidget(notice)
        form = QFormLayout()
        self.minutes, self.ranges, self.short_seconds = QSpinBox(), QSpinBox(), QSpinBox()
        self.minutes.setRange(1, 120)
        self.minutes.setValue(10)
        self.ranges.setRange(1, 20)
        self.ranges.setValue(5)
        self.short_seconds.setRange(15, 180)
        self.short_seconds.setValue(60)
        form.addRow('Maximum main-video minutes', self.minutes)
        form.addRow('Maximum complete ranges / Shorts', self.ranges)
        form.addRow('Maximum seconds per Short', self.short_seconds)
        layout.addLayout(form)
        self.burn, self.srt = QCheckBox('Burn captions into videos'), QCheckBox('Save SRT captions')
        row = QHBoxLayout()
        row.addWidget(self.burn)
        row.addWidget(self.srt)
        self.run_button = button(row, 'Auto Edit selected recording…', self.start_auto)
        layout.addLayout(row)
        self.auto_result = QLabel('Complete exchanges stay in recording order. Shorts use fit framing; longer ranges are skipped.')
        self.auto_result.setWordWrap(True)
        layout.addWidget(self.auto_result)
        layout.addStretch()
        self.auto_tab = scroll_panel(self.auto)
        window.tabs.addTab(self.auto_tab, 'Auto Edit')

        self.library = QWidget()
        layout = QVBoxLayout(self.library)
        label = QLabel('LEARNING LIBRARY · Local transcripts, frame samples and your corrections. '
                       'Technique mentions are hypotheses. Saved URLs are not analyzed. '
                       'Only tested built-in operations can run; source footage and assets are never copied into edits.')
        label.setWordWrap(True)
        layout.addWidget(label)
        row = QHBoxLayout()
        self.kind = QComboBox()
        for title, value in [('Editing tutorial', 'tutorial'), ('Other creator', 'creator'), ('My finished video', 'own')]:
            self.kind.addItem(title, value)
        row.addWidget(self.kind)
        button(row, 'Import video…', window.import_files)
        button(row, 'Index selected recording', self.index_selected)
        self.url = QLineEdit()
        self.url.setPlaceholderText('YouTube URL (reference only)')
        row.addWidget(self.url)
        button(row, 'Save URL', self.save_url)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.documents, self.original = QComboBox(), QComboBox()
        self.original.setMinimumContentsLength(15)
        self.original.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.documents.setMinimumContentsLength(15)
        self.documents.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.documents.currentIndexChanged.connect(self.refresh_examples)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search dialogue, techniques or corrections')
        self.search.returnPressed.connect(self.refresh_examples)
        row.addWidget(self.documents, 1)
        row.addWidget(self.search, 1)
        button(row, 'Search', self.refresh_examples)
        button(row, 'Delete source knowledge', self.delete_document)
        layout.addLayout(row)
        self.examples = table(['Time', 'Technique', 'Status', 'Dialogue'])
        self.examples.itemSelectionChanged.connect(self.selected)
        layout.addWidget(self.examples)
        row = QHBoxLayout()
        self.frame = QLabel('Frame sample')
        self.frame.setFixedSize(240, 135)
        row.addWidget(self.frame)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        row.addWidget(self.details, 1)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.status = QComboBox()
        self.status.addItems(['observed', 'confirmed', 'rejected'])
        self.note = QLineEdit()
        self.note.setPlaceholderText('Your correction or style preference')
        self.share = QCheckBox('Use this own-video note in Auto Edit')
        row.addWidget(self.status)
        row.addWidget(self.note, 1)
        row.addWidget(self.share)
        button(row, 'Preview example', self.preview_example)
        button(row, 'Save correction', self.correct)
        layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel('Original for comparison:'))
        row.addWidget(self.original, 1)
        button(row, 'Compare with selected finished source', self.compare)
        button(row, 'Test editing operations', self.test_techniques)
        button(row, 'View test history', self.show_tests)
        button(row, 'Source history', self.show_source_history)
        layout.addLayout(row)
        self.rows = []
        self.library_tab = scroll_panel(self.library)
        window.tabs.addTab(self.library_tab, 'Learning library')
        self.refresh()

    def analysis_params(self):
        p, w = self.w.finder, self.w
        return {'query': '', 'transcribe_only': False, 'contextual': True,
                'speech_model': w.transcript.model.currentText(),
                'model_folder': w.settings.value('model_folder', '', type=str),
                'url': p.url.text(), 'model': p.model.currentText()}

    def start_auto(self, checked=False, resume=None):
        w = self.w
        if w.job:
            return
        try:
            media = w.current_media()
            if not media:
                raise ValueError('Import and select the raw recording first.')
            source = self.store.source(media)
            ffmpeg, ffprobe = w.tools()
            if resume:
                if source != resume['source']:
                    raise ValueError('The source changed. Start a new Auto Edit run.')
                params = json.loads(resume['params'])
                identifier = resume['id']
            else:
                params = self.analysis_params()
                if not params['model']:
                    raise ValueError('Open AI Clip Finder, connect to local Ollama, and select a downloaded model first.')
                parent = QFileDialog.getExistingDirectory(w, 'Choose where to save completed YouTube and Shorts videos')
                if not parent:
                    return
                options = AutoOptions(self.minutes.value()*60, self.ranges.value(), self.short_seconds.value(),
                                      self.burn.isChecked(), self.srt.isChecked())
                params.update(kind='auto_edit', auto_options=asdict(options), output_parent=parent)
                identifier = self.store.create_job(source, params)
            snapshot = copy.deepcopy(media)
            w.start_job(lambda runner, progress: run_auto_edit(self.store, source, snapshot, params, identifier,
                        ffmpeg, ffprobe, runner, progress), self.auto_ready, 'Auto editing selected recording')
        except Exception as error:
            w.fail(str(error))

    def auto_ready(self, result):
        self.auto_result.setText(f"Saved {result['main_clips']} main ranges and {result['shorts']} Shorts. "
            f"Skipped Shorts: {result['skipped']}. Technical checks passed.\n{result['directory']}\n"
            'See draft-manifest.json for selections, skips and checks. Editorial quality is experimental.')
        if result.get('history_warning'):
            self.auto_result.setText(self.auto_result.text() + '\n' + result['history_warning'])
        self.w.tabs.setCurrentWidget(self.auto_tab)
        self.w.finder_controller.refresh_all()
        QDesktopServices.openUrl(QUrl.fromLocalFile(result['directory']))

    def index_selected(self, checked=False, resume=None):
        if self.w.job:
            return
        try:
            media = self.w.current_media()
            if not media:
                raise ValueError('Import and select a video in Recordings first.')
            media = copy.deepcopy(media)
            ffmpeg = self.w.tools()[0]
            source = self.store.source(media)
            if resume:
                if source != resume['source']:
                    raise ValueError('The learning source changed. Import it again.')
                params, identifier = json.loads(resume['params']), resume['id']
            else:
                params = {**self.analysis_params(), 'kind': 'learn_video', 'source_kind': self.kind.currentData()}
                identifier = self.store.create_job(source, params)
            def done(result):
                self.refresh(result['document'])
                self.w.tabs.setCurrentWidget(self.library_tab)
                if result.get('history_warning'):
                    self.details.append(result['history_warning'])
            self.w.start_job(lambda runner, progress: run_learning_job(
                self.store, media, params, identifier, ffmpeg, runner, progress), done, 'Indexing learning video')
        except Exception as error:
            self.w.fail(str(error))

    def save_url(self):
        try:
            identifier = self.store.add_learning_url(self.url.text(), self.kind.currentData())
            self.refresh(identifier)
        except Exception as error:
            self.w.fail(str(error))

    def refresh(self, selected=None):
        selected = selected or self.documents.currentData()
        self.docs = self.store.learning_documents()
        self.documents.blockSignals(True)
        self.documents.clear()
        self.documents.addItem('All indexed examples', None)
        self.original.clear()
        for d in self.docs:
            label = f"{d['kind']} · {Path(d['reference']).name} · {d['state']}"
            self.documents.addItem(label, d['id'])
            if d['source']:
                self.original.addItem(label, d['id'])
        self.documents.setCurrentIndex(max(0, self.documents.findData(selected)))
        self.documents.blockSignals(False)
        self.refresh_examples()

    def refresh_examples(self):
        self.rows = self.store.learning_examples(self.search.text(), self.documents.currentData())
        self.examples.setRowCount(len(self.rows))
        for i, row in enumerate(self.rows):
            for j, value in enumerate((timestamp(row['start']), row['technique'], row['status'], row['excerpt'])):
                cell = QTableWidgetItem(value)
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.examples.setItem(i, j, cell)
        self.examples.setCurrentCell(-1, -1)
        self.frame.clear()
        self.note.clear()
        self.share.setChecked(False)
        doc = next((d for d in self.docs if d['id'] == self.documents.currentData()), None)
        self.details.setPlainText((doc['reference'] + '\n' + doc['details']) if doc else
                                 'Select an example to see its source and timestamp. Search displays up to 500 matches.')

    def current(self):
        row = self.examples.currentRow()
        if not 0 <= row < len(self.rows):
            raise ValueError('Select a learning example first.')
        return self.rows[row]

    def selected(self):
        try:
            row = self.current()
        except ValueError:
            return
        self.details.setPlainText(f"{row['reference']}\n{timestamp(row['start'])} – {timestamp(row['end'])}\n"
            f"{row['excerpt']}\n\n{row['explanation']}\nCorrection: {row['note']}")
        self.status.setCurrentText(row['status'])
        self.note.setText(row['note'])
        self.share.setChecked(bool(row['use_note']))
        self.frame.clear()
        path = (self.store.root / row['frame']).resolve()
        if row['frame'] and path.is_relative_to(self.store.root.resolve()) and path.is_file():
            self.frame.setPixmap(QPixmap(str(path)).scaled(240, 135, Qt.AspectRatioMode.KeepAspectRatio))

    def correct(self):
        try:
            self.store.correct_learning_example(self.current()['id'], self.status.currentText(),
                                                 self.note.text(), self.share.isChecked())
            self.refresh_examples()
            self.w.finder_controller.refresh_data()
        except Exception as error:
            self.w.fail(str(error))

    def preview_example(self):
        try:
            row = self.current()
            self.w.finder_controller.media_for(row)
            self.w.range.start.setText(timestamp(row['start']))
            self.w.range.end.setText(timestamp(row['end']))
            self.w.range.name.setText('Learning example')
            self.w.range_changed()
            self.w.player.play_range()
        except Exception as error:
            self.w.fail(str(error))

    def delete_document(self):
        identifier = self.documents.currentData()
        if identifier and QMessageBox.question(self.w, 'Delete learned source?',
            'Delete its examples, corrections and learned preference influence? Original videos stay intact.') == QMessageBox.StandardButton.Yes:
            self.store.delete_learning_document(identifier)
            self.refresh()
            self.w.finder_controller.refresh_data()

    def compare(self):
        if self.w.job:
            return
        try:
            original = next((d for d in self.docs if d['id'] == self.original.currentData()), None)
            finished = next((d for d in self.docs if d['id'] == self.documents.currentData()), None)
            if not original or not finished or finished['kind'] != 'own' or original['id'] == finished['id']:
                raise ValueError('Choose an original source and a different indexed own-video source.')
            def load(doc):
                if not doc['source'] or fingerprint(doc['reference']) != doc['source']:
                    raise ValueError('A comparison source changed or is unavailable. Reimport it.')
                metadata = self.store.get_source(doc['source'])
                segments = self.store.cache_get(f"analysis-transcript:{doc['source']}")
                if segments is None:
                    raise ValueError('Reindex both videos to restore their transcripts before comparison.')
                return Media(doc['id'], metadata['path'], **{k: metadata[k] for k in
                    ('duration', 'width', 'height', 'has_audio')}, transcript=[Segment(**s) for s in segments])
            def operation(runner, progress):
                runner.check()
                matches = compare_transcripts(load(original), load(finished))
                runner.check()
                details = {'original_document': original['id'], 'original_source': original['source'],
                           'finished_source': finished['source'], 'matches': matches,
                           'method': 'Unique exact transcript matches of at least six words; not audiovisual alignment.'}
                with self.store.connect() as db:
                    self.store.learning_event(db, finished['id'], '', 'comparison', details)
                return details
            self.w.start_job(operation, lambda result: self.details.setPlainText(json.dumps(
                result, indent=2, ensure_ascii=False)), 'Comparing original and finished transcripts')
        except Exception as error:
            self.w.fail(str(error))

    def test_techniques(self):
        if self.w.job:
            return
        try:
            ffmpeg, ffprobe = self.w.tools()
            self.w.start_job(lambda runner, progress: ensure_capabilities(self.store, list(RECIPES),
                ffmpeg, ffprobe, runner, progress), lambda _: self.show_tests(), 'Testing built-in editing operations')
        except Exception as error:
            self.w.fail(str(error))

    def show_tests(self):
        rows = self.store.technique_results()
        self.details.setPlainText(json.dumps(rows[:50], indent=2, ensure_ascii=False) if rows else
                                 'NOT_TESTED. Use Test editing operations. Imported examples cannot enable execution.')

    def show_source_history(self):
        with self.store.connect() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM learning_events WHERE document=? '
                'ORDER BY created DESC,id DESC LIMIT 100', (self.documents.currentData(),))]
        self.details.setPlainText(json.dumps(rows, indent=2, ensure_ascii=False))
