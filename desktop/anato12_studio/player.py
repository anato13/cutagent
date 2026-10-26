"""Native local-video player with the same framing geometry as the exporter."""
from PySide6.QtCore import Qt, QUrl, QRectF, QSizeF, QSignalBlocker, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import (
    QGraphicsScene, QGraphicsTextItem, QGraphicsView, QGraphicsDropShadowEffect,
    QGraphicsRectItem, QGraphicsItem,
    QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)

from .model import Clip, Media, caption_style, timestamp
from .video import layout


class Canvas(QGraphicsView):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class Player(QWidget):
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.media: Media | None = None
        self.clip: Clip | None = None
        self.output_size = (1920, 1080)
        self.show_captions = False
        self.range_playback = False
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QColor("#0b0e14"))
        self.frame = QGraphicsRectItem()
        self.frame.setPen(QPen(Qt.PenStyle.NoPen))
        self.frame.setBrush(QColor("#0b0e14"))
        self.frame.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)
        self.scene.addItem(self.frame)
        self.video = QGraphicsVideoItem()
        self.video.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
        self.video.setParentItem(self.frame)
        self.caption = QGraphicsTextItem()
        self.caption.setDefaultTextColor(QColor("white"))
        self.caption.setZValue(2)
        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor("black"))
        shadow.setOffset(1, 2)
        shadow.setBlurRadius(4)
        self.caption.setGraphicsEffect(shadow)
        self.caption.setParentItem(self.frame)
        self.view = Canvas(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setMinimumSize(360, 230)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(.7)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.seek_timer = QTimer(self)
        self.seek_timer.setSingleShot(True)
        self.seek_timer.timeout.connect(self._apply_seek)
        self.requested_position = 0
        self.play_after_seek = False
        self.awaiting_load = False
        self.player.positionChanged.connect(self._position)
        self.player.errorOccurred.connect(lambda *_: self.error.emit(self.player.errorString()))
        self.player.playbackStateChanged.connect(self._state)
        self.player.mediaStatusChanged.connect(self._loaded)
        self.video.nativeSizeChanged.connect(lambda _: self.reframe())
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 0)
        self.seek.valueChanged.connect(self._seek)
        self.play = QPushButton("▶ Play / pause")
        self.play.clicked.connect(self.toggle)
        self.range_button = QPushButton("▶ Play range")
        self.range_button.clicked.connect(self.play_range)
        self.clock = QLabel("00:00:00.000 / 00:00:00.000")
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(70)
        self.volume.setMaximumWidth(90)
        self.volume.valueChanged.connect(lambda v: self.audio.setVolume(v / 100))
        row = QHBoxLayout()
        for widget in (self.play, self.range_button, self.clock, QLabel("Volume"), self.volume):
            row.addWidget(widget)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(self.view, 1)
        column.addWidget(self.seek)
        column.addLayout(row)
        self.reframe()

    def load(self, media: Media, position=0.0):
        self.range_playback = False
        changed = self.media is None or self.media.id != media.id
        self.media = media
        self.pending_position = position
        self.seek.setRange(0, round(media.duration * 1000))
        if changed:
            self.seek_timer.stop()
            self.awaiting_load = True
            self.player.setSource(QUrl.fromLocalFile(media.path))
        else:
            self.request_seek(round(position * 1000))
        self.reframe()

    def _loaded(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia and self.awaiting_load:
            self.awaiting_load = False
            self.request_seek(round(getattr(self, "pending_position", 0) * 1000))

    def request_seek(self, value, play=False):
        self.requested_position = value
        self.play_after_seek = play
        # Coalesce scrubs and clip updates before asking the multimedia backend.
        # Redundant synchronous seeks can deadlock some FFmpeg/Qt backends.
        self.seek_timer.start(35)

    def _apply_seek(self):
        if abs(self.player.position() - self.requested_position) > 5:
            self.player.setPosition(self.requested_position)
        if self.play_after_seek:
            self.play_after_seek = False
            self.player.play()

    def _seek(self, value):
        self.range_playback = False
        self.request_seek(value)

    def _state(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play.setText("❚❚ Pause" if playing else "▶ Play / pause")

    def toggle(self):
        if not self.media:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.range_playback = False
            self.player.play()

    def play_range(self):
        if self.clip and self.media:
            self.range_playback = True
            self.request_seek(round(self.clip.start * 1000), play=True)

    def _position(self, value):
        if not self.seek.isSliderDown():
            with QSignalBlocker(self.seek):
                self.seek.setValue(value)
        duration = self.media.duration if self.media else 0
        self.clock.setText(f"{timestamp(value/1000)} / {timestamp(duration)}")
        if self.range_playback and self.clip and value >= round(self.clip.end * 1000):
            self.range_playback = False
            self.player.pause()
            self.request_seek(max(0, round(self.clip.end * 1000) - 33))
        self.update_caption(value / 1000)

    def reframe(self):
        width, height = self.output_size
        self.scene.setSceneRect(QRectF(0, 0, width, height))
        self.frame.setRect(0, 0, width, height)
        if self.media and self.clip:
            x, y, w, h = layout(self.media.width, self.media.height, width, height, self.clip)
            self.video.setSize(QSizeF(w, h))
            self.video.setPos(x, y)
        else:
            self.video.setSize(QSizeF(width, height))
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        size, _ = caption_style(width, height)
        font = QFont("Arial")
        font.setBold(True)
        font.setPixelSize(size)
        self.caption.setFont(font)
        self.caption.setTextWidth(width * .86)
        self.update_caption(self.player.position() / 1000)

    def update_caption(self, position):
        text = ""
        if self.media and self.show_captions:
            text = "\n".join(s.text for s in self.media.transcript if s.start <= position < s.end)
        self.caption.setPlainText(text)
        option = self.caption.document().defaultTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.caption.document().setDefaultTextOption(option)
        width, height = self.output_size
        _, margin = caption_style(width, height)
        self.caption.setPos(width * .07, height - margin - self.caption.boundingRect().height())
