"""Local, transactional review/cache/job storage. No recording bytes are stored here."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import uuid

from .knowledge import KnowledgeMixin


def data_folder() -> Path:
    if os.environ.get("ANATO12_DATA_DIR"):
        return Path(os.environ["ANATO12_DATA_DIR"]).expanduser().resolve()
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "Anato12Studio"


def fingerprint(path: str) -> str:
    """Bounded sampling plus stat identity; changing a source invalidates its caches."""
    source = Path(path).resolve()
    before = source.stat()
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        digest.update(stream.read(1024 * 1024))
        stream.seek(max(0, before.st_size - 1024 * 1024))
        digest.update(stream.read(1024 * 1024))
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("The recording changed while it was being inspected. Retry when recording stops.")
    digest.update(f"{source}|{after.st_size}|{after.st_mtime_ns}".encode("utf-8"))
    return digest.hexdigest()


class Store(KnowledgeMixin):
    def __init__(self, root: Path | None = None):
        self.root = (root or data_folder()).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "studio.sqlite3"
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > 3:
                raise ValueError("This app-data database was made by a newer Studio. Keep it and upgrade.")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sources (
                    key TEXT PRIMARY KEY, path TEXT NOT NULL, metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY, source TEXT NOT NULL, kind TEXT NOT NULL,
                    payload TEXT NOT NULL, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS highlights (
                    id TEXT PRIMARY KEY, source TEXT NOT NULL, signature TEXT NOT NULL,
                    start REAL NOT NULL, end REAL NOT NULL, title TEXT NOT NULL,
                    category TEXT NOT NULL, reason TEXT NOT NULL, excerpt TEXT NOT NULL,
                    evidence TEXT NOT NULL, method TEXT NOT NULL, rank REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'unreviewed', edited INTEGER NOT NULL DEFAULT 0,
                    updated REAL NOT NULL, UNIQUE(source, signature));
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY, highlight TEXT NOT NULL, category TEXT NOT NULL,
                    decision TEXT NOT NULL, note TEXT NOT NULL, personalize INTEGER NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'user_confirmed', created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, source TEXT NOT NULL, params TEXT NOT NULL,
                    status TEXT NOT NULL, progress REAL NOT NULL, message TEXT NOT NULL,
                    created REAL NOT NULL, updated REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS cache_source ON cache(source,kind);
                CREATE INDEX IF NOT EXISTS highlights_source ON highlights(source,status);
            """)
            db.execute("BEGIN IMMEDIATE")
            columns = {r["name"] for r in db.execute("PRAGMA table_info(feedback)")}
            if "use_note" not in columns:
                db.execute("ALTER TABLE feedback ADD COLUMN use_note INTEGER NOT NULL DEFAULT 0")
            self.initialize_knowledge(db)
            db.execute("PRAGMA user_version=3")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=20000")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def source(self, media):
        key = fingerprint(media.path)
        meta = {k: getattr(media, k) for k in ("duration", "width", "height", "has_audio")}
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO sources VALUES (?,?,?)",
                       (key, str(Path(media.path).resolve()), json.dumps(meta)))
        return key

    def get_source(self, key):
        with self.connect() as db:
            row = db.execute("SELECT * FROM sources WHERE key=?", (key,)).fetchone()
        if row is None:
            raise ValueError("The source recording is not registered.")
        return {"key": key, "path": row["path"], **json.loads(row["metadata"])}

    def cache_get(self, key):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM cache WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def cache_put(self, key, source, kind, payload):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?,?,?)",
                       (key, source, kind, json.dumps(payload, ensure_ascii=False), time.time()))

    def upsert_highlight(self, source, signature, start, end, title, category, reason,
                         excerpt, evidence, method, rank):
        now = time.time()
        identifier = uuid.uuid4().hex
        with self.connect() as db:
            old = db.execute("SELECT id FROM highlights WHERE source=? AND signature=?",
                             (source, signature)).fetchone()
            if old:
                # Reanalysis never overwrites a reviewed or manually adjusted highlight.
                return old["id"]
            db.execute("""INSERT INTO highlights
                (id,source,signature,start,end,title,category,reason,excerpt,evidence,method,rank,updated)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (identifier, source, signature, start, end, title[:180], category, reason,
                        excerpt, json.dumps(evidence, ensure_ascii=False), method, rank, now))
        return identifier

    def highlights(self, source=None, status="all", order="rank"):
        sql, args = "SELECT h.*,s.path FROM highlights h JOIN sources s ON s.key=h.source WHERE 1=1", []
        if source:
            sql += " AND h.source=?"
            args.append(source)
        if status in ("approved", "rejected", "unreviewed"):
            sql += " AND h.status=?"
            args.append(status)
        sql += {"rank": " ORDER BY h.rank DESC,h.start",
                "time": " ORDER BY h.start", "duration": " ORDER BY h.end-h.start DESC"}.get(order, " ORDER BY h.start")
        with self.connect() as db:
            result = [dict(r) for r in db.execute(sql + " LIMIT 500", args)]
        preferences = self.preferences()
        for item in result:
            item["preference_adjustment"] = preferences.get(item["category"], 0)
        if order == "rank":
            result.sort(key=lambda r: (-(r["rank"] + r["preference_adjustment"]), r["start"]))
        return result

    def approved_for_source(self, source):
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM highlights WHERE source=? AND status='approved' ORDER BY start,end,id", (source,))]

    def rejected_for_source(self, source):
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM highlights WHERE source=? AND status='rejected' ORDER BY start", (source,))]

    def highlight(self, identifier):
        with self.connect() as db:
            row = db.execute("SELECT * FROM highlights WHERE id=?", (identifier,)).fetchone()
        if not row:
            raise ValueError("Highlight no longer exists.")
        return dict(row)

    def adjust(self, identifier, start, end, title, excerpt):
        from .model import number
        item = self.highlight(identifier)
        duration = self.get_source(item["source"])["duration"]
        start, end = number(start, 0, duration, "Start"), number(end, 0, duration, "End")
        if end - start < 1/30:
            raise ValueError("The highlight needs at least one frame.")
        with self.connect() as db:
            db.execute("UPDATE highlights SET start=?,end=?,title=?,excerpt=?,edited=1,updated=? WHERE id=?",
                       (start, end, title[:180], excerpt, time.time(), identifier))

    def review(self, identifier, decision):
        if decision not in ("approved", "rejected", "unreviewed"):
            raise ValueError("Unknown review decision.")
        with self.connect() as db:
            db.execute("UPDATE highlights SET status=?,updated=? WHERE id=?",
                       (decision, time.time(), identifier))

    def add_feedback(self, identifier, note, personalize, use_note=False):
        item = self.highlight(identifier)
        if use_note and item["status"] not in ("approved", "rejected"):
            raise ValueError("Approve or reject the highlight before sharing its note with the local model.")
        with self.connect() as db:
            db.execute("""INSERT INTO feedback
                (id,highlight,category,decision,note,personalize,kind,created,use_note)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                       (uuid.uuid4().hex, identifier, item["category"], item["status"],
                        note.strip()[:4000], bool(personalize), "user_confirmed", time.time(), bool(use_note)))
            if personalize or use_note:
                db.execute("DELETE FROM cache WHERE kind='analysis_window'")

    def update_feedback(self, identifier, note, personalize, use_note):
        with self.connect() as db:
            row = db.execute("SELECT decision,personalize,use_note FROM feedback WHERE id=?", (identifier,)).fetchone()
            if not row:
                raise ValueError("Feedback no longer exists.")
            if use_note and row["decision"] not in ("approved", "rejected"):
                raise ValueError("Only feedback saved after approval or rejection can be shared with the model.")
            db.execute("UPDATE feedback SET note=?,personalize=?,use_note=? WHERE id=?",
                       (note.strip()[:4000], bool(personalize), bool(use_note), identifier))
            if row["personalize"] or row["use_note"] or personalize or use_note:
                db.execute("DELETE FROM cache WHERE kind='analysis_window'")

    def model_preferences(self):
        with self.connect() as db:
            notes = [dict(r) for r in db.execute("""
                SELECT category,decision,substr(note,1,240) AS note,created FROM feedback
                WHERE use_note=1 AND decision IN ('approved','rejected') AND trim(note)<>''
                ORDER BY created DESC,id DESC LIMIT 8""")]
            notes += [dict(r) for r in db.execute("""
                SELECT 'other' AS category,'approved' AS decision,substr(e.note,1,240) AS note,
                    e.updated AS created FROM learning_examples e JOIN learning_documents d ON d.id=e.document
                WHERE e.use_note=1 AND e.status='confirmed' AND d.kind='own'
                    AND trim(e.note)<>'' ORDER BY e.updated DESC,e.id DESC LIMIT 8""")]
        notes.sort(key=lambda r: r['created'], reverse=True)
        return {"category_weights": self.preferences(),
                "notes": [{k: r[k] for k in ('category', 'decision', 'note')} for r in notes[:8]]}

    def feedback(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM feedback ORDER BY created DESC")]

    def delete_feedback(self, identifier):
        with self.connect() as db:
            old = db.execute("SELECT personalize,use_note FROM feedback WHERE id=?", (identifier,)).fetchone()
            db.execute("DELETE FROM feedback WHERE id=?", (identifier,))
            if old and (old["personalize"] or old["use_note"]):
                db.execute("DELETE FROM cache WHERE kind='analysis_window'")

    def preferences(self):
        with self.connect() as db:
            rows = db.execute("""SELECT category,
                SUM(CASE decision WHEN 'approved' THEN 1 WHEN 'rejected' THEN -1 ELSE 0 END) AS weight
                FROM feedback WHERE personalize=1 GROUP BY category""").fetchall()
        return {r["category"]: max(-2, min(2, r["weight"])) for r in rows}

    def create_job(self, source, params):
        identifier, now = uuid.uuid4().hex, time.time()
        with self.connect() as db:
            db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
                       (identifier, source, json.dumps(params), "queued", 0, "Queued", now, now))
        return identifier

    def update_job(self, identifier, status, progress=0, message=""):
        if status not in ("queued", "running", "interrupted", "completed", "failed", "cancelled"):
            raise ValueError("Unknown job status.")
        with self.connect() as db:
            db.execute("UPDATE jobs SET status=?,progress=?,message=?,updated=? WHERE id=?",
                       (status, max(0, min(1, progress)), message[:4000], time.time(), identifier))

    def recover_jobs(self):
        with self.connect() as db:
            db.execute("UPDATE jobs SET status='interrupted',message='App stopped; resume manually' "
                       "WHERE status='running'")

    def jobs(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT 100")]

    def clear_cache(self):
        with self.connect() as db:
            db.execute("DELETE FROM cache")
        # Sources, highlights and feedback are intentionally preserved.

    def delete_source_data(self, source):
        with self.connect() as db:
            for row in db.execute("SELECT id FROM learning_documents WHERE source=?", (source,)).fetchall():
                self.delete_learning_document_rows(db, row['id'])
            db.execute("DELETE FROM feedback WHERE highlight IN (SELECT id FROM highlights WHERE source=?)", (source,))
            db.execute("DELETE FROM cache WHERE kind='analysis_window'")
            for table in ("highlights", "cache", "jobs"):
                db.execute(f"DELETE FROM {table} WHERE source=?", (source,))
            db.execute("DELETE FROM sources WHERE key=?", (source,))
        # Thumbnails are disposable; original media is never touched.
        import re
        import shutil
        if re.fullmatch(r"[0-9a-f]{64}", source):
            shutil.rmtree(self.root / "thumbnails" / source, ignore_errors=True)

    def export_data(self, path):
        if path.suffix.lower() != ".json" or path.resolve() == self.path.resolve():
            raise ValueError("Choose a new .json file for exporting application data.")
        with self.connect() as db:
            if any(Path(r[0]).resolve() == path.resolve() or
                   (path.exists() and Path(r[0]).exists() and path.samefile(r[0]))
                   for r in db.execute("SELECT path FROM sources")):
                raise ValueError("Application data cannot replace a source recording.")
            data = {table: [dict(r) for r in db.execute(f"SELECT * FROM {table}")]
                    for table in ("sources", "highlights", "feedback", "jobs", "learning_documents",
                                  "learning_examples", "learning_events", "technique_tests")}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".tmp",
                                             prefix=".anato12-data-", dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump({"version": 1, **data}, stream, indent=2, ensure_ascii=False)
            temporary.replace(path)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
