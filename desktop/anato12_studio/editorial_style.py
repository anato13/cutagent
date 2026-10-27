"""Optional, source-cited pacing choices for group-conversation edits."""

STYLE_DEFAULT = 'anato'
STYLE_GROUP_COMEDY = 'group_comedy'
STYLES = frozenset({STYLE_DEFAULT, STYLE_GROUP_COMEDY})
GROUP_CATEGORY_BONUS = {
    'banter': 12, 'misunderstanding': 12, 'callback': 10,
    'awkward': 8, 'argument': 7, 'surprise': 6,
}


def validate_style(style):
    if style not in STYLES:
        raise ValueError('Choose a supported Auto Edit pacing style.')
    return style


def selection_priority(item, preferences, style=STYLE_DEFAULT):
    """Approved decisions always outrank model guesses; bonuses remain modest."""
    validate_style(style)
    base = item['rank'] + preferences.get(item['category'], 0)
    if style == STYLE_GROUP_COMEDY and item['status'] != 'approved':
        base += GROUP_CATEGORY_BONUS.get(item['category'], 0)
        # Favor compact complete exchanges; never shorten an existing range.
        base += max(0, min(8, int((45 - (item['end'] - item['start'])) / 5)))
    return base


def plan_group_opening(selected, max_short_seconds, preferences=None, runner=None):
    """Choose one short, cited reaction as a cold open, or explain why none qualifies.

    Reaction labels originate with the local model and are still unverified.
    No source dialogue is cut, copied, or inferred here.
    """
    ordered = sorted((item for item in selected if not item.get('context_only')),
                     key=lambda item: (item['start'], item['end'], item['id']))
    reason = 'No short, independently understandable, source-cited reaction justified a cold open.'
    if len(ordered) < 3:
        reason = 'Fewer than three distinct selected exchanges; keep recording order.'
    else:
        first = ordered[0]
        eligible = []
        for item in ordered[1:-1]:
            if runner:
                runner.check()
            exchange = item.get('exchange') or {}
            roles = exchange.get('roles') or {}
            reaction = roles.get('reaction') or []
            if (item['status'] != 'unreviewed' or exchange.get('reference_check') != 'passed'
                    or exchange.get('needs_context') or not reaction
                    or item['end'] - item['start'] > min(30, max_short_seconds)
                    or any(item['start'] < other['end'] and item['end'] > other['start']
                           for other in ordered if other['id'] != item['id'])):
                continue
            eligible.append(item)
        if eligible:
            preferences = preferences or {}
            best = max(eligible, key=lambda item: (
                selection_priority(item, preferences, STYLE_GROUP_COMEDY), -item['start']))
            if (first['status'] != 'approved' and
                    selection_priority(best, preferences, STYLE_GROUP_COMEDY) >=
                    selection_priority(first, preferences, STYLE_GROUP_COMEDY) + 10):
                return {'opening_id': best['id'],
                        'source_reaction_ids': [row['id'] for row in best['exchange']['roles']['reaction']],
                        'reason': ('A short complete exchange has a higher group-comedy review priority '
                                   'and a source-cited model reaction. Review that reaction before publishing.'),
                        'reaction_meaning': 'NOT_EVALUATED'}
            reason = 'The first selected exchange has comparable or higher review priority.'
    return {'opening_id': None, 'source_reaction_ids': [], 'reason': reason,
            'reaction_meaning': 'NOT_EVALUATED'}
