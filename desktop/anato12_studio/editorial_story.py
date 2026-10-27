"""Source-grounded story-opening heuristic for complete, validated exchanges."""
import hashlib
import math
import re

from .finder import rows_for


PLAYBOOK_VERSION = 'anato-first-edit-1'
PLAYBOOK = (
    'Find a recurring conversation or claim rather than joining unrelated loud moments.',
    'Keep each selected exchange complete: setup, turn or payoff, and any real reaction.',
    'Keep a brief source-dialogue bridge when it may connect two selected moments.',
    'Open with a short, understandable moment only when source dialogue links it to the rest.',
    'Use the remaining moments in recording order; do not repeat the opening later.',
    'Treat an ending as a payoff only after playback confirms it, not because a word repeats.',
)
STOP_WORDS = frozenset('''about after again ain't also because been before being bro brother could
didn't does don't dude everyone friend from game gonna gotta have here just know like literally
maybe more never okay only over people real really said some something still sure than that their
them then there these they thing think this those through time what when where which while
who's with would yeah your you're thats fucking fuck shit damn hell'''.split())


def _words(spoken):
    return {word for word in re.findall(r"[a-z][a-z0-9']{3,}", spoken.casefold())
            if word not in STOP_WORDS and not word.isdigit()}


def _terms(item, rows):
    spoken = ' '.join(row['text'] for row in rows
                      if row['end'] > item['start'] and row['start'] < item['end'])
    return _words(spoken)


def find_context_bridges(selected, segments, source, rejected, max_ranges, max_main_seconds,
                         duration, runner=None):
    """Find a short real-dialogue link between adjacent selected exchanges.

    A bridge is source context, not a humor candidate, and never becomes a Short.
    Both anchor words must already occur in selected clips; nearby source lines
    must contain them in order. This is lexical evidence, not semantic proof.
    """
    ordered = sorted(selected, key=lambda item: (item['start'], item['end']))
    rows = rows_for(segments)
    term_sets = {item['id']: _terms(item, rows) for item in ordered}
    bridges = []
    for left, right in zip(ordered, ordered[1:]):
        if runner:
            runner.check()
        if len(ordered) + len(bridges) >= max_ranges or not left['end'] < right['start']:
            continue
        if right['start'] - left['end'] > 180 or term_sets[left['id']] & term_sets[right['id']]:
            continue
        gap = [row for row in rows if row['start'] >= left['end'] and row['end'] <= right['start']]
        if not gap:
            continue
        choices = []
        for i, first in enumerate(gap):
            if runner and i % 32 == 0:
                runner.check()
            earlier = _words(first['text']) & term_sets[left['id']]
            if not earlier:
                continue
            for j in range(i, min(i+4, len(gap))):
                if gap[j]['end'] - first['start'] > 20:
                    break
                later = _words(gap[j]['text']) & term_sets[right['id']]
                if later:
                    choices.append((gap[j]['end'] - first['start'], i, j,
                                    sorted(earlier)[0], sorted(later)[0]))
        if not choices:
            continue
        _, i, j, earlier_word, later_word = min(choices)
        end_index = j
        if j + 1 < len(gap) and gap[j+1]['start'] - gap[j]['end'] <= 4 and (
                gap[j+1]['end'] - gap[i]['start'] <= 25):
            end_index += 1  # Keep one immediate response when the transcript has one.
        evidence = gap[i:end_index+1]
        start = max(left['end'], math.floor(evidence[0]['start'] * 30 + 1e-7) / 30)
        end = min(right['start'], duration, math.ceil(evidence[-1]['end'] * 30 - 1e-7) / 30)
        if (end <= start or end-start > 25 or
                any(old['start'] < end and old['end'] > start for old in rejected) or
                any(old['start'] < end and old['end'] > start for old in bridges)):
            continue
        if sum(item['end'] - item['start'] for item in ordered + bridges) + end-start > max_main_seconds:
            continue
        identifier = 'bridge-' + hashlib.sha256(
            f"{source}:{evidence[0]['id']}:{evidence[-1]['id']}".encode()).hexdigest()[:24]
        bridges.append({'id': identifier, 'source': source, 'start': start, 'end': end,
                        'title': 'Context: ' + evidence[0]['text'].strip()[:70],
                        'category': 'other', 'status': 'unreviewed', 'rank': -1,
                        'method': 'source dialogue bridge', 'context_only': True,
                        'original_range': [evidence[0]['start'], evidence[-1]['end']],
                        'reason': (f'Source lines repeat “{earlier_word}” from the earlier clip '
                                   f'and “{later_word}” from the later clip; relevance needs playback review.'),
                        'evidence': evidence,
                        'exchange': {'reference_check': 'source_lines',
                                     'source_ids': [row['id'] for row in evidence],
                                     'semantic_quality': 'NOT_EVALUATED'}})
    return bridges


def plan_story(selected, segments, max_short_seconds, preferences=None, runner=None):
    """Suggest one source-linked opening; never infer a semantic payoff or invent a cut."""
    if runner:
        runner.check()
    ordered = sorted(selected, key=lambda item: (item['start'], item['end'], item['id']))
    rows = rows_for(segments)
    terms = {item['id']: _terms(item, rows) for item in ordered}
    occurrences = {}
    for item in ordered:
        if runner:
            runner.check()
        for word in terms[item['id']]:
            occurrences.setdefault(word, []).append(item)
    linked = {word: items for word, items in occurrences.items() if len(items) >= 2}
    # A recurrence across a wider source span is a possible story thread, not
    # proof that the conversations are about the same event.
    topic = (max(linked, key=lambda word: (len(linked[word]),
              linked[word][-1]['start'] - linked[word][0]['start'], len(word), word))
             if linked else None)
    opening_id, reason = None, 'No repeated source-dialogue topic justified moving an opening.'
    if topic and len(ordered) > 1:
        preferences = preferences or {}
        earliest = ordered[0]
        def priority(item):
            return (item['status'] == 'approved',
                    item['rank'] + preferences.get(item['category'], 0))
        eligible = [item for item in linked[topic]
                    if not item.get('context_only')
                    and any(other['start'] >= item['end'] and not other.get('context_only')
                            for other in ordered)
                    and item['end'] - item['start'] <= min(45, max_short_seconds)
                    and all(item['end'] <= other['start'] or item['start'] >= other['end']
                            for other in ordered if other['id'] != item['id'])]
        if eligible:
            best = max(eligible, key=lambda item: (priority(item), -item['start']))
            higher = (best['status'] == 'approved' and earliest['status'] != 'approved' or
                      best['status'] == earliest['status'] and
                      priority(best)[1] >= priority(earliest)[1] + 10)
            if best['id'] != earliest['id'] and higher:
                opening_id = best['id']
                reason = ('A short, complete selected exchange has higher review priority and '
                          f'repeats the source word “{topic}” in another selected moment.')
            else:
                reason = 'The first complete selected exchange already has comparable review priority.'
        else:
            reason = 'No short, independent exchange on the repeated topic fits the opening limit.'
    planned = ([opening_id] + [item['id'] for item in ordered if item['id'] != opening_id]
               if opening_id else [item['id'] for item in ordered])
    return {'version': PLAYBOOK_VERSION, 'method': 'repeated source words and review priority',
            'principles': PLAYBOOK, 'possible_topic_word': topic,
            'linked_moments': [item['id'] for item in linked[topic]] if topic else [],
            'opening_id': opening_id, 'main_order': planned, 'reason': reason,
            'ending_payoff': 'NOT_EVALUATED', 'humor_quality': 'NOT_EVALUATED',
            'scope': 'Heuristic ordering only; inspect playback before publishing.'}
