"""A source-linked opener changes order without inventing or repeating footage."""
from anato12_studio.drafts import DraftOptions, assemble
from anato12_studio.editorial_story import find_context_bridges, plan_story
from anato12_studio.model import Media, Segment


def moment(identifier, start, end, rank, status='unreviewed'):
    return {'id': identifier, 'source': 'source', 'start': start, 'end': end,
            'rank': rank, 'category': 'banter', 'status': status,
            'title': identifier}


def test_repeated_dialogue_can_move_one_complete_opening_without_repeating_it():
    transcript = [Segment(0, 1, 'They say the date is impossible.'),
                  Segment(3, 4, 'He insists the date is real.'),
                  Segment(100, 101, 'I am on a date.'),
                  Segment(103, 104, 'You are definitely not on a date.'),
                  Segment(200, 201, 'The date claim comes back.'),
                  Segment(203, 204, 'He finally explains the date.')]
    selected = [moment('setup', 0, 5, 10), moment('opening', 100, 105, 40),
                moment('ending', 200, 205, 20)]
    plan = plan_story(selected, transcript, 60)
    assert plan['possible_topic_word'] == 'date'
    assert plan['opening_id'] == 'opening'
    assert plan['main_order'] == ['opening', 'setup', 'ending']
    assert plan['ending_payoff'] == 'NOT_EVALUATED'
    media = Media('m', 'source.mp4', 250, 320, 180, transcript=transcript)
    main, shorts, details = assemble(media, 'source', selected,
                                     DraftOptions(opening_id=plan['opening_id']), 'automatic')
    assert [(clip.start, clip.end) for clip in main.clips] == [
        (100, 105), (0, 5), (200, 205)]
    assert [identifier for identifier, _ in shorts] == ['setup', 'opening', 'ending']
    assert details['opening_applied'] and len({(c.start, c.end) for c in main.clips}) == 3


def test_unlinked_or_overlong_moments_keep_recording_order():
    transcript = [Segment(0, 1, 'The date is real.'),
                  Segment(100, 101, 'The potato objects.'),
                  Segment(200, 201, 'The date comes back.')]
    selected = [moment('first', 0, 2, 10), moment('unrelated', 100, 102, 50),
                moment('last', 200, 202, 12)]
    plan = plan_story(selected, transcript, 60)
    assert plan['opening_id'] is None and plan['main_order'] == ['first', 'unrelated', 'last']
    assert plan['possible_topic_word'] == 'date'
    selected[1] = moment('long', 100, 175, 80)
    transcript[1] = Segment(100, 101, 'The date is real this time.')
    plan = plan_story(selected, transcript, 60)
    assert plan['opening_id'] is None


def test_profanity_alone_never_links_unrelated_conversations():
    transcript = [Segment(0, 2, 'The date claim is funny as fuck.'),
                  Segment(100, 102, 'The potato is a fucking lawyer.')]
    selected = [moment('date', 0, 4, 10), moment('potato', 100, 104, 50)]
    plan = plan_story(selected, transcript, 60)
    assert plan['possible_topic_word'] is None
    assert plan['opening_id'] is None


def test_opted_in_category_preference_can_change_opening_choice():
    transcript = [Segment(0, 1, 'The date is real.'),
                  Segment(100, 101, 'The date is a surprise.'),
                  Segment(200, 201, 'The date claim returns later.')]
    first = moment('first', 0, 3, 20)
    later = moment('later', 100, 103, 20)
    later['category'] = 'surprise'
    ending = moment('ending', 200, 203, 10)
    assert plan_story([first, later, ending], transcript, 60)['opening_id'] is None
    assert plan_story([first, later, ending], transcript, 60, {'surprise': 15})['opening_id'] == 'later'


def test_story_opening_cannot_reorder_approved_drafts_or_merged_ranges():
    media = Media('m', 'source.mp4', 30, 320, 180)
    selected = [moment('first', 0, 10, 10, 'approved'),
                moment('overlap', 8, 15, 30, 'approved')]
    try:
        assemble(media, 'source', selected, DraftOptions(opening_id='overlap'))
    except ValueError as error:
        assert 'automatic draft' in str(error)
    else:
        raise AssertionError('Approved draft order changed')
    try:
        assemble(media, 'source', selected, DraftOptions(opening_id='overlap'), 'automatic')
    except ValueError as error:
        assert 'overlaps another main range' in str(error)
    else:
        raise AssertionError('A merged range was promoted as a distinct opening')


def test_source_dialogue_bridge_adds_context_to_main_without_creating_a_short():
    transcript = [Segment(0, 2, 'The date is real.'),
                  Segment(3, 5, 'You are not on a date.'),
                  Segment(20, 22, 'I am on a date.'),
                  Segment(23, 25, 'Do you want to see the photo?'),
                  Segment(26, 27, 'Show it.'),
                  Segment(40, 42, 'That photo looks fake.'),
                  Segment(43, 45, 'The photo is real.')]
    selected = [moment('date', 0, 6, 20), moment('photo', 40, 46, 30)]
    bridges = find_context_bridges(selected, transcript, 'source', [], 5, 100, 60)
    assert len(bridges) == 1
    bridge = bridges[0]
    assert bridge['context_only'] and bridge['start'] <= 20 and bridge['end'] >= 27
    assert bridge['exchange']['source_ids'] == [2, 3, 4]
    media = Media('m', 'source.mp4', 60, 320, 180, transcript=transcript)
    main, shorts, details = assemble(media, 'source', selected + bridges,
                                     DraftOptions(), 'automatic')
    assert len(main.clips) == 3
    assert [identifier for identifier, _ in shorts] == ['date', 'photo']
    assert details['shorts_skipped'][0]['highlight'] == bridge['id']


def test_rejected_or_over_budget_context_is_not_added():
    transcript = [Segment(0, 2, 'The date is real.'),
                  Segment(20, 22, 'I am on a date.'),
                  Segment(23, 25, 'Look at this photo.'),
                  Segment(40, 42, 'The photo looks fake.')]
    selected = [moment('date', 0, 5, 20), moment('photo', 40, 45, 30)]
    arguments = (selected, transcript, 'source')
    assert not find_context_bridges(*arguments, [{'start': 21, 'end': 24}], 5, 100, 60)
    assert not find_context_bridges(*arguments, [], 2, 100, 60)
    assert not find_context_bridges(*arguments, [], 5, 11, 60)
