"""Group-comedy preset changes review priority only with cited source roles."""
from anato12_studio.finder import analyze, possible_topic_refs, rows_for
from anato12_studio.editorial_style import (STYLE_DEFAULT, STYLE_GROUP_COMEDY,
    guard_callback_opening, plan_group_opening, selection_priority, validate_style)
from anato12_studio.model import Segment
from anato12_studio.model_context import bounded_windows, messages_for, MAX_INPUT_BYTES
from anato12_studio.store import Store
from anato12_studio.video import Runner


def item(identifier, start, rank, category='banter', status='unreviewed', reaction=True):
    return {'id': identifier, 'start': start, 'end': start + 12, 'rank': rank,
            'category': category, 'status': status,
            'exchange': {'reference_check': 'passed', 'needs_context': False,
                         'roles': {'reaction': [{'id': int(start) + 2}]} if reaction else {}}}


def test_group_priority_favors_social_comedy_without_overriding_approval():
    social = item('social', 20, 20, 'misunderstanding')
    callback = item('callback', 30, 20, 'callback')
    gameplay = item('game', 50, 20, 'gameplay')
    approved = item('approved', 0, 1, 'gameplay', 'approved')
    assert selection_priority(social, {}, STYLE_DEFAULT) == 20
    assert selection_priority(social, {}, STYLE_GROUP_COMEDY) > selection_priority(
        gameplay, {}, STYLE_GROUP_COMEDY)
    assert selection_priority(callback, {}, STYLE_GROUP_COMEDY) > selection_priority(
        social, {}, STYLE_GROUP_COMEDY)
    assert selection_priority(approved, {}, STYLE_GROUP_COMEDY) == 1
    assert selection_priority(social, {'misunderstanding': -20}, STYLE_GROUP_COMEDY) < 20


def test_short_source_cited_reaction_can_open_once_without_losing_later_moments():
    selected = [item('setup', 0, 10, 'gameplay'), item('reaction', 40, 40),
                item('ending', 90, 25)]
    plan = plan_group_opening(selected, 60)
    assert plan['opening_id'] == 'reaction'
    assert plan['source_reaction_ids'] == [42]
    assert plan['reaction_meaning'] == 'NOT_EVALUATED'


def test_missing_reaction_extra_context_or_no_later_clip_keeps_source_order():
    selected = [item('setup', 0, 10, 'gameplay'), item('middle', 40, 40, reaction=False),
                item('ending', 90, 20)]
    assert plan_group_opening(selected, 60)['opening_id'] is None
    selected[1] = item('middle', 40, 40)
    selected[1]['exchange']['needs_context'] = True
    assert plan_group_opening(selected, 60)['opening_id'] is None
    selected[1]['exchange']['needs_context'] = False
    selected.pop()
    assert plan_group_opening(selected, 60)['opening_id'] is None


def test_group_callback_stays_after_selected_earlier_setup():
    selected = [item('setup', 0, 10), item('callback', 40, 50, 'callback'),
                item('later', 90, 20)]
    opening, reason = guard_callback_opening(selected, 'callback')
    assert opening is None and 'kept after' in reason
    opening, reason = guard_callback_opening(selected, 'later')
    assert opening == 'later' and reason is None


def test_unknown_style_fails_explicitly():
    try:
        validate_style('copy_creator')
    except ValueError as error:
        assert 'supported' in str(error)
    else:
        raise AssertionError('Unknown editing preset was accepted')


def test_group_model_guidance_keeps_timestamped_rows_within_budget():
    rows = rows_for([Segment(0, 1, 'a'*3200), Segment(40, 42, 'The cone fooled everyone.')])
    windows = list(bounded_windows(rows, {}, editing_style=STYLE_GROUP_COMEDY))
    assert len(windows) == 2 and all(w.content_bytes <= MAX_INPUT_BYTES for w in windows)
    assert windows[0].rows[0]['text'] == 'a'*3200
    message = messages_for(rows[1:], {}, '', {}, editing_style=STYLE_GROUP_COMEDY)[0]['content']
    assert 'complete friend exchanges' in message and 'Do not imitate' in message
    assert 'first setup of a recurring bit' in message
    assert 'first setup of a recurring bit' in messages_for(rows[1:], {}, '', {})[0]['content']


def test_group_model_request_uses_separate_cache_and_style(tmp_path):
    class Model:
        base, model = 'http://127.0.0.1:11434', 'fixture-local'
        def __init__(self):
            self.calls = []
        def identity(self, runner):
            return {'digest': 'test-digest', 'configuration': 'fixed'}
        def analyze(self, *args, editing_style=STYLE_DEFAULT, **kwargs):
            self.calls.append(editing_style)
            return []
    model = Model()
    store = Store(tmp_path / 'profile')
    segments = [Segment(1, 2, 'I became a traffic cone.'),
                Segment(3, 4, 'Nobody is going to believe you.')]
    for style in (STYLE_DEFAULT, STYLE_GROUP_COMEDY, STYLE_GROUP_COMEDY):
        analyze(store, 'source', segments, 20, Runner(), lambda *_: None,
                model=model, editing_style=style)
    assert model.calls == [STYLE_DEFAULT, STYLE_GROUP_COMEDY]


def test_distant_recurring_topic_supplies_source_context_without_claiming_humor():
    rows = rows_for([Segment(0, 2, 'Why are we talking about feet?'),
                     Segment(125, 127, 'Your brother is here.'),
                     Segment(300, 302, 'Your brother mentioned those feet again.')])
    refs = possible_topic_refs(rows)
    assert {item['id'] for item in refs[2]} == {0, 1}
    assert not possible_topic_refs(rows_for([
        Segment(0, 1, 'That was really good.'),
        Segment(100, 101, 'That was really good.')]))
    windows = list(bounded_windows(rows, refs, editing_style=STYLE_GROUP_COMEDY))
    assert {item['id'] for prior in windows[-1].callbacks.values() for item in prior} == {0, 1}


def test_group_finder_passes_distant_topic_reference_to_model(tmp_path):
    class Model:
        base, model = 'http://127.0.0.1:11434', 'fixture-local'
        def __init__(self):
            self.references = []
        def identity(self, runner):
            return {'digest': 'test-digest', 'configuration': 'fixed'}
        def analyze(self, rows, references, *args, **kwargs):
            self.references.append(references)
            return []
    model = Model()
    analyze(Store(tmp_path / 'profile'), 'source', [
        Segment(0, 2, 'My brother talks about feet.'),
        Segment(300, 302, 'Your brother mentioned feet again.')],
        310, Runner(), lambda *_: None, model=model, editing_style=STYLE_GROUP_COMEDY)
    assert any(any(item['id'] == 0 for item in refs.get(1, []))
               for refs in model.references)
