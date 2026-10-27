"""Automatic orchestration with a fixture model and real FFmpeg, not humor acceptance."""
from dataclasses import asdict
import json
from pathlib import Path

import pytest

from anato12_studio.auto_edit import AutoOptions, run_auto_edit, select_ranges
from anato12_studio.finder import rows_for
from anato12_studio.model import Media, Project, Segment
from anato12_studio.quality import ensure_capabilities, verify_video
from anato12_studio.store import Store, fingerprint
from anato12_studio.video import Cancelled, Runner, probe
from test_local_model import endpoint  # noqa: F401


def candidate(media, identifier='h', start=2, end=8, **overrides):
    last = len(media.transcript) - 1
    return {'id': identifier, 'source': 's', 'status': 'unreviewed', 'start': start, 'end': end,
            'rank': 10, 'category': 'banter', 'title': 'Complete exchange', 'method': 'local model order',
            'structure': json.dumps({'version': 1, 'first_id': 0, 'last_id': last,
                'setup_ids': [0], 'payoff_ids': [last], 'reaction_ids': [], 'needs_context': False}),
            'evidence': json.dumps(rows_for(media.transcript)), **overrides}


def test_selection_expands_whole_lines_keeps_evidence_and_budget():
    media = Media('m', 'source.mp4', 100, 320, 180,
                  transcript=[Segment(2.01, 3.51, 'setup'), Segment(7, 9.01, 'reaction')])
    item = candidate(media, start=2, end=9.1)
    selected, skipped = select_ranges(media, 's', [item], [], {}, AutoOptions())
    assert not skipped and selected[0]['start'] == 2 and selected[0]['end'] >= 9.1
    assert item['status'] == 'unreviewed' and item['end'] == 9.1
    selected, skipped = select_ranges(media, 's', [item], [], {}, AutoOptions(max_main_seconds=4))
    assert not selected and 'budget' in skipped[0]['reason']
    # Approved cut crossing an utterance expands to include the entire line.
    selected, _ = select_ranges(media, 's', [candidate(media, status='approved', start=3, end=8)], [], {}, AutoOptions())
    assert selected[0]['start'] == 2 and selected[0]['end'] >= 9.01


@pytest.mark.parametrize('change,reason', [
    ({'evidence': '[]'}, 'Evidence'),
    ({'evidence': '[{"id":999}]'}, 'Evidence'),
    ({'method': 'context cues'}, 'cue/search'),
    ({'end': 6}, 'outside'),
    ({'status': 'rejected'}, 'rejected'),
])
def test_auto_selection_rejects_missing_context_and_untrusted_evidence(change, reason):
    media = Media('m', 'source.mp4', 100, 320, 180,
                  transcript=[Segment(3, 4, 'real setup'), Segment(5, 7, 'real payoff')])
    selected, skipped = select_ranges(media, 's', [candidate(media, **change)], [], {}, AutoOptions())
    assert not selected and reason in skipped[0]['reason']


def test_rejected_ranges_apply_even_to_new_model_candidates():
    media = Media('m', 'source.mp4', 100, 320, 180,
                  transcript=[Segment(3, 4, 'real setup'), Segment(5, 7, 'real payoff')])
    selected, skipped = select_ranges(media, 's', [candidate(media)], [{'start': 7, 'end': 8}], {}, AutoOptions())
    assert not selected and 'rejected' in skipped[0]['reason']


@pytest.fixture
def auto_source(tmp_path, recording, binaries, endpoint):  # noqa: F811
    store = Store(tmp_path / 'profile')
    media = Media('m', str(recording), **probe(str(recording), binaries[1]),
                  transcript=[Segment(.1, 1, 'fixture setup'), Segment(1.5, 3, 'fixture reply')])
    source = store.source(media)
    params = {'kind': 'auto_edit', 'contextual': True, 'url': endpoint[0], 'model': 'fixture-local',
              'auto_options': asdict(AutoOptions(save_srt=True, burn_captions=True)),
              'output_parent': str(tmp_path)}
    return store, media, source, params


@pytest.mark.parametrize('history_failure', [False, True])
def test_one_run_checked_main_and_shorts_without_manual_approval(auto_source, binaries, monkeypatch, history_failure):
    store, media, source, params = auto_source
    before = asdict(media)
    job = store.create_job(source, params)
    if history_failure:
        update = store.update_job
        def fail_completed(identifier, status, progress=0, message=''):
            if status == 'completed':
                raise OSError('injected history failure after publication')
            return update(identifier, status, progress, message)
        monkeypatch.setattr(store, 'update_job', fail_completed)
    result = run_auto_edit(store, source, media, params, job, *binaries, Runner(), lambda *_: None)
    folder = Path(result['directory'])
    manifest = json.loads((folder / 'draft-manifest.json').read_text())
    assert result['committed'] and result['shorts'] == 1 and result['main_clips'] == 1
    assert 'approved_highlights' not in manifest
    assert manifest['automation']['selection'][0]['status'] == 'unreviewed'
    assert store.highlights(source)[0]['status'] == 'unreviewed'
    for entry in manifest['outputs']:
        assert entry['quality']['full_decode'] == 'passed'
        assert entry['quality']['humor_quality'] == 'NOT_EVALUATED'
        assert Project.load(folder / entry['project']).media['m'].path == media.path
    assert len(store.technique_results()) == 3
    assert asdict(media) == before and fingerprint(media.path) == source
    assert store.jobs()[0]['status'] == ('running' if history_failure else 'completed')
    assert bool(result['history_warning']) is history_failure
    assert not list(folder.parent.glob('.anato12-drafts-*'))


@pytest.mark.parametrize('failure', ['quality', 'cancel'])
def test_auto_failure_never_publishes_unchecked_bundle(auto_source, binaries, monkeypatch, failure):
    store, media, source, params = auto_source
    params['auto_options'].update(burn_captions=False, save_srt=False)
    def broken(*args):
        if failure == 'cancel':
            raise Cancelled('fixture cancellation during quality checks')
        raise ValueError('fixture corrupt output')
    monkeypatch.setattr('anato12_studio.auto_edit.verify_bundle', broken)
    job = store.create_job(source, params)
    with pytest.raises(Cancelled if failure == 'cancel' else ValueError):
        run_auto_edit(store, source, media, params, job, *binaries, Runner(), lambda *_: None)
    assert store.jobs()[0]['status'] == ('cancelled' if failure == 'cancel' else 'failed')
    assert not list(Path(params['output_parent']).glob('Anato12-auto-*'))
    assert not list(Path(params['output_parent']).glob('.anato12-drafts-*'))
    assert fingerprint(media.path) == source
    if failure == 'cancel':
        # A restart reuses analysis, but rerenders in a fresh owned directory.
        store.update_job(job, 'running', .9, 'Simulated app interruption')
        reopened = Store(store.root)
        reopened.recover_jobs()
        assert reopened.jobs()[0]['status'] == 'interrupted'
        from anato12_studio.quality import verify_bundle
        monkeypatch.setattr('anato12_studio.auto_edit.verify_bundle', verify_bundle)
        result = run_auto_edit(reopened, source, media, params, job, *binaries, Runner(), lambda *_: None)
        assert result['committed'] and reopened.jobs()[0]['status'] == 'completed'


def test_missing_model_fails_without_fallback(auto_source, binaries):
    store, media, source, params = auto_source
    params['model'] = ''
    job = store.create_job(source, params)
    with pytest.raises(ValueError, match='explicitly selected'):
        run_auto_edit(store, source, media, params, job, *binaries, Runner(), lambda *_: None)
    assert store.jobs()[0]['status'] == 'failed'


def test_rejected_model_results_produce_no_auto_output(auto_source, binaries):
    from anato12_studio.finder_jobs import run_pipeline
    store, media, source, params = auto_source
    job = store.create_job(source, params)
    result = run_pipeline(store, source, media, params, job, binaries[0], Runner(), lambda *_: None)
    store.review(result['ids'][0], 'rejected')
    with pytest.raises(ValueError, match='No usable complete exchanges'):
        run_auto_edit(store, source, media, params, job, *binaries, Runner(), lambda *_: None)
    assert not store.technique_results()
    assert not list(Path(params['output_parent']).glob('Anato12-auto-*'))


def test_committed_job_reports_success_despite_late_cancel():
    from anato12_studio.jobs import Job
    def operation(runner, progress):
        runner.cancel()
        return {'committed': True, 'directory': 'published'}
    job = Job(operation)
    results, cancelled = [], []
    job.result.connect(results.append)
    job.cancelled.connect(cancelled.append)
    job.run()
    assert results == [{'committed': True, 'directory': 'published'}] and not cancelled


def test_capability_failure_blocks_export_and_success_is_engine_specific(tmp_path, binaries, monkeypatch):
    store = Store(tmp_path / 'profile')
    engine = ensure_capabilities(store, ['zoom'], *binaries, Runner(), lambda *_: None)
    assert store.technique_results()[0]['passed'] == 1
    assert ensure_capabilities(store, ['zoom'], *binaries, Runner(), lambda *_: None) == engine
    assert len(store.technique_results()) == 1
    monkeypatch.setattr('anato12_studio.quality.engine_identity', lambda *a: 'changed-engine')
    def failed(*a):
        raise RuntimeError('fixture decoder failed')
    monkeypatch.setattr('anato12_studio.quality.verify_video', failed)
    with pytest.raises(RuntimeError, match='decoder'):
        ensure_capabilities(store, ['zoom'], *binaries, Runner(), lambda *_: None)
    assert store.technique_results()[0]['passed'] == 0


def test_quality_detects_wrong_dimensions(recording, binaries):
    media = Media('m', str(recording), **probe(str(recording), binaries[1]))
    from anato12_studio.model import Clip
    project = Project(media={'m': media}, clips=[Clip('m', 0, 4)], save_srt=False)
    with pytest.raises(ValueError, match='dimensions'):
        verify_video(recording, project, *binaries, Runner())


def ranked_ranges(media, ranges):
    return [candidate(media, identifier=name, start=start, end=end, status='approved', rank=10-i)
            for i, (name, start, end) in enumerate(ranges)]


@pytest.mark.parametrize('limits', [
    {'max_ranges': 1}, {'max_main_seconds': 85},
])
def test_complete_short_is_reserved_when_longer_range_would_fill_budget(limits):
    media = Media('m', 'source.mp4', 300, 320, 180)
    items = ranked_ranges(media, [('long', 0, 80), ('short', 100, 120)])
    before = json.dumps(items)
    chosen, skipped = select_ranges(media, 's', items, [], {}, AutoOptions(**limits))
    assert [h['id'] for h in chosen] == ['short']
    assert chosen[0]['original_range'] == [100, 120]
    assert skipped[0]['highlight'] == 'long' and 'reserved' in skipped[0]['reason']
    assert json.dumps(items) == before


def test_short_reservation_refills_budget_and_keeps_recording_order():
    media = Media('m', 'source.mp4', 300, 320, 180)
    items = ranked_ranges(media, [('first', 100, 180), ('second', 200, 280), ('short', 0, 10)])
    chosen, skipped = select_ranges(media, 's', items, [], {}, AutoOptions(max_ranges=2))
    assert [h['id'] for h in chosen] == ['short', 'first']
    assert [h['highlight'] for h in skipped] == ['second']


def test_ordinary_ranking_is_preserved_when_it_already_contains_a_short():
    media = Media('m', 'source.mp4', 300, 320, 180)
    items = ranked_ranges(media, [('first', 0, 80), ('short', 100, 120), ('other', 200, 210)])
    chosen, skipped = select_ranges(media, 's', items, [], {}, AutoOptions(max_ranges=2))
    assert [h['id'] for h in chosen] == ['first', 'short']
    assert len(skipped) == 1 and 'reserved' not in skipped[0]['reason']


def test_reserved_short_still_enforces_rejections_evidence_and_expanded_boundaries():
    media = Media('m', 'source.mp4', 300, 320, 180,
                  transcript=[Segment(100, 170, 'A whole long line must be retained')])
    items = ranked_ranges(media, [('long', 0, 80), ('expanded', 105, 115),
                                 ('rejected', 180, 190), ('stale', 220, 230), ('short', 250, 260)])
    items[3].update(status='unreviewed', structure='{}')
    chosen, skipped = select_ranges(media, 's', items, [{'start': 185, 'end': 186}], {},
                                   AutoOptions(max_ranges=1))
    assert [h['id'] for h in chosen] == ['short']
    by_id = {h['highlight']: h['reason'] for h in skipped}
    assert 'rejected' in by_id['rejected'] and 'analyze' in by_id['stale']
    assert 'reserved' in by_id['expanded']


def test_short_reservation_never_creates_substantially_overlapping_outputs():
    media = Media('m', 'source.mp4', 300, 320, 180)
    items = ranked_ranges(media, [('long', 0, 80), ('second', 100, 180), ('short', 10, 20)])
    chosen, skipped = select_ranges(media, 's', items, [], {}, AutoOptions(max_ranges=2))
    assert [h['id'] for h in chosen] == ['short', 'second']
    assert len(skipped) == 1 and 'overlaps' in skipped[0]['reason']


def test_short_reservation_cannot_exceed_main_budget_or_truncate_dialogue():
    media = Media('m', 'source.mp4', 300, 320, 180)
    items = ranked_ranges(media, [('short', 100, 120)])
    chosen, skipped = select_ranges(media, 's', items, [], {}, AutoOptions(max_main_seconds=10))
    assert not chosen and len(skipped) == 1 and 'budget' in skipped[0]['reason']
    items = ranked_ranges(media, [('long', 0, 80), ('second', 100, 170)])
    chosen, _ = select_ranges(media, 's', items, [], {}, AutoOptions(max_ranges=1))
    assert chosen[0]['id'] == 'long' and chosen[0]['end'] == 80


def test_selection_cancellation_is_checked_during_boundary_expansion():
    media = Media('m', 'source.mp4', 300, 320, 180,
                  transcript=[Segment(5, 7, 'one'), Segment(7, 9, 'two')])
    items = ranked_ranges(media, [('crossing', 6, 8)])
    class CancelDuringScan(Runner):
        checks = 0
        def check(self):
            self.checks += 1
            if self.checks == 6:  # inside the first boundary scan, after validation
                self.cancel()
            super().check()
    runner = CancelDuringScan()
    before = asdict(media)
    with pytest.raises(Cancelled):
        select_ranges(media, 's', items, [], {}, AutoOptions(), runner)
    assert runner.checks == 6 and asdict(media) == before
    assert items[0]['start'] == 6


def test_reserved_short_runs_through_real_checked_export(auto_source, binaries, monkeypatch):
    store, media, source, params = auto_source
    media.transcript = [Segment(.1, .9, 'First line'), Segment(2, 3.2, 'Second complete line')]
    params['auto_options'].update(max_ranges=1, max_short_seconds=1.5, burn_captions=False)
    ids = []
    for i, (name, a, b) in enumerate([('long', 0, 3.8), ('short', 2, 3.2)]):
        identifier = store.upsert_highlight(source, name, a, b, name, 'other', '', '', [], 'manual', 10-i)
        store.review(identifier, 'approved')
        ids.append(identifier)
    monkeypatch.setattr('anato12_studio.auto_edit.run_pipeline',
                        lambda *a, **kw: {'segments': media.transcript, 'ids': ids})
    job = store.create_job(source, params)
    result = run_auto_edit(store, source, media, params, job, *binaries, Runner(), lambda *_: None)
    manifest = json.loads((Path(result['directory']) / 'draft-manifest.json').read_text())
    assert result['shorts'] == 1 and store.jobs()[0]['status'] == 'completed'
    assert manifest['automation']['selection'][0]['id'] == ids[1]
    assert manifest['automation']['skipped'][0]['highlight'] == ids[0]
    for entry in manifest['outputs']:
        assert entry['quality']['full_decode'] == 'passed'
        assert entry['quality']['duration_seconds'] == pytest.approx(1.2, abs=.05)
    assert all(store.highlight(i)['status'] == 'approved' for i in ids)


@pytest.mark.parametrize('cancel', [False, True])
def test_failed_history_write_does_not_mask_original_error_or_cancellation(auto_source, binaries, monkeypatch, cancel):
    store, media, source, params = auto_source
    params['model'] = '' if not cancel else params['model']
    job = store.create_job(source, params)
    original = store.update_job
    def fail_final(identifier, status, *args):
        if status in {'failed', 'cancelled'}:
            raise OSError('fixture history write failure')
        return original(identifier, status, *args)
    monkeypatch.setattr(store, 'update_job', fail_final)
    runner = Runner()
    if cancel:
        runner.cancel()
    with pytest.raises(Cancelled if cancel else ValueError, match=None if cancel else 'explicitly selected'):
        run_auto_edit(store, source, media, params, job, *binaries, runner, lambda *_: None)
    assert not list(Path(params['output_parent']).glob('Anato12-auto-*'))
