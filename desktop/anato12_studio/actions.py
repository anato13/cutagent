"""Window actions for project files, probing, jobs and export."""
import copy
from pathlib import Path

from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QMessageBox

from .jobs import Job
from .model import Project
from .video import ExportPlan, export_video, find_tool, probe


class Actions:
    def tools(self):
        folder = self.settings.value("ffmpeg_folder", "", type=str)
        return find_tool("ffmpeg", folder), find_tool("ffprobe", folder)

    def choose_tools(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose FFmpeg's bin folder")
        if not folder:
            return
        try:
            find_tool("ffmpeg", folder)
            find_tool("ffprobe", folder)
        except Exception as error:
            self.fail(str(error))
            return
        self.settings.setValue("ffmpeg_folder", folder)
        self.statusBar().showMessage("FFmpeg and FFprobe are ready.")

    def import_files(self, paths=None):
        if self.job:
            return
        if not paths or isinstance(paths, bool):
            paths, _ = QFileDialog.getOpenFileNames(
                self, "Import recordings", "", "Videos (*.mp4 *.mkv *.mov *.m4v *.webm);;All files (*)")
        if not paths:
            return
        try:
            _, ffprobe = self.tools()
        except Exception as error:
            self.fail(str(error))
            return
        def operation(runner, progress):
            good, errors = [], []
            for index, path in enumerate(paths):
                runner.check()
                progress(index / len(paths), f"Reading {Path(path).name}")
                try:
                    good.append((path, probe(path, ffprobe)))
                except Exception as error:
                    errors.append(f"{Path(path).name}: {error}")
            return good, errors
        self.start_job(operation, self._imported, "Reading recordings")

    def _imported(self, result):
        good, errors = result
        last = None
        for path, metadata in good:
            last = self.project.add_media(path, **metadata)
        if good:
            self.dirty = True
            self.refresh_library(last.id)
        if errors:
            self.fail("\n\n".join(errors))

    def new_project(self):
        if not self.confirm_discard():
            return
        self.player.player.stop()
        self.player.player.setSource(QUrl())
        self.project = Project()
        self.project_path = None
        self.current_id = None
        self.dirty = False
        self.player.media = None
        self.player.clip = None
        self.loading = True
        self.inspector.profile.setCurrentIndex(0)
        self.inspector.burn.setChecked(False)
        self.inspector.srt.setChecked(False)
        self.inspector.fit.setCurrentIndex(0)
        self.inspector.zoom.setValue(1)
        self.inspector.x.setValue(50)
        self.inspector.y.setValue(50)
        self.range.start.setText("00:00:00.000")
        self.range.end.setText("00:00:00.000")
        self.range.name.clear()
        self.loading = False
        self.player.output_size = (1920, 1080)
        self.player.show_captions = False
        self.moments = []
        self.moments_panel.list.clear()
        self.player.reframe()
        self.refresh_library()
        self.refresh_clips()
        self.refresh_transcript()
        self.refresh_title()

    def open_project(self):
        if not self.confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open project", "", "Anato12 projects (*.anato12.json)")
        if not path:
            return
        try:
            project = Project.load(Path(path))
        except Exception as error:
            self.fail(str(error))
            return
        self.player.player.stop()
        self.player.player.setSource(QUrl())
        self.player.media = None
        self.player.clip = None
        self.moments = []
        self.moments_panel.list.clear()
        self.project, self.project_path, self.dirty = project, Path(path), False
        self.current_id = None
        self.loading = True
        self.inspector.profile.setCurrentText(project.profile)
        self.inspector.burn.setChecked(project.burn_captions)
        self.inspector.srt.setChecked(project.save_srt)
        self.loading = False
        from .model import PROFILES
        self.player.output_size = PROFILES[project.profile]
        self.player.show_captions = project.burn_captions
        self.refresh_library()
        self.refresh_clips()
        self.refresh_title()
        missing = [m.path for m in project.media.values() if not Path(m.path).is_file()]
        if missing:
            self.fail("Some recordings have moved. Select each missing recording and use "
                      "'Relink selected' to choose its new location.\n\n" + "\n".join(missing[:10]))

    def relink_media(self):
        media = self.current_media()
        if not media:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Relink the same recording", "", "Videos (*.mp4 *.mkv *.mov *.m4v *.webm)")
        if not path:
            return
        try:
            _, ffprobe = self.tools()
        except Exception as error:
            self.fail(str(error))
            return
        def done(metadata):
            if abs(metadata["duration"] - media.duration) > 1:
                self.fail("This recording has a different duration. Reimport it as a new source "
                          "instead of relinking existing clip times.")
                return
            media.path = str(Path(path).resolve())
            media.width, media.height = metadata["width"], metadata["height"]
            media.has_audio = metadata["has_audio"]
            self.dirty = True
            self.player.media = None
            self.refresh_library(media.id)
        self.start_job(lambda runner, progress: probe(path, ffprobe), done, "Checking recording")

    def save_project(self, save_as=False):
        path = self.project_path
        if path is None or save_as:
            chosen, _ = QFileDialog.getSaveFileName(
                self, "Save project", "My edit.anato12.json", "Anato12 projects (*.anato12.json)")
            if not chosen:
                return False
            path = Path(chosen)
            if not path.name.endswith(".anato12.json"):
                path = path.with_name(path.name + ".anato12.json")
                if path.exists() and QMessageBox.question(
                        self, "Replace project?", f"Replace {path.name}?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) != QMessageBox.StandardButton.Yes:
                    return False
        if any(path.resolve() == Path(m.path).resolve() for m in self.project.media.values()):
            self.fail("A project cannot replace a recording.")
            return False
        try:
            self.project.save(path)
        except Exception as error:
            self.fail(str(error))
            return False
        self.project_path, self.dirty = path, False
        self.refresh_title()
        self.statusBar().showMessage(f"Project saved: {path}")
        return True

    def confirm_discard(self):
        if not self.dirty:
            return True
        choice = QMessageBox.question(
            self, "Save your edit?", "Save the project before continuing?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if choice == QMessageBox.StandardButton.Save:
            return self.save_project()
        return choice == QMessageBox.StandardButton.Discard

    def export(self):
        try:
            ffmpeg, _ = self.tools()
            clips = [copy.deepcopy(c) for c in self.project.clips if c.enabled]
            if not self.project.clips:
                clips = [self.current_clip()]
            if not clips or clips[0] is None:
                raise ValueError("Import a recording, then choose a range or check clips in the list.")
            for c in clips:
                c.validate(self.project.media[c.media_id])
            if (self.inspector.burn.isChecked() or self.inspector.srt.isChecked()) and not any(
                    self.project.media[c.media_id].transcript for c in clips):
                raise ValueError("Add captions first: transcribe locally or import an SRT in the Dialogue tab.")
        except Exception as error:
            self.fail(str(error))
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Export video", "Anato12 edit.mp4", "MP4 video (*.mp4)")
        if not destination:
            return
        destination = Path(destination)
        if destination.suffix.lower() != ".mp4":
            destination = destination.with_suffix(".mp4")
        sidecar = destination.with_suffix(".srt")
        existing = [p for p in (destination, sidecar if self.inspector.srt.isChecked() else destination) if p.exists()]
        overwrite = False
        if existing:
            overwrite = QMessageBox.question(self, "Replace export?", "Replace the existing export files?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
            if not overwrite:
                return
        plan = ExportPlan(copy.deepcopy(self.project.media), clips, destination,
                          self.inspector.profile.currentText(), self.inspector.burn.isChecked(),
                          self.inspector.srt.isChecked(), overwrite)
        try:
            plan.validate()
        except Exception as error:
            self.fail(str(error))
            return
        self.player.player.pause()
        self.start_job(lambda runner, progress: export_video(plan, ffmpeg, runner, progress),
                       self._exported, "Exporting video")

    def _exported(self, destination):
        self.last_export = Path(destination)
        self.statusBar().showMessage(f"Export complete: {destination}")
        box = QMessageBox(self)
        box.setWindowTitle("Export complete")
        box.setText("Your MP4 is ready.")
        box.setInformativeText(str(destination))
        open_file = box.addButton("Open video", QMessageBox.ButtonRole.AcceptRole)
        open_folder = box.addButton("Open folder", QMessageBox.ButtonRole.ActionRole)
        box.addButton(QMessageBox.StandardButton.Close)
        box.exec()
        if box.clickedButton() == open_file:
            QDesktopServices.openUrl(QUrl.fromLocalFile(destination))
        elif box.clickedButton() == open_folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(destination).parent)))

    def start_job(self, operation, callback, message):
        if self.job:
            return
        self.job_callback = callback
        self.player.seek_timer.stop()
        self.player.play_after_seek = False
        self.player.range_playback = False
        self.player.player.pause()
        self.editor.setEnabled(False)
        self.menuBar().setEnabled(False)
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.job_label.setText(message)
        self.cancel_button.setEnabled(True)
        self.job = Job(operation, self)
        self.job.progress.connect(self._progress)
        self.job.result.connect(self._job_result)
        self.job.failed.connect(self._job_failed)
        self.job.cancelled.connect(self._job_cancelled)
        self.job.finished.connect(self._job_finished)
        self.job.start()

    @Slot(float, str)
    def _progress(self, value, message):
        self.progress.setValue(round(value * 1000))
        self.job_label.setText(message)

    @Slot(object)
    def _job_result(self, result):
        self.progress.setValue(1000)
        self.job_label.setText("Done")
        try:
            self.job_callback(result)
        except Exception as error:
            self.fail(str(error))

    @Slot(str)
    def _job_failed(self, message):
        self.job_label.setText("Operation did not finish")
        self.fail(message)

    @Slot(str)
    def _job_cancelled(self, message):
        self.job_label.setText("Cancelled")
        self.statusBar().showMessage(message)

    @Slot()
    def _job_finished(self):
        old = self.job
        self.job = None
        self.editor.setEnabled(True)
        self.menuBar().setEnabled(True)
        self.cancel_button.setEnabled(False)
        if old:
            old.deleteLater()
        if self.close_pending:
            self.close()

    def cancel_job(self):
        if self.job:
            self.job_label.setText("Cancelling…")
            self.cancel_button.setEnabled(False)
            self.job.cancel()

    def fail(self, message):
        QMessageBox.warning(self, "Anato12 Studio", message)
