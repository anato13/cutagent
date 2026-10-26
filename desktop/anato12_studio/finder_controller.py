"""Connect persistent analysis/review to the existing editor without replacing its timeline."""
import copy
import json
from pathlib import Path

from PySide6.QtCore import Qt, QSignalBlocker, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem

from .finder_jobs import make_thumbnail, run_pipeline, thumbnail_path
from .drafts import DraftOptions, create_bundle
from .exchange import describe_exchange
from .finder_ui import DraftDialog
from .local_model import LocalModel
from .model import Clip, Segment, timestamp
from .store import Store, fingerprint
from .video import ExportPlan, export_video


class FinderController:
    def __init__(self, window):
        self.w = window
        self.store = Store()
        self.store.recover_jobs()
        self.source = None
        self.ids_filter = None
        self.items = []
        self.job_rows, self.feedback_rows = [], []
        p = window.finder
        p.analyze.connect(self.start)
        p.search.connect(lambda: self.start(query=p.query.text()))
        p.connect_model.connect(self.connect_model)
        p.refresh.connect(self.refresh_all)
        p.selected.connect(self.selected)
        p.action.connect(self.action)
        p.drafts.connect(self.create_drafts)
        p.status.currentIndexChanged.connect(self.refresh)
        p.order.currentIndexChanged.connect(self.refresh)
        window.data_panel.action.connect(self.data_action)
        window.data_panel.feedback_selected.connect(self.feedback_selected)
        self.refresh_data()

    def select_source(self, media):
        self.ids_filter = None
        try:
            self.source = self.store.source(media) if media and Path(media.path).is_file() else None
        except Exception as error:
            self.source = None
            self.w.fail(f"Clip finder could not inspect this recording: {error}")
        self.w.finder.table.clearSelection()
        self.w.finder.table.setCurrentCell(-1, -1)
        self.refresh()

    def refresh_all(self):
        self.ids_filter = None
        self.refresh()

    def refresh(self):
        p = self.w.finder
        row = p.table.currentRow()
        previous_id = self.items[row]["id"] if 0 <= row < len(self.items) else None
        status = p.status.currentText() if p.status.currentIndex() else "all"
        order = ("rank", "time", "duration")[p.order.currentIndex()]
        self.items = self.store.highlights(self.source, status, order) if self.source else []
        if self.ids_filter is not None:
            self.items = [r for r in self.items if r["id"] in self.ids_filter]
        with QSignalBlocker(p.table):
            p.table.setRowCount(len(self.items))
            for i, item in enumerate(self.items):
                values = (item["title"], timestamp(item["start"]), timestamp(item["end"]),
                          f'{item["end"]-item["start"]:.1f}s', item["category"], item["status"], item["method"])
                for j, value in enumerate(values):
                    cell = QTableWidgetItem(str(value))
                    cell.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    p.table.setItem(i, j, cell)
        p.details.setPlainText("Select a highlight. Review ranks are not confidence percentages.")
        p.thumbnail.clear()
        selected_row = next((i for i, item in enumerate(self.items) if item["id"] == previous_id), -1)
        p.table.setCurrentCell(-1, -1)
        if selected_row >= 0:
            p.table.selectRow(selected_row)

    def current(self):
        row = self.w.finder.table.currentRow()
        if not 0 <= row < len(self.items):
            raise ValueError("Select a highlight first.")
        return self.store.highlight(self.items[row]["id"])

    def selected(self):
        try:
            item = self.current()
        except ValueError:
            return
        p = self.w.finder
        p.start.setValue(item["start"])
        p.end.setValue(item["end"])
        p.title.setText(item["title"])
        evidence = json.loads(item["evidence"])
        explanation_label = 'Model explanation (unverified)' if item['method'] == 'local model order' else 'Reason'
        text = (f'Recording: {Path(self.store.get_source(item["source"])["path"]).name}\n'
                f'Method: {item["method"]} (uncalibrated review order)\n'
                f'{explanation_label}: {item["reason"]}\n')
        text += (f'Category preference adjustment: {self.store.preferences().get(item["category"], 0)}\n\n'
                + (describe_exchange(item) + '\n\n' if item['method'] == 'local model order' else '') +
                f'Selected transcript:\n{item["excerpt"]}\n\nSource evidence:\n')
        text += "\n".join(f'{timestamp(r["start"])} · {r["text"]}' for r in evidence)
        p.details.setPlainText(text)
        path = thumbnail_path(self.store, item)
        if path.exists():
            p.thumbnail.setPixmap(QPixmap(str(path)).scaled(300, 160, Qt.AspectRatioMode.KeepAspectRatio,
                                                           Qt.TransformationMode.SmoothTransformation))
        else:
            p.thumbnail.setText("Preview thumbnail will be restored on Preview.")

    def connect_model(self):
        w, p = self.w, self.w.finder
        def done(models):
            p.model.clear()
            p.model.addItems(models)
            p.notice.setText(f"Local endpoint connected · {len(models)} downloaded model names available. "
                             "Known cloud-backed models are excluded. Nothing has been analyzed yet.")
        try:
            client = LocalModel(p.url.text())
            w.start_job(lambda runner, progress: client.models(runner), done, "Connecting to local Ollama")
        except Exception as error:
            w.fail(str(error))

    def start(self, query="", transcribe_only=False, resume=None):
        w, p = self.w, self.w.finder
        media = w.current_media()
        if not media or w.job:
            if not media:
                w.fail("Import or select a recording first.")
            return
        try:
            ffmpeg, _ = w.tools()
            source = self.store.source(media)
            params = {"query": str(query).strip(), "transcribe_only": transcribe_only,
                      "speech_model": w.transcript.model.currentText(),
                      "model_folder": w.settings.value("model_folder", "", type=str),
                      "contextual": p.engine.currentIndex() == 1,
                      "url": p.url.text(), "model": p.model.currentText()}
            if resume:
                params = json.loads(resume["params"])
                if source != resume["source"]:
                    raise ValueError("The source changed. Start a new job instead of resuming.")
            if params["contextual"] and not params["transcribe_only"]:
                LocalModel(params["url"], params["model"])
                if not params["model"]:
                    raise ValueError("Connect to Ollama and choose an installed local model, or select Context cues.")
            identifier = resume["id"] if resume else self.store.create_job(source, params)
            snapshot = copy.deepcopy(media)
            def done(result):
                media.transcript = result["segments"]
                w.dirty = True
                w.refresh_transcript()
                w.range_changed()
                self.source = result["source"]
                self.ids_filter = set(result["ids"]) if not params["transcribe_only"] else None
                self.refresh()
                self.refresh_data()
                p.notice.setText(
                    f'{len(result["ids"])} candidates · ' +
                    ("local model output requires review; humor quality is unverified."
                     if params["contextual"] else
                     "context cues/literal search only; these are not validated humor judgments."))
                w.tabs.setCurrentWidget(w.transcript if params["transcribe_only"] else p)
            w.start_job(lambda runner, progress: run_pipeline(
                self.store, source, snapshot, params, identifier, ffmpeg, runner, progress), done, "Analyzing recording")
        except Exception as error:
            w.fail(str(error))

    def media_for(self, item):
        source = self.store.get_source(item["source"])
        if fingerprint(source["path"]) != item["source"]:
            raise ValueError("This recording changed; reimport and analyze it before using old highlights.")
        media = self.w.project.add_media(source["path"], **{k: source[k] for k in
                                        ("duration", "width", "height", "has_audio")})
        if not media.transcript:
            saved = self.store.cache_get(f'analysis-transcript:{item["source"]}')
            if saved is not None:
                media.transcript = [Segment(**s) for s in saved]
        if self.w.current_id != media.id:
            self.w.refresh_library(media.id)
        else:
            self.w.refresh_transcript()
        return media

    def action(self, action):
        try:
            item = self.current()
            w, p = self.w, self.w.finder
            if action in ("approve", "reject"):
                self.store.review(item["id"], "approved" if action == "approve" else "rejected")
                self.refresh()
                self.refresh_data()
                return
            if action == "feedback":
                self.store.add_feedback(item["id"], p.feedback.text(), p.personalize.isChecked(),
                                        p.model_note.isChecked())
                p.feedback.clear()
                p.personalize.setChecked(False)
                p.model_note.setChecked(False)
                self.refresh_data()
                self.refresh()
                p.notice.setText("Feedback saved. Category ranking and sharing note text each require their own opt-in.")
                return
            if action == "save":
                cached = self.store.cache_get(f'analysis-transcript:{item["source"]}') or []
                excerpt = "\n".join(s["text"] for s in cached if s["end"] > p.start.value()
                                    and s["start"] < p.end.value())
                self.store.adjust(item["id"], p.start.value(), p.end.value(), p.title.text(), excerpt)
                self.refresh()
                return
            media = self.media_for(item)
            w.range.start.setText(timestamp(item["start"]))
            w.range.end.setText(timestamp(item["end"]))
            w.range.name.setText(item["title"])
            w.range_changed()
            if action == "preview":
                ffmpeg, _ = w.tools()
                if not thumbnail_path(self.store, item).exists():
                    def restored(path):
                        p.thumbnail.setPixmap(QPixmap(path).scaled(300, 160, Qt.AspectRatioMode.KeepAspectRatio))
                        w.player.play_range()
                    w.start_job(lambda runner, progress: str(make_thumbnail(self.store, item, ffmpeg, runner)),
                                restored, "Restoring thumbnail")
                else:
                    w.player.play_range()
            elif action in ("main", "shorts"):
                w.inspector.profile.setCurrentIndex(0 if action == "main" else 1)
                if action == "shorts":
                    w.inspector.fit.setCurrentIndex(1)
                w.add_clip()
                w.statusBar().showMessage("Added to current editor; export format switched. "
                                          "Use a separate saved project for a separate Shorts timeline.")
            elif action == "export":
                self.export_item(item, media)
        except Exception as error:
            self.w.fail(str(error))

    def export_item(self, item, media):
        w = self.w
        if (w.inspector.burn.isChecked() or w.inspector.srt.isChecked()) and not media.transcript:
            raise ValueError("Add captions first: transcribe locally or import an SRT in the Dialogue tab.")
        destination, _ = QFileDialog.getSaveFileName(w, "Export this highlight",
                                                     "Anato12 highlight.mp4", "MP4 (*.mp4)")
        if not destination:
            return
        path = Path(destination).with_suffix(".mp4")
        overwrite = False
        if path.exists() or (w.inspector.srt.isChecked() and path.with_suffix(".srt").exists()):
            overwrite = QMessageBox.question(w, "Replace highlight export?", "Replace existing output files?") == QMessageBox.StandardButton.Yes
            if not overwrite:
                return
        clip = Clip(media.id, item["start"], item["end"], item["title"],
                    zoom=w.inspector.zoom.value(), focus_x=w.inspector.x.value()/100,
                    focus_y=w.inspector.y.value()/100, fit=w.inspector.fit.currentData())
        plan = ExportPlan(copy.deepcopy(w.project.media), [clip], path,
                          w.inspector.profile.currentText(), w.inspector.burn.isChecked(),
                          w.inspector.srt.isChecked(), overwrite)
        plan.validate()
        ffmpeg, _ = w.tools()
        w.start_job(lambda runner, progress: export_video(plan, ffmpeg, runner, progress),
                    w._exported, "Exporting selected highlight only")

    def create_drafts(self):
        w = self.w
        if w.job:
            return
        try:
            media = w.current_media()
            if not media or not self.source:
                raise ValueError("Select a recording with approved highlights first.")
            approved = self.store.approved_for_source(self.source)
            if not approved:
                raise ValueError("Approve at least one highlight for this recording first.")
            dialog = DraftDialog(len(approved), w)
            if dialog.exec() != DraftDialog.DialogCode.Accepted:
                return
            parent = QFileDialog.getExistingDirectory(w, "Choose folder for a new draft bundle")
            if not parent:
                return
            snapshot = copy.deepcopy(media)
            if not snapshot.transcript:
                saved = self.store.cache_get(f"analysis-transcript:{self.source}") or []
                snapshot.transcript = [Segment(**s) for s in saved]
            options = DraftOptions(dialog.limit.value(), dialog.fit.currentData(),
                                   dialog.burn.isChecked(), dialog.srt.isChecked(), dialog.render.isChecked())
            ffmpeg = w.tools()[0] if options.render else ""
            source = self.source
            w.start_job(lambda runner, progress: create_bundle(snapshot, source, approved,
                parent, options, ffmpeg, runner, progress), self._drafts_ready, "Creating approved drafts")
        except Exception as error:
            w.fail(str(error))

    def _drafts_ready(self, result):
        self.w.statusBar().showMessage(f"Drafts ready: {result['directory']}")
        box = QMessageBox(self.w)
        box.setWindowTitle("Drafts ready")
        box.setText(
            f"Created {result['main_clips']} main-video ranges and {result['shorts']} Shorts projects.\n"
            f"Skipped Shorts: {result['skipped']} (see draft-manifest.json).\n\n{result['directory']}\n\n"
            "Open a draft using File → Open project. Review its framing before publishing.")
        open_folder = box.addButton("Open folder", QMessageBox.ButtonRole.AcceptRole)
        box.addButton(QMessageBox.StandardButton.Close)
        box.exec()
        if box.clickedButton() == open_folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(result["directory"]))

    def refresh_data(self):
        p = self.w.data_panel
        self.job_rows = self.store.jobs()
        self.feedback_rows = self.store.feedback()
        for table, rows, fields in (
            (p.jobs, self.job_rows, ("id", "source", "status", "progress", "message")),
            (p.feedback, self.feedback_rows, ("category", "decision", "personalize", "use_note", "note"))):
            table.setRowCount(len(rows))
            for i, item in enumerate(rows):
                for j, field in enumerate(fields):
                    value = item[field]
                    if field == "source":
                        value = Path(self.store.get_source(value)["path"]).name
                    if field == "progress":
                        value = f"{value:.0%}"
                    if field in ("personalize", "use_note"):
                        value = "Yes" if value else "No"
                    cell = QTableWidgetItem(str(value))
                    cell.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    table.setItem(i, j, cell)
        p.feedback.clearSelection()
        p.feedback.setCurrentCell(-1, -1)
        p.note.clear()
        p.use_category.setChecked(False)
        p.use_note.setChecked(False)
        context = self.store.model_preferences()
        lines = ["Category ranking: " + (", ".join(f"{k}: {v:+d}" for k, v in
                 sorted(context["category_weights"].items())) or "none"), "", "Shared notes:"]
        lines += [f'{n["decision"]} · {n["category"]}: {n["note"]}' for n in context["notes"]]
        p.personalization.setPlainText("\n".join(lines))

    def feedback_selected(self):
        p = self.w.data_panel
        row = p.feedback.currentRow()
        if 0 <= row < len(self.feedback_rows):
            item = self.feedback_rows[row]
            p.note.setPlainText(item["note"])
            p.use_category.setChecked(bool(item["personalize"]))
            p.use_note.setChecked(bool(item["use_note"]))

    def data_action(self, action):
        w, p = self.w, self.w.data_panel
        try:
            if action == "resume":
                row = p.jobs.currentRow()
                if row < 0:
                    raise ValueError("Select a job to resume.")
                job = self.job_rows[row]
                if job["status"] == "completed":
                    raise ValueError("This job is complete. Start a new analysis to rerun it.")
                source = self.store.get_source(job["source"])
                media = w.project.add_media(source["path"], **{k: source[k] for k in
                                            ("duration", "width", "height", "has_audio")})
                w.refresh_library(media.id)
                if json.loads(job['params']).get('kind') == 'auto_edit':
                    self.w.learning_controller.start_auto(resume=job)
                elif json.loads(job['params']).get('kind') == 'learn_video':
                    self.w.learning_controller.index_selected(resume=job)
                else:
                    self.start(resume=job)
            elif action == "cache":
                if QMessageBox.question(w, "Clear processing caches?",
                    "Delete cached transcripts and model responses? Reviewed highlights and feedback stay. "
                    "Original recordings, models and saved projects stay.") == QMessageBox.StandardButton.Yes:
                    self.store.clear_cache()
            elif action == "source":
                if not self.source:
                    raise ValueError("Select a recording first.")
                if QMessageBox.question(w, "Delete this recording's app data?",
                    "Delete its cached transcripts, highlights, feedback and job history? "
                    "The recording, saved project files and exported files will not be deleted.") == QMessageBox.StandardButton.Yes:
                    self.store.delete_source_data(self.source)
                    if w.current_media():
                        w.current_media().transcript = []
                        w.dirty = True
                    self.source = None
                    self.refresh()
                    w.refresh_transcript()
            elif action == "update_feedback":
                row = p.feedback.currentRow()
                if not 0 <= row < len(self.feedback_rows):
                    raise ValueError("Select saved feedback to edit first.")
                self.store.update_feedback(self.feedback_rows[row]["id"], p.note.toPlainText(),
                                           p.use_category.isChecked(), p.use_note.isChecked())
                self.refresh()
            elif action == "delete_feedback":
                row = p.feedback.currentRow()
                if row >= 0:
                    self.store.delete_feedback(self.feedback_rows[row]["id"])
                    self.refresh()
            elif action == "export_data":
                path, _ = QFileDialog.getSaveFileName(w, "Export local application data", "Anato12-data.json", "JSON (*.json)")
                if path:
                    self.store.export_data(Path(path).with_suffix(".json"))
            self.refresh_data()
            if action == "source" and hasattr(w, "learning_controller"):
                w.learning_controller.refresh()
        except Exception as error:
            w.fail(str(error))
