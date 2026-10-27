"""Check dialogue references and expose evidence without certifying model interpretations."""
import json

from .model import timestamp


ROLES = ('setup_ids', 'payoff_ids', 'reaction_ids')


def validate_structure(value, allowed):
    if not isinstance(value, dict):
        raise ValueError('Missing setup/payoff map; analyze this recording again.')
    first, last = value.get('first_id'), value.get('last_id')
    if (type(first) is not int or type(last) is not int or first not in allowed or last not in allowed
            or first > last or type(value.get('needs_context')) is not bool):
        raise ValueError('Invalid exchange boundaries or missing context assessment.')
    roles = {}
    for role in ROLES:
        ids = value.get(role)
        if (not isinstance(ids, list) or len(ids) > 8 or (role != 'reaction_ids' and not ids)
                or any(type(i) is not int or i not in allowed for i in ids)
                or len(set(ids)) != len(ids)):
            raise ValueError(f'Invalid or missing {role}; use supplied transcript IDs.')
        roles[role] = sorted(ids)
    if max(roles['setup_ids']) >= min(roles['payoff_ids']):
        raise ValueError('Setup must precede the payoff on distinct transcript lines.')
    if roles['reaction_ids'] and min(roles['reaction_ids']) <= max(roles['payoff_ids']):
        raise ValueError('Reaction references must follow the payoff.')
    if any(i < first or i > last for role in ('payoff_ids', 'reaction_ids') for i in roles[role]):
        raise ValueError('The selected range omits a cited payoff or reaction.')
    if any(i > last for i in roles['setup_ids']):
        raise ValueError('The selected range ends before its setup.')
    return {'version': 1, 'first_id': first, 'last_id': last, **roles,
            'needs_context': value['needs_context']}


def quote_title(structure, allowed):
    def snippet(identifier):
        text = ' '.join(allowed[identifier]['text'].split())
        return text[:62] + ('…' if len(text) > 62 else '')
    return f'“{snippet(structure["setup_ids"][0])}” → “{snippet(structure["payoff_ids"][0])}”'


def exchange_evidence(item, rows):
    """Bind saved evidence and roles to the current transcript, never just old IDs."""
    evidence = json.loads(item['evidence'])
    if not isinstance(evidence, list) or not evidence:
        raise ValueError('Evidence no longer matches this transcript.')
    actual = {r['id']: r for r in rows}
    if any(not isinstance(e, dict) or type(e.get('id')) is not int or actual.get(e['id']) != e
           for e in evidence):
        raise ValueError('Evidence no longer matches this transcript.')
    structure = json.loads(item.get('structure', '{}'))
    if (not isinstance(structure, dict) or type(structure.get('version')) is not int
            or structure['version'] != 1):
        raise ValueError('Missing setup/payoff map; analyze this recording again.')
    checked = validate_structure(structure, actual)
    cited = {r['id'] for r in evidence}
    if any(i not in cited for role in ROLES for i in checked[role]):
        raise ValueError('Setup/payoff/reaction references lack matching source evidence.')
    return {**checked, 'roles': {role.removesuffix('_ids'): [actual[i] for i in checked[role]] for role in ROLES},
            'reference_check': 'passed', 'semantic_quality': 'NOT_EVALUATED'}


def describe_exchange(item):
    """UI text always labels interpretations; legacy examples remain reviewable."""
    try:
        structure = json.loads(item.get('structure', '{}'))
        if not isinstance(structure, dict):
            raise ValueError('Invalid exchange map')
        evidence = json.loads(item['evidence'])
        allowed = {r['id']: r for r in evidence}
        # Endpoints may not be evidence lines; the UI does not certify them here.
        lines = ['Model-suggested roles (meaning has not been verified):']
        for role in ROLES:
            ids = structure.get(role, [])
            if not isinstance(ids, list) or any(type(i) is not int or i not in allowed for i in ids):
                raise ValueError('Invalid role references')
            title = role.removesuffix('_ids').title()
            lines.append(title + ':')
            lines.extend(f'  {timestamp(allowed[i]["start"])} · {allowed[i]["text"]}' for i in ids)
            if not ids:
                lines.append('  Not supplied')
        if not structure:
            return 'Legacy suggestion: reanalyze to obtain setup/payoff references.'
        score = structure.get('subjective_humor_score')
        if type(score) is int and 1 <= score <= 5:
            lines.append(f'Model taste estimate: {score}/5 (subjective, unverified)')
        lines.append('Additional context requested by model: ' + str(structure.get('needs_context')))
        return '\n'.join(lines)
    except (TypeError, ValueError, KeyError):
        return 'Exchange evidence could not be read; reanalyze this recording.'
