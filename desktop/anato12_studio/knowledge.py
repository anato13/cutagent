"""Persistent source evidence and corrections, separate from executable capabilities.

Only the fixed recipes below can be executed. Imported text never becomes code.
Transcript cues are hypotheses, not proof of a visual technique or humor quality.
"""
from dataclasses import asdict
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import uuid

from .model import Segment


RECIPES = {
    "trim_join": "Keep complete ranges and join them in recording order.",
    "portrait_fit": "Fit the whole source in a portrait canvas to preserve visible context.",
    "captions": "Display timestamped dialogue to help viewers follow speech.",
    "zoom": "Enlarge the image around a fixed focus point to emphasize a subject.",
}
TECHNIQUE_CUES = {
    "trim_join": r"\b(jump cuts?|trim(?:ming)?|cut out|cutting out)\b",
    "portrait_fit": r"\b(portrait|vertical video|9:16)\b",
    "captions": r"\b(captions?|subtitles?)\b",
    "zoom": r"\b(zoom(?:ing)?|punch in)\b",
}


class KnowledgeMixin:
    @staticmethod
    def initialize_knowledge(db):
        # Each statement stays inside Store's migration transaction.
        for statement in (
            """CREATE TABLE IF NOT EXISTS learning_documents (
                id TEXT PRIMARY KEY, source TEXT, kind TEXT NOT NULL, reference TEXT NOT NULL,
                state TEXT NOT NULL, details TEXT NOT NULL, updated REAL NOT NULL)""",
            """CREATE UNIQUE INDEX IF NOT EXISTS learning_local_source
                ON learning_documents(source,kind) WHERE source IS NOT NULL""",
            """CREATE TABLE IF NOT EXISTS learning_examples (
                id TEXT PRIMARY KEY, document TEXT NOT NULL, start REAL NOT NULL, end REAL NOT NULL,
                excerpt TEXT NOT NULL, technique TEXT NOT NULL, explanation TEXT NOT NULL,
                status TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', use_note INTEGER NOT NULL DEFAULT 0,
                frame TEXT NOT NULL DEFAULT '', updated REAL NOT NULL)""",
            "CREATE INDEX IF NOT EXISTS learning_example_document ON learning_examples(document,start)",
            """CREATE TABLE IF NOT EXISTS learning_events (
                id TEXT PRIMARY KEY, document TEXT NOT NULL, example TEXT NOT NULL,
                action TEXT NOT NULL, details TEXT NOT NULL, created REAL NOT NULL)""",
            """CREATE TABLE IF NOT EXISTS technique_tests (
                id TEXT PRIMARY KEY, recipe TEXT NOT NULL, engine TEXT NOT NULL,
                passed INTEGER NOT NULL, report TEXT NOT NULL, created REAL NOT NULL)""",
        ):
            db.execute(statement)

    def add_learning_url(self, url, kind):
        url = url.strip()
        parsed = urlsplit(url)
        if (kind not in {'tutorial', 'creator', 'own'} or parsed.scheme != 'https'
                or parsed.hostname not in {'youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com'}
                or parsed.username or parsed.password or parsed.port not in (None, 443) or len(url) > 2000):
            raise ValueError('Use an HTTPS YouTube URL and choose a source type.')
        with self.connect() as db:
            old = db.execute('SELECT id FROM learning_documents WHERE reference=? AND kind=? AND source IS NULL',
                             (url, kind)).fetchone()
            if old:
                return old['id']
            identifier = uuid.uuid4().hex
            db.execute('INSERT INTO learning_documents VALUES (?,?,?,?,?,?,?)',
                       (identifier, None, kind, url, 'reference_only', json.dumps({
                           'access': 'NOT_ANALYZED', 'reason': 'URL saved only. Import an authorized local copy to analyze.'}),
                        time.time()))
        return identifier

    def save_learning_source(self, source, kind, examples, details):
        if kind not in {'tutorial', 'creator', 'own'}:
            raise ValueError('Choose tutorial, creator or own video.')
        metadata = self.get_source(source)
        for example in examples:
            Segment(example['start'], example['end'], example['excerpt']).validate(metadata['duration'])
            if example['technique'] not in {'dialogue', 'visual_sample', *RECIPES}:
                raise ValueError('Unsupported technique identifier.')
        with self.connect() as db:
            old = db.execute('SELECT id FROM learning_documents WHERE source=? AND kind=?', (source, kind)).fetchone()
            identifier = old['id'] if old else uuid.uuid4().hex
            if old:
                # An explicit reimport updates observations, never confirmed/rejected examples or notes.
                db.execute("DELETE FROM learning_examples WHERE document=? AND status='observed' AND note=''", (identifier,))
                db.execute('UPDATE learning_documents SET details=?,state=?,updated=? WHERE id=?',
                           (json.dumps(details), 'indexed', time.time(), identifier))
            else:
                db.execute('INSERT INTO learning_documents VALUES (?,?,?,?,?,?,?)',
                           (identifier, source, kind, metadata['path'], 'indexed', json.dumps(details), time.time()))
            retained = {(r['start'], r['end'], r['technique']) for r in db.execute(
                'SELECT start,end,technique FROM learning_examples WHERE document=?', (identifier,))}
            for e in examples:
                if (e['start'], e['end'], e['technique']) in retained:
                    continue
                db.execute('INSERT INTO learning_examples VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                           (uuid.uuid4().hex, identifier, e['start'], e['end'], e['excerpt'], e['technique'],
                            e['explanation'], 'observed', '', 0, e.get('frame', ''), time.time()))
            self.learning_event(db, identifier, '', 'indexed', details)
        return identifier

    @staticmethod
    def learning_event(db, document, example, action, details):
        db.execute('INSERT INTO learning_events VALUES (?,?,?,?,?,?)',
                   (uuid.uuid4().hex, document, example, action, json.dumps(details), time.time()))

    def learning_documents(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM learning_documents ORDER BY updated DESC,id')]

    def learning_examples(self, query='', document=None):
        # Literal LIKE search, escaped so '%' and '_' are not wildcard commands.
        pattern = '%' + query[:500].replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        sql = r"""SELECT e.*,d.kind,d.source,d.reference FROM learning_examples e
            JOIN learning_documents d ON d.id=e.document
            WHERE (e.excerpt LIKE ? ESCAPE '\' OR e.note LIKE ? ESCAPE '\'
                   OR e.technique LIKE ? ESCAPE '\')"""
        args = [pattern] * 3
        if document:
            sql += ' AND e.document=?'
            args.append(document)
        with self.connect() as db:
            return [dict(r) for r in db.execute(sql + ' ORDER BY e.updated DESC,e.start,e.id LIMIT 500', args)]

    def correct_learning_example(self, identifier, status, note, use_note=False):
        if status not in {'observed', 'confirmed', 'rejected'} or not isinstance(note, str):
            raise ValueError('Invalid example correction.')
        with self.connect() as db:
            row = db.execute('''SELECT e.*,d.kind FROM learning_examples e
                JOIN learning_documents d ON d.id=e.document WHERE e.id=?''', (identifier,)).fetchone()
            if not row:
                raise ValueError('Example no longer exists.')
            if use_note and (row['kind'] != 'own' or status != 'confirmed' or not note.strip()):
                raise ValueError('Only a confirmed, nonempty note about your own video can guide Auto Edit.')
            db.execute('UPDATE learning_examples SET status=?,note=?,use_note=?,updated=? WHERE id=?',
                       (status, note.strip()[:4000], bool(use_note), time.time(), identifier))
            self.learning_event(db, row['document'], identifier, 'correction', {
                'previous_status': row['status'], 'status': status, 'note': note.strip()[:4000], 'use_note': bool(use_note)})
            if row['use_note'] or use_note:
                db.execute("DELETE FROM cache WHERE kind='analysis_window'")

    @staticmethod
    def delete_learning_document_rows(db, identifier):
        for table in ('learning_examples', 'learning_events'):
            db.execute(f'DELETE FROM {table} WHERE document=?', (identifier,))
        db.execute('DELETE FROM learning_documents WHERE id=?', (identifier,))
        db.execute("DELETE FROM cache WHERE kind='analysis_window'")

    def delete_learning_document(self, identifier):
        with self.connect() as db:
            self.delete_learning_document_rows(db, identifier)

    def record_technique_test(self, recipe, engine, passed, report):
        if recipe not in RECIPES or type(passed) is not bool:
            raise ValueError('Invalid capability test.')
        with self.connect() as db:
            db.execute('INSERT INTO technique_tests VALUES (?,?,?,?,?,?)',
                       (uuid.uuid4().hex, recipe, engine, passed, json.dumps(report), time.time()))

    def technique_results(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM technique_tests ORDER BY created DESC,id DESC')]


def index_learning_video(store, media, kind, params, ffmpeg, runner, progress):
    """Index dialogue and sampled frames. No claim that a sampled frame was understood."""
    from .finder_jobs import make_thumbnail
    from .store import fingerprint
    if kind not in {'tutorial', 'creator', 'own'}:
        raise ValueError('Choose tutorial, creator or own video.')
    source = store.source(media)
    runner.check()
    segments = media.transcript
    if not segments:
        saved = store.cache_get(f'analysis-transcript:{source}')
        if saved is not None:
            segments = [Segment(**s) for s in saved]
        elif media.has_audio:
            from .speech import transcribe
            root = Path(params['model_folder']) if params.get('model_folder') else None
            segments = transcribe(media, ffmpeg, params['speech_model'], runner,
                                  lambda v, m: progress(v * .8, m), root, cache=store)
    examples = []
    for s in segments:
        runner.check()
        s.validate(media.duration)
        techniques = [key for key, pattern in TECHNIQUE_CUES.items() if re.search(pattern, s.text.casefold())]
        for technique in techniques or ['dialogue']:
            examples.append({'start': s.start, 'end': s.end, 'excerpt': s.text,
                'technique': technique, 'explanation': (
                    'Transcript mentions a possible technique. Purpose: ' + RECIPES[technique] +
                    ' Visual use has not been verified.' if technique != 'dialogue' else
                    'Timestamped dialogue reference; engagement and humor have not been assessed.')})
    from .learning_visual import observe_scene_changes
    scene_observations = observe_scene_changes(media, store.root, ffmpeg, runner,
                                               lambda v, m: progress(.8 + v * .1, m))
    for point in scene_observations['candidate_seconds'][:24]:
        examples.append({'start': point, 'end': min(media.duration, point + .1), 'excerpt': '',
                         'technique': 'visual_sample',
                         'explanation': 'Possible visual scene change; may be motion or a flash, not an edit.'})
    if not examples:
        # Silent/empty-ASR sources still get explicitly unassessed visual references.
        count = min(24, max(1, int(media.duration / 60) + 1))
        for i in range(count):
            start = i * media.duration / count
            examples.append({'start': start, 'end': min(media.duration, start + 1), 'excerpt': '',
                             'technique': 'visual_sample',
                             'explanation': 'Sampled source frame; no transcript or visual interpretation available.'})
    # Bound disk work: capture at most 24 evenly distributed examples, including endpoints.
    count = min(24, len(examples))
    indices = sorted({round(i * (len(examples)-1) / max(1, count-1)) for i in range(count)})
    for i, index in enumerate(indices):
        item = examples[index]
        frame = make_thumbnail(store, {'source': source, **item}, ffmpeg, runner)
        item['frame'] = str(frame.relative_to(store.root))
        progress(.9 + .09 * (i+1)/len(indices), 'Saving timestamped frame samples')
    runner.check()
    if fingerprint(media.path) != source:
        raise ValueError('The video changed during indexing. Import the stable file again.')
    details = {'transcript_lines': len(segments), 'sampled_frames': len(indices),
               'scene_observations': scene_observations,
               'visual_understanding': 'NOT_IMPLEMENTED', 'engagement_quality': 'NOT_EVALUATED',
               'method': 'Transcript index and keyword technique hypotheses; no model training.'}
    store.cache_put(f'analysis-transcript:{source}', source, 'analysis_transcript', [asdict(s) for s in segments])
    progress(.99, 'Saving learned examples')
    runner.check()
    identifier = store.save_learning_source(source, kind, examples, details)
    return {'document': identifier, **details}


def compare_transcripts(original, finished):
    """Conservative text matches, with both timestamps. Not audiovisual alignment."""
    def keyed(media):
        result = {}
        for s in media.transcript:
            s.validate(media.duration)
            words = re.findall(r"[\w']+", s.text.casefold())
            if len(words) >= 6:
                result.setdefault(' '.join(words), []).append(s)
        return result
    left, right = keyed(original), keyed(finished)
    matches = []
    for text, rows in left.items():
        if len(rows) == 1 and len(right.get(text, [])) == 1:
            a, b = rows[0], right[text][0]
            matches.append({'original_start': a.start, 'original_end': a.end,
                            'finished_start': b.start, 'finished_end': b.end, 'text': a.text,
                            'status': 'text_match_only'})
    return sorted(matches, key=lambda r: r['finished_start'])


def run_learning_job(store, media, params, job_id, ffmpeg, runner, progress):
    """Persist progress/errors; manual retry uses completed speech chunks."""
    from .video import Cancelled
    last = [0.0, 0.0]
    def report(value, message):
        last[0] = max(last[0], value)
        progress(last[0], message)
        if time.monotonic() - last[1] > .5:
            store.update_job(job_id, 'running', last[0], message)
            last[1] = time.monotonic()
    store.update_job(job_id, 'running', 0, 'Indexing learning source')
    try:
        result = index_learning_video(store, media, params['source_kind'], params, ffmpeg, runner, report)
    except Cancelled:
        store.update_job(job_id, 'cancelled', last[0], 'Cancelled; completed speech chunks are cached')
        raise
    except Exception as error:
        store.update_job(job_id, 'failed', last[0], str(error))
        raise
    warning = ''
    try:
        store.update_job(job_id, 'completed', 1, 'Learning source indexed: ' + result['document'])
    except Exception as error:
        warning = f'Knowledge was saved, but job history could not be updated: {error}'
    return {**result, 'committed': True, 'history_warning': warning}
