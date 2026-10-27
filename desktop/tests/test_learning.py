"""Persistent evidence/consent and local indexing; no humor-learning claims."""
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

import pytest

from anato12_studio.knowledge import compare_transcripts, index_learning_video, run_learning_job
from anato12_studio.learning_visual import observe_scene_changes
from anato12_studio.model import Media, Segment
from anato12_studio.store import Store
from anato12_studio.video import Cancelled, Runner, probe


@pytest.fixture
def learned(tmp_path, recording, binaries):
    store = Store(tmp_path / 'profile')
    media = Media('m', str(recording), **probe(str(recording), binaries[1]),
                  transcript=[Segment(.1, 1, 'Use a jump cut then zoom with captions'),
                              Segment(1.1, 2, 'Keep the whole setup and the reaction')])
    result = index_learning_video(store, media, 'own', {}, binaries[0], Runner(), lambda *_: None)
    return store, media, result['document']


def test_index_citations_frames_reopen_search_and_corrections(learned, binaries):
    store, media, doc = learned
    rows = store.learning_examples('zoom', doc)
    assert rows and all(r['status'] == 'observed' and r['start'] == .1 for r in rows)
    assert all(Path(store.root / r['frame']).read_bytes().startswith(b'\x89PNG') for r in rows)
    assert store.learning_examples('%') == []
    assert [r['technique'] for r in store.learning_examples('_')] == ['trim_join']
    assert store.technique_results() == []  # tutorial words never certify an operation
    chosen = rows[0]['id']
    store.correct_learning_example(chosen, 'confirmed', 'Keep setup and reaction', True)
    assert store.model_preferences()['notes'][0]['note'] == 'Keep setup and reaction'
    reopened = Store(store.root)
    assert reopened.learning_examples('setup and reaction', doc)[0]['id'] == chosen
    index_learning_video(reopened, media, 'own', {}, binaries[0], Runner(), lambda *_: None)
    same = [r for r in reopened.learning_examples(document=doc) if r['id'] == chosen]
    assert len(same) == 1 and same[0]['status'] == 'confirmed' and same[0]['use_note'] == 1
    assert len(reopened.learning_examples(document=doc)) == 4


def test_correction_consent_revocation_export_delete(learned, tmp_path):
    store, media, doc = learned
    example = store.learning_examples(document=doc)[0]
    store.correct_learning_example(example['id'], 'confirmed', 'private', False)
    assert store.model_preferences()['notes'] == []
    with pytest.raises(ValueError, match='confirmed'):
        store.correct_learning_example(example['id'], 'observed', 'not confirmed', True)
    source = store.source(media)
    store.cache_put('window', source, 'analysis_window', ['old'])
    store.correct_learning_example(example['id'], 'confirmed', 'keep reactions', True)
    assert store.cache_get('window') is None
    assert store.model_preferences()['notes']
    store.correct_learning_example(example['id'], 'confirmed', 'private again', False)
    assert store.model_preferences()['notes'] == []
    output = tmp_path / 'export.json'
    store.export_data(output)
    data = json.loads(output.read_text(encoding='utf-8'))
    assert data['learning_documents'] and data['learning_events'] and data['learning_examples']
    original = Path(media.path).read_bytes()
    store.delete_source_data(source)
    assert not store.learning_documents() and not store.learning_examples()
    assert Path(media.path).read_bytes() == original


def test_url_is_only_a_reference_and_rejects_non_youtube(tmp_path):
    store = Store(tmp_path / 'profile')
    url = 'https://www.youtube.com/watch?v=example'
    doc = store.add_learning_url(url, 'creator')
    assert store.add_learning_url(url, 'creator') == doc
    row = store.learning_documents()[0]
    assert row['state'] == 'reference_only' and row['source'] is None
    assert json.loads(row['details'])['access'] == 'NOT_ANALYZED'
    assert not store.learning_examples()
    for bad in ('https://youtube.com.evil.test/a', 'file:///tmp/a', 'http://youtu.be/a', 'https://me@youtube.com/a'):
        with pytest.raises(ValueError):
            store.add_learning_url(bad, 'creator')


def test_relative_profile_resolves_before_ffmpeg_workers_change_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = Store(Path('profile'))
    assert store.root == tmp_path / 'profile' and store.path.is_absolute()


def test_cancelled_index_not_registered_as_analyzed(tmp_path, recording, binaries):
    store = Store(tmp_path / 'profile')
    media = Media('m', str(recording), **probe(str(recording), binaries[1]))
    runner = Runner()
    runner.cancel()
    with pytest.raises(Cancelled):
        index_learning_video(store, media, 'tutorial', {}, binaries[0], runner, lambda *_: None)
    assert not store.learning_documents()


def test_v2_migration_retains_existing_feedback_and_is_atomic(tmp_path, monkeypatch):
    store = Store(tmp_path / 'profile')
    with store.connect() as db:
        for table in ('learning_documents', 'learning_examples', 'learning_events', 'technique_tests'):
            db.execute(f'DROP TABLE {table}')
        db.execute("INSERT INTO feedback VALUES ('old','h','banter','approved','private',1,'user_confirmed',1,0)")
        db.execute('PRAGMA user_version=2')
    initialize = Store.initialize_knowledge
    def fail(db):
        initialize(db)
        raise OSError('injected migration failure')
    monkeypatch.setattr(Store, 'initialize_knowledge', staticmethod(fail))
    with pytest.raises(OSError):
        Store(store.root)
    with sqlite3.connect(store.path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 2
        assert db.execute("SELECT name FROM sqlite_master WHERE name='learning_documents'").fetchone() is None
        assert db.execute('SELECT note FROM feedback').fetchone()[0] == 'private'
    monkeypatch.setattr(Store, 'initialize_knowledge', staticmethod(initialize))
    assert Store(store.root).feedback()[0]['use_note'] == 0


def test_unique_transcript_comparison_not_humor_or_alignment():
    line = 'I opened the door and you fell through'
    raw = Media('r', 'raw.mp4', 100, 320, 180,
                transcript=[Segment(30, 33, line), Segment(40, 42, 'a repeated line with six different words'),
                            Segment(50, 52, 'a repeated line with six different words')])
    finished = Media('f', 'finished.mp4', 10, 320, 180,
                     transcript=[Segment(1, 4, line), Segment(5, 7, 'a repeated line with six different words')])
    before = asdict(raw)
    matches = compare_transcripts(raw, finished)
    assert len(matches) == 1
    assert matches[0]['original_start'] == 30 and matches[0]['finished_start'] == 1
    assert matches[0]['status'] == 'text_match_only' and asdict(raw) == before


def test_visual_scene_measurement_and_silent_index(tmp_path, binaries):
    import subprocess
    path = tmp_path / 'hard-cut.mp4'
    subprocess.run([binaries[0], '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
        'color=black:s=160x90:r=30:d=2[b];color=white:s=160x90:r=30:d=2[w];[b][w]concat=n=2:v=1:a=0',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path)], check=True, timeout=20)
    media = Media('silent', str(path), **probe(str(path), binaries[1]))
    observations = observe_scene_changes(media, tmp_path, binaries[0], Runner(), lambda *_: None)
    assert observations['candidate_count'] == 1 and observations['candidate_seconds'] == [2.0]
    store = Store(tmp_path / 'profile')
    result = index_learning_video(store, media, 'tutorial', {}, binaries[0], Runner(), lambda *_: None)
    assert result['transcript_lines'] == 0 and result['sampled_frames'] == 1
    example = store.learning_examples()[0]
    assert example['start'] == 2 and example['technique'] == 'visual_sample'
    assert 'not an edit' in example['explanation']
    assert not list(store.root.glob('scene-observations-*'))


def test_creator_notes_cannot_become_own_preferences(learned):
    store, media, doc = learned
    source = store.source(media)
    other = store.save_learning_source(source, 'creator', [{'start': 0, 'end': 1, 'excerpt': 'a caption',
        'technique': 'captions', 'explanation': 'unverified mention'}], {})
    row = store.learning_examples(document=other)[0]
    with pytest.raises(ValueError, match='own video'):
        store.correct_learning_example(row['id'], 'confirmed', 'copy that creator', True)
    assert not store.model_preferences()['notes']


def test_learning_failure_records_progress_and_can_retry(learned, binaries, monkeypatch):
    store, media, doc = learned
    params = {'kind': 'learn_video', 'source_kind': 'own'}
    job = store.create_job(store.source(media), params)
    original = index_learning_video
    def fail(store, media, kind, params, ffmpeg, runner, progress):
        progress(.4, 'Completed speech chunks')
        raise OSError('injected learning disk error')
    monkeypatch.setattr('anato12_studio.knowledge.index_learning_video', fail)
    with pytest.raises(OSError):
        run_learning_job(store, media, params, job, binaries[0], Runner(), lambda *_: None)
    assert store.jobs()[0]['status'] == 'failed' and store.jobs()[0]['progress'] == .4
    monkeypatch.setattr('anato12_studio.knowledge.index_learning_video', original)
    result = run_learning_job(store, media, params, job, binaries[0], Runner(), lambda *_: None)
    assert result['document'] == doc and result['committed']
    assert Store(store.root).jobs()[0]['status'] == 'completed'
