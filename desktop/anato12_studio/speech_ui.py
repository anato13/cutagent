"""Optional dialogue and moment actions; the core editor needs no speech packages."""
from pathlib import Path
from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtWidgets import QFileDialog, QListWidgetItem, QTableWidgetItem

from .captions import read_srt
from .model import timestamp


class SpeechActions:
    def choose_model_folder(self):
        from .speech import model_folder
        folder = QFileDialog.getExistingDirectory(self, "Choose where speech models are stored",
                                                   str(model_folder().parent))
        if folder:
            self.settings.setValue("model_folder", folder)
            self.statusBar().showMessage(f"Speech-model folder: {folder}")

    def refresh_transcript(self):
        media = self.current_media()
        segments = media.transcript if media else []
        with QSignalBlocker(self.transcript.table):
            self.transcript.table.setRowCount(len(segments))
            for i, segment in enumerate(segments):
                for col, value in enumerate((timestamp(segment.start), timestamp(segment.end), segment.text)):
                    item = QTableWidgetItem(value)
                    if col < 2:
                        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    self.transcript.table.setItem(i, col, item)
        self.transcript.status.setText(
            f"{len(segments)} timestamped lines · captions are editable; review recognition before publishing."
            if segments else "Optional: transcribe locally or import an SRT. "
            "First speech use downloads a free model; the recording stays on your computer.")

    def caption_edited(self, item):
        media = self.current_media()
        if media and item.column() == 2 and item.row() < len(media.transcript):
            media.transcript[item.row()].text = item.text()
            self.dirty = True
            self.player.update_caption(self.player.player.position()/1000)
            self.refresh_title()

    def import_captions(self):
        media = self.current_media()
        if not media:
            self.fail("Import a recording first.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import matching captions", "", "SRT captions (*.srt)")
        if path:
            try:
                media.transcript = read_srt(Path(path), media.duration)
            except Exception as error:
                self.fail(str(error))
                return
            self.dirty = True
            self.refresh_transcript()
            self.range_changed()

    def transcribe(self):
        media = self.current_media()
        if not media or not media.has_audio:
            self.fail("Choose a recording with an audio track.")
            return
        try:
            ffmpeg, _ = self.tools()
            from .speech import transcribe
        except Exception as error:
            self.fail(str(error))
            return
        model = self.transcript.model.currentText()
        folder = self.settings.value("model_folder", "", type=str)
        def done(segments):
            media.transcript = segments
            self.dirty = True
            self.refresh_transcript()
            self.range_changed()
            self.tabs.setCurrentIndex(1)
            self.statusBar().showMessage(f"Transcription complete: {len(segments)} lines. Review captions for accuracy.")
        self.start_job(lambda runner, progress: transcribe(media, ffmpeg, model, runner, progress,
                                                          Path(folder) if folder else None),
                       done, "Preparing local transcription")

    def use_line(self):
        media = self.current_media()
        row = self.transcript.table.currentRow()
        if media and 0 <= row < len(media.transcript):
            segment = media.transcript[row]
            self.range.start.setText(timestamp(max(0, segment.start - 2)))
            self.range.end.setText(timestamp(min(media.duration, segment.end + 2)))
            self.range_changed()
            self.player.request_seek(round(max(0, segment.start - 2) * 1000))

    def suggest(self):
        media = self.current_media()
        if not media or not media.transcript:
            self.fail("Transcribe a recording or import an SRT before suggesting moments.")
            return
        from .moments import suggest_moments
        self.moments = suggest_moments(media.transcript, media.duration)
        self.moments_panel.list.clear()
        for moment in self.moments:
            self.moments_panel.list.addItem(QListWidgetItem(
                f"{timestamp(moment.start)} – {timestamp(moment.end)} · {moment.reason}\n{moment.text[:140]}"))
        self.tabs.setCurrentIndex(2)
        if not self.moments:
            self.statusBar().showMessage("No strong cues found. You can still choose any clip manually.")

    def review_moment(self):
        row = self.moments_panel.list.currentRow()
        if 0 <= row < len(self.moments):
            moment = self.moments[row]
            self.range.start.setText(timestamp(moment.start))
            self.range.end.setText(timestamp(moment.end))
            self.range.name.setText(moment.reason)
            self.range_changed()
            self.player.play_range()

    def add_moment(self):
        self.review_moment()
        if self.moments_panel.list.currentRow() >= 0:
            self.add_clip()
