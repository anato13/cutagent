"""Small native editing panels."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QPushButton, QSlider, QTableWidget,
    QVBoxLayout, QWidget,
)
from .model import PROFILES


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.verticalHeader().hide()
    widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    widget.horizontalHeader().setStretchLastSection(True)
    return widget


class Inspector(QWidget):
    changed = Signal()
    export_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(245)
        self.profile = QComboBox()
        self.profile.addItems(PROFILES)
        self.fit = QComboBox()
        self.fit.addItem("Fit whole video · add bars", "fit")
        self.fit.addItem("Fill frame · crop edges", "fill")
        self.zoom = QDoubleSpinBox()
        self.zoom.setRange(1, 2)
        self.zoom.setSingleStep(.05)
        self.zoom.setDecimals(2)
        self.zoom.setSuffix(" ×")
        self.x = QSlider(Qt.Orientation.Horizontal)
        self.y = QSlider(Qt.Orientation.Horizontal)
        for slider in (self.x, self.y):
            slider.setRange(0, 100)
            slider.setValue(50)
        self.burn = QCheckBox("Show & burn captions")
        self.srt = QCheckBox("Also save .srt captions")
        self.srt.setChecked(False)
        form = QFormLayout()
        form.addRow("Export format", self.profile)
        form.addRow("Framing", self.fit)
        form.addRow("Zoom", self.zoom)
        form.addRow("Left ↔ right", self.x)
        form.addRow("Top ↔ bottom", self.y)
        column = QVBoxLayout(self)
        heading = QLabel("FRAME & EXPORT")
        heading.setObjectName("section")
        column.addWidget(heading)
        column.addLayout(form)
        note = QLabel("Preview shows the output frame.\nAdd or update a clip to keep its framing.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        column.addWidget(note)
        column.addSpacing(16)
        column.addWidget(self.burn)
        column.addWidget(self.srt)
        note = QLabel("Captions use your transcript or imported SRT. They are optional.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        column.addWidget(note)
        column.addStretch()
        note = QLabel("Checked clips export in list order.\nIf the list is empty, the current range exports.")
        note.setWordWrap(True)
        column.addWidget(note)
        self.export = QPushButton("Export MP4")
        self.export.setObjectName("primary")
        self.export.clicked.connect(self.export_requested)
        column.addWidget(self.export)
        for widget in (self.profile, self.fit):
            widget.currentIndexChanged.connect(self.changed)
        self.zoom.valueChanged.connect(self.changed)
        self.x.valueChanged.connect(self.changed)
        self.y.valueChanged.connect(self.changed)
        self.burn.toggled.connect(self.changed)
        self.srt.toggled.connect(self.changed)


class RangeBar(QWidget):
    mark_in = Signal()
    mark_out = Signal()
    add = Signal()
    update = Signal()
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.start = QLineEdit("00:00:00.000")
        self.end = QLineEdit("00:00:00.000")
        self.name = QLineEdit()
        self.name.setPlaceholderText("Clip name (optional)")
        self.start.setToolTip("Seconds or HH:MM:SS.mmm")
        self.end.setToolTip("Seconds or HH:MM:SS.mmm")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        b = QPushButton("[ Mark in")
        b.clicked.connect(self.mark_in)
        row.addWidget(b)
        row.addWidget(self.start)
        b = QPushButton("Mark out ]")
        b.clicked.connect(self.mark_out)
        row.addWidget(b)
        row.addWidget(self.end)
        row.addWidget(self.name)
        b = QPushButton("+ Add clip")
        b.clicked.connect(self.add)
        row.addWidget(b)
        b = QPushButton("Update selected")
        b.clicked.connect(self.update)
        row.addWidget(b)
        self.start.editingFinished.connect(self.changed)
        self.end.editingFinished.connect(self.changed)


class TranscriptPanel(QWidget):
    transcribe = Signal()
    import_srt = Signal()
    suggest = Signal()
    use_line = Signal()

    def __init__(self):
        super().__init__()
        self.table = table(["In", "Out", "Dialogue · double-click text to edit"])
        self.model = QComboBox()
        self.model.addItems(["tiny.en", "base.en", "small.en"])
        self.model.setCurrentText("base.en")
        row = QHBoxLayout()
        row.addWidget(QLabel("English speech model"))
        row.addWidget(self.model)
        for text, signal in (("Transcribe locally", self.transcribe), ("Import SRT", self.import_srt),
                             ("Suggest moments", self.suggest), ("Use selected line", self.use_line)):
            b = QPushButton(text)
            b.clicked.connect(signal)
            row.addWidget(b)
        column = QVBoxLayout(self)
        column.addLayout(row)
        column.addWidget(self.table)
        self.status = QLabel("Optional: install speech tools with INSTALL_SPEECH.bat. "
                             "You can also import an existing .srt file.")
        self.status.setWordWrap(True)
        self.status.setObjectName("muted")
        column.addWidget(self.status)


class MomentsPanel(QWidget):
    review = Signal()
    add = Signal()

    def __init__(self):
        super().__init__()
        self.list = QListWidget()
        column = QVBoxLayout(self)
        text = QLabel("Potential moments, not guaranteed jokes. Review each suggestion before adding it.")
        text.setWordWrap(True)
        column.addWidget(text)
        column.addWidget(self.list)
        row = QHBoxLayout()
        for text, signal in (("Preview selected", self.review), ("Add selected to clips", self.add)):
            b = QPushButton(text)
            b.clicked.connect(signal)
            row.addWidget(b)
        column.addLayout(row)
