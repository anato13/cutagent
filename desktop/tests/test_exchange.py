"""Reference checks are not semantic truth; no invented human quality labels."""
from dataclasses import asdict
import json
import sqlite3

import pytest

from anato12_studio.auto_edit import AutoOptions, select_ranges
from anato12_studio.exchange import describe_exchange, exchange_evidence, validate_structure
from anato12_studio.finder import analyze, model_proposals, rows_for
from anato12_studio.model import Media, Segment
from anato12_studio.store import Store
from anato12_studio.video import Runner


def dialogue():
    return [Segment(5, 7, 'Did you really take it earlier?'),
            Segment(8, 10, 'No, I did not already have that photo.'),
            Segment(11, 13, 'Then how did you take it earlier?')]


def raw(**changes):
    return {'first_id': 0, 'last_id': 2, 'evidence_ids': [0, 1, 2],
            'setup_ids': [0], 'payoff_ids': [1], 'reaction_ids': [2], 'needs_context': False,
            'title': 'They admit the photo is fake', 'reason': 'Unverified invented explanation', **changes}


def saved(media, **changes):
    proposal = model_proposals([raw()], rows_for(media.transcript), {}, media.duration)[0]
    return {'id': 'h', 'source': 's', 'status': 'unreviewed', **asdict(proposal),
            'evidence': json.dumps(proposal.evidence), 'structure': json.dumps(proposal.structure), **changes}


def test_quote_title_and_role_text_only_come_from_cited_dialogue():
    rows = rows_for(dialogue())
    proposal = model_proposals([raw()], rows, {}, 30)[0]
    assert 'admit' not in proposal.title and 'fake' not in proposal.title
    assert rows[0]['text'] in proposal.title and rows[1]['text'] in proposal.title
    assert proposal.structure['model_title'] == 'They admit the photo is fake'
    # The raw interpretation remains available, not certified as supported.
    assert proposal.reason == 'Unverified invented explanation'
    media = Media('m', 'source.mp4', 30, 320, 180, transcript=dialogue())
    item = saved(media)
    report = exchange_evidence(item, rows)
    assert report['roles']['reaction'] == [rows[2]]
    assert report['semantic_quality'] == 'NOT_EVALUATED'
    assert 'meaning has not been verified' in describe_exchange(item)


@pytest.mark.parametrize('changes', [
    {'setup_ids': []}, {'payoff_ids': []}, {'reaction_ids': None}, {'setup_ids': [True]},
    {'setup_ids': [999]}, {'setup_ids': '0'}, {'payoff_ids': [0]}, {'setup_ids': [2]},
    {'reaction_ids': [0]}, {'reaction_ids': [2, 2]}, {'needs_context': 'false'},
    {'needs_context': None}, {'last_id': 1}, {'evidence_ids': [999]},
])
def test_bad_or_uncited_roles_do_not_become_candidates(changes):
    assert model_proposals([raw(**changes)], rows_for(dialogue()), {}, 30) == []


def test_role_references_supply_real_evidence_without_redundant_model_list():
    rows = rows_for(dialogue())
    item = raw(evidence_ids=[])
    proposal = model_proposals([item], rows, {}, 30)[0]
    assert proposal.evidence == rows
    assert proposal.structure['role_evidence_added'] == [0, 1, 2]
    assert item['evidence_ids'] == []  # Raw model response retained without rewriting it.
    item.pop('evidence_ids')
    assert model_proposals([item], rows, {}, 30)[0].evidence == rows


def test_unapproved_legacy_or_context_dependent_candidates_cannot_auto_export():
    media = Media('m', 'source.mp4', 30, 320, 180, transcript=dialogue())
    for structure, message in [('{}', 'analyze'), (json.dumps({**raw(), 'version': 1, 'needs_context': True}), 'context')]:
        selected, skipped = select_ranges(media, 's', [saved(media, structure=structure)], [], {}, AutoOptions())
        assert not selected and message in skipped[0]['reason']
    # Explicit human approval remains usable even for older saved suggestions.
    selected, _ = select_ranges(media, 's', [saved(media, status='approved', structure='{}')], [], {}, AutoOptions())
    assert selected[0]['exchange']['reference_check'] == 'human_approved'


def test_changed_transcript_invalidates_role_evidence_even_with_same_ids():
    media = Media('m', 'source.mp4', 30, 320, 180, transcript=dialogue())
    item = saved(media)
    media.transcript[0].text = 'Different setup'
    with pytest.raises(ValueError, match='no longer matches'):
        exchange_evidence(item, rows_for(media.transcript))


def test_callback_is_valid_reference_but_cannot_drop_distant_setup():
    rows = rows_for([Segment(1, 2, 'earlier setup'), Segment(120, 121, 'payoff'), Segment(123, 124, 'reaction')])
    proposal = model_proposals([raw(first_id=1)], rows[1:], {1: [rows[0]]}, 150)[0]
    assert proposal.structure['setup_ids'] == [0]
    assert model_proposals([raw(first_id=1)], rows[1:], {}, 150) == []


def test_near_duplicate_ranges_after_expansion_are_not_multiple_shorts():
    media = Media('m', 'source.mp4', 60, 320, 180, transcript=dialogue())
    first = saved(media, start=1, end=20, status='approved')
    second = saved(media, id='second', start=6, end=24, status='approved', rank=9)
    selected, skipped = select_ranges(media, 's', [first, second], [], {}, AutoOptions())
    assert len(selected) == 1 and 'overlaps' in skipped[0]['reason']


def test_fresh_analysis_updates_only_untouched_unreviewed_highlights(tmp_path):
    source_file = tmp_path / 'source.mp4'
    source_file.write_bytes(b'identity only')
    media = Media('m', str(source_file), 30, 320, 180, transcript=dialogue())
    store = Store(tmp_path / 'profile')
    source = store.source(media)
    class Model:
        base, model, digest = 'http://localhost', 'fixture', 'one'
        def identity(self, runner=None):
            return {'digest': self.digest}
        def analyze(self, *args):
            return [raw(reason=self.digest)]
    model = Model()
    identifier = analyze(store, source, media.transcript, 30, Runner(), lambda *_: None, model)[0]
    model.digest = 'two'
    assert analyze(store, source, media.transcript, 30, Runner(), lambda *_: None, model) == [identifier]
    assert store.highlight(identifier)['reason'] == 'two'
    for decision in ('approved', 'rejected'):
        store.review(identifier, decision)
        before = store.highlight(identifier)
        model.digest = decision
        analyze(store, source, media.transcript, 30, Runner(), lambda *_: None, model)
        assert store.highlight(identifier) == before
    store.review(identifier, 'unreviewed')
    store.adjust(identifier, 3, 15, 'My manual title', 'My excerpt')
    before = store.highlight(identifier)
    model.digest = 'three'
    analyze(store, source, media.transcript, 30, Runner(), lambda *_: None, model)
    assert store.highlight(identifier) == before


def test_v3_upgrade_and_rollback_preserve_legacy_highlights(tmp_path, monkeypatch):
    store = Store(tmp_path / 'profile')
    identifier = store.upsert_highlight('s', 'sig', 1, 10, 'Old label', 'other', 'Old reason', '', [], 'local model order', 1)
    store.review(identifier, 'approved')
    with store.connect() as db:
        db.execute('ALTER TABLE highlights DROP COLUMN structure')
        db.execute('PRAGMA user_version=3')
    from contextlib import contextmanager
    @contextmanager
    def interrupted(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            yield db
            raise OSError('injected migration interruption')
        finally:
            db.rollback()
            db.close()
    with monkeypatch.context() as patch:
        patch.setattr(Store, 'connect', interrupted)
        with pytest.raises(OSError):
            Store(store.root)
    with sqlite3.connect(store.path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 3
        assert 'structure' not in {r[1] for r in db.execute('PRAGMA table_info(highlights)')}
    reopened = Store(store.root)
    assert reopened.highlight(identifier)['status'] == 'approved'
    assert reopened.highlight(identifier)['structure'] == '{}'
    with reopened.connect() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 4


def test_validator_does_not_call_correct_role_labels_verified_meaning():
    # Deliberately mislabeled real lines pass reference checks: semantics require separate review.
    checked = validate_structure(raw(setup_ids=[0], payoff_ids=[2], reaction_ids=[]),
                                 {r['id']: r for r in rows_for(dialogue())})
    assert checked['payoff_ids'] == [2]


@pytest.mark.parametrize('bad', ['[]', 'null', '3', '{not json', '{"setup_ids":[[0]]}'])
def test_unreadable_map_has_actionable_ui_message(bad):
    assert 'could not be read' in describe_exchange({'structure': bad, 'evidence': '[]'})
