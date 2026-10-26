"""The main, deliberately simple desktop editing workflow."""
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QSignalBlocker
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QSplitter, QTabWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)
from .actions import Actions
from .model import Clip, Project, PROFILES, parse_time, timestamp
from .panels import Inspector, MomentsPanel, RangeBar, TranscriptPanel, table
from .player import Player
from .speech_ui import SpeechActions


class MainWindow(Actions, SpeechActions, QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Anato12", "Anato12 Studio")
        self.project = Project(save_srt=False)
        self.project_path = None
        self.current_id = None
        self.job = None
        self.job_callback = None
        self.close_pending = False
        self.dirty = False
        self.loading = False
        self.moments = []
        self.resize(1400, 910)
        self.setMinimumSize(1050, 740)
        self.setAcceptDrops(True)
        shell = QWidget()
        self.setCentralWidget(shell)
        column = QVBoxLayout(shell)
        title = QLabel("ANATO12  STUDIO")
        title.setObjectName("brand")
        subtitle = QLabel("Local video editing  /  Your recordings stay on your computer")
        subtitle.setObjectName("muted")
        column.addWidget(title)
        column.addWidget(subtitle)
        self.editor = QWidget()
        editing = QVBoxLayout(self.editor)
        editing.setContentsMargins(0, 0, 0, 0)
        top = QSplitter(Qt.Orientation.Horizontal)
        library_panel = QWidget()
        library = QVBoxLayout(library_panel)
        library.addWidget(QLabel("RECORDINGS"))
        self.library = QListWidget()
        self.library.currentItemChanged.connect(self._library_selected)
        library.addWidget(self.library)
        b = QPushButton("+ Import recordings")
        b.clicked.connect(self.import_files)
        library.addWidget(b)
        b = QPushButton("Relink selected")
        b.clicked.connect(self.relink_media)
        library.addWidget(b)
        self.player = Player()
        self.player.error.connect(lambda message: self.statusBar().showMessage(
            f"Preview: {message}. Try another file or check START_HERE.md."))
        self.inspector = Inspector()
        self.inspector.changed.connect(self.framing_changed)
        self.inspector.export_requested.connect(self.export)
        top.addWidget(library_panel)
        top.addWidget(self.player)
        top.addWidget(self.inspector)
        top.setSizes([215, 820, 280])
        self.range = RangeBar()
        self.range.mark_in.connect(lambda: self.mark(True))
        self.range.mark_out.connect(lambda: self.mark(False))
        self.range.add.connect(self.add_clip)
        self.range.update.connect(self.update_clip)
        self.range.changed.connect(self.range_changed)
        self.tabs = QTabWidget()
        clips_panel = QWidget()
        clips_layout = QVBoxLayout(clips_panel)
        self.clips = table(["Use", "Clip", "Recording", "In", "Out", "Length"])
        self.clips.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.clips.itemSelectionChanged.connect(self._clip_selected)
        self.clips.itemChanged.connect(self._clip_checked)
        clips_layout.addWidget(self.clips)
        row = QHBoxLayout()
        row.addWidget(QLabel("Export checked clips in this order"))
        row.addStretch()
        for text, callback in (("↑ Move up", lambda: self.move_clip(-1)),
                               ("↓ Move down", lambda: self.move_clip(1)),
                               ("Remove", self.remove_clip)):
            b = QPushButton(text)
            b.clicked.connect(callback)
            row.addWidget(b)
        clips_layout.addLayout(row)
        self.transcript = TranscriptPanel()
        self.transcript.transcribe.connect(self.transcribe)
        self.transcript.import_srt.connect(self.import_captions)
        self.transcript.suggest.connect(self.suggest)
        self.transcript.use_line.connect(self.use_line)
        self.transcript.table.itemChanged.connect(self.caption_edited)
        self.moments_panel = MomentsPanel()
        self.moments_panel.review.connect(self.review_moment)
        self.moments_panel.add.connect(self.add_moment)
        self.tabs.addTab(clips_panel, "Clips")
        self.tabs.addTab(self.transcript, "Dialogue & captions")
        self.tabs.addTab(self.moments_panel, "Potential moments")
        upper = QWidget()
        upper_layout = QVBoxLayout(upper)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        upper_layout.addWidget(top)
        upper_layout.addWidget(self.range)
        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(upper)
        vertical.addWidget(self.tabs)
        vertical.setSizes([540, 230])
        editing.addWidget(vertical)
        column.addWidget(self.editor, 1)
        progress_row = QHBoxLayout()
        self.job_label = QLabel("Import a recording to begin. You can also drag an MP4 into the window.")
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(240)
        self.progress.setRange(0, 1000)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_job)
        progress_row.addWidget(self.job_label, 1)
        progress_row.addWidget(self.progress)
        progress_row.addWidget(self.cancel_button)
        column.addLayout(progress_row)
        self._menus()
        self.statusBar().showMessage("Ready · FFmpeg exports H.264 MP4 at 30 fps")
        self.refresh_title()

    def _menus(self):
        file_menu = self.menuBar().addMenu("File")
        for title, shortcut, callback in (
            ("New project", "Ctrl+N", self.new_project),
            ("Import recordings…", "Ctrl+I", self.import_files),
            ("Open project…", "Ctrl+O", self.open_project),
            ("Save project", "Ctrl+S", self.save_project),
            ("Save project as…", "Ctrl+Shift+S", lambda: self.save_project(True)),
            ("Export MP4…", "Ctrl+E", self.export),
        ):
            action = QAction(title, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            file_menu.addAction(action)
        settings = self.menuBar().addMenu("Settings")
        settings.addAction("Choose FFmpeg folder…", self.choose_tools)
        settings.addAction("Choose speech-model folder…", self.choose_model_folder)
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("Getting started", lambda: QMessageBox.information(
            self, "Getting started",
            "1. Import an MP4.\n2. Move the playhead and mark in/out.\n"
            "3. Choose YouTube or Shorts; adjust framing.\n4. Add the range as a clip.\n"
            "5. Export checked clips to a new MP4.\n\n"
            "Save a project to continue editing later. The project stores cuts, not a copy "
            "of your recording. See START_HERE.md for setup and optional speech tools."))
        self.space_shortcut = QShortcut(QKeySequence("Space"), self.player.view)
        self.space_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.space_shortcut.activated.connect(self.player.toggle)

    def current_media(self):
        return self.project.media.get(self.current_id)

    def current_clip(self):
        media = self.current_media()
        if not media:
            return None
        clip = Clip(media.id, parse_time(self.range.start.text()), parse_time(self.range.end.text()),
                    self.range.name.text().strip() or f"Clip {len(self.project.clips)+1}",
                    zoom=self.inspector.zoom.value(), focus_x=self.inspector.x.value()/100,
                    focus_y=self.inspector.y.value()/100, fit=self.inspector.fit.currentData())
        clip.validate(media)
        return clip

    def refresh_title(self):
        name = self.project_path.name if self.project_path else "Untitled project"
        self.setWindowTitle(f"{'* ' if self.dirty else ''}{name} — Anato12 Studio")

    def refresh_library(self, select_id=None):
        with QSignalBlocker(self.library):
            self.library.clear()
            for media in self.project.media.values():
                missing = " · MISSING" if not Path(media.path).is_file() else ""
                item = QListWidgetItem(f"{media.name}\n{timestamp(media.duration)} · "
                                       f"{media.width}×{media.height}{missing}")
                item.setData(Qt.ItemDataRole.UserRole, media.id)
                item.setToolTip(media.path)
                self.library.addItem(item)
        if self.library.count():
            wanted = select_id or self.current_id
            row = next((i for i in range(self.library.count()) if
                        self.library.item(i).data(Qt.ItemDataRole.UserRole) == wanted), 0)
            self.library.setCurrentRow(row)
        self.refresh_title()

    def _library_selected(self, item, previous=None):
        if not item:
            return
        self.current_id = item.data(Qt.ItemDataRole.UserRole)
        media = self.current_media()
        self.loading = True
        self.range.start.setText(timestamp(0))
        self.range.end.setText(timestamp(media.duration))
        self.range.name.clear()
        self.loading = False
        self.player.load(media)
        self.range_changed()
        self.refresh_transcript()
        self.moments = []
        self.moments_panel.list.clear()

    def framing_changed(self):
        if self.loading:
            return
        self.project.profile = self.inspector.profile.currentText()
        self.project.burn_captions = self.inspector.burn.isChecked()
        self.project.save_srt = self.inspector.srt.isChecked()
        self.dirty = bool(self.project.media) or self.dirty
        self.player.output_size = PROFILES[self.project.profile]
        self.player.show_captions = self.project.burn_captions
        self.range_changed()

    def range_changed(self):
        if self.loading:
            return
        try:
            clip = self.current_clip()
        except ValueError as error:
            self.statusBar().showMessage(str(error))
            return
        self.player.clip = clip
        self.player.reframe()
        self.refresh_title()

    def mark(self, start):
        media = self.current_media()
        if not media:
            return
        value = min(media.duration, self.player.player.position()/1000)
        (self.range.start if start else self.range.end).setText(timestamp(value))
        self.range_changed()

    def add_clip(self):
        try:
            clip = self.current_clip()
            if clip is None:
                raise ValueError("Import a recording first.")
        except ValueError as error:
            self.fail(str(error))
            return
        self.project.clips.append(clip)
        self.dirty = True
        self.refresh_clips(len(self.project.clips)-1)
        self.tabs.setCurrentIndex(0)

    def update_clip(self):
        row = self.clips.currentRow()
        if row < 0:
            self.fail("Select a clip in the list to update it, or use Add clip.")
            return
        try:
            clip = self.current_clip()
            if clip is None:
                return
        except ValueError as error:
            self.fail(str(error))
            return
        clip.enabled = self.project.clips[row].enabled
        self.project.clips[row] = clip
        self.dirty = True
        self.refresh_clips(row)

    def refresh_clips(self, select=-1):
        with QSignalBlocker(self.clips):
            self.clips.setRowCount(len(self.project.clips))
            for i, clip in enumerate(self.project.clips):
                check = QTableWidgetItem()
                check.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable |
                               Qt.ItemFlag.ItemIsUserCheckable)
                check.setCheckState(Qt.CheckState.Checked if clip.enabled else Qt.CheckState.Unchecked)
                self.clips.setItem(i, 0, check)
                values = [clip.name, self.project.media[clip.media_id].name, timestamp(clip.start),
                          timestamp(clip.end), f"{clip.end-clip.start:.2f} s"]
                for col, value in enumerate(values, 1):
                    item = QTableWidgetItem(value)
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    self.clips.setItem(i, col, item)
            if select >= 0:
                self.clips.selectRow(select)
        if select >= 0:
            self._clip_selected()
        self.refresh_title()

    def _clip_checked(self, item):
        if item.column() == 0 and item.row() < len(self.project.clips):
            self.project.clips[item.row()].enabled = item.checkState() == Qt.CheckState.Checked
            self.dirty = True
            self.refresh_title()

    def _clip_selected(self):
        row = self.clips.currentRow()
        if row < 0 or row >= len(self.project.clips):
            return
        clip = self.project.clips[row]
        media = self.project.media[clip.media_id]
        if self.current_id != media.id:
            self.moments = []
            self.moments_panel.list.clear()
        # Do not reset the clip range through the library selection callback.
        self.current_id = media.id
        with QSignalBlocker(self.library):
            for i in range(self.library.count()):
                if self.library.item(i).data(Qt.ItemDataRole.UserRole) == media.id:
                    self.library.setCurrentRow(i)
        self.loading = True
        self.range.start.setText(timestamp(clip.start))
        self.range.end.setText(timestamp(clip.end))
        self.range.name.setText(clip.name)
        self.inspector.zoom.setValue(clip.zoom)
        self.inspector.x.setValue(round(clip.focus_x*100))
        self.inspector.y.setValue(round(clip.focus_y*100))
        self.inspector.fit.setCurrentIndex(0 if clip.fit == "fit" else 1)
        self.loading = False
        self.player.load(media, clip.start)
        self.range_changed()
        self.refresh_transcript()

    def move_clip(self, offset):
        row = self.clips.currentRow()
        other = row + offset
        if row >= 0 and 0 <= other < len(self.project.clips):
            self.project.clips[row], self.project.clips[other] = self.project.clips[other], self.project.clips[row]
            self.dirty = True
            self.refresh_clips(other)

    def remove_clip(self):
        row = self.clips.currentRow()
        if row >= 0:
            del self.project.clips[row]
            self.dirty = True
            self.refresh_clips(min(row, len(self.project.clips)-1))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.job:
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.import_files(paths)
            event.acceptProposedAction()

    def closeEvent(self, event):
        if self.job:
            if QMessageBox.question(self, "Operation running", "Cancel the operation and close when it stops?") == QMessageBox.StandardButton.Yes:
                self.close_pending = True
                self.cancel_job()
            event.ignore()
            return
        if not self.confirm_discard():
            event.ignore()
            return
        self.player.seek_timer.stop()
        self.player.player.stop()
        event.accept()
