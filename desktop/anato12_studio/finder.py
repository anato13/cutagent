"""Absolute-time analysis windows, evidence validation and real transcript search."""
from dataclasses import dataclass, field
import bisect
import hashlib
import json
import re
from .model_context import bounded_windows, HIGHLIGHT_CATEGORIES, PROMPT_VERSION
from .model_policy import context_tokens
from .exchange import ROLES, quote_title, validate_structure


ANALYSIS_VERSION = "finder-personal-style-3"
CATEGORIES = set(HIGHLIGHT_CATEGORIES)


@dataclass
class Proposal:
    start: float
    end: float
    title: str
    category: str
    reason: str
    evidence: list[dict]
    rank: float
    method: str
    structure: dict = field(default_factory=dict)


def rows_for(segments):
    return [{"id": i, "start": s.start, "end": s.end, "text": s.text}
            for i, s in enumerate(sorted(segments, key=lambda s: s.start))]


def windows(rows, length=90, overlap=30):
    if length <= 0 or not 0 <= overlap < length:
        raise ValueError("Invalid analysis window settings.")
    starts = [r["start"] for r in rows]
    index = 0
    while index < len(rows):
        end = bisect.bisect_left(starts, starts[index] + length)
        yield rows[index:max(index+1, end)]
        if end == len(rows):
            break
        index = max(index + 1, bisect.bisect_left(starts, starts[index] + length - overlap))


def callbacks(rows):
    seen, result = {}, {}
    stop = {"the", "a", "an", "i", "you", "we", "they", "is", "are", "to", "of", "and", "it",
            "i'm", "on", "in", "that", "this", "was", "be", "my", "your", "it's", "so"}
    for row in rows:
        words = re.findall(r"[a-z0-9']+", row["text"].casefold())
        for i in range(len(words)-3):
            phrase = " ".join(words[i:i+4])
            if len(set(words[i:i+4]) - stop) < 2:
                continue
            if phrase in seen:
                old = seen[phrase]
                if row["start"] - old["start"] >= 60:
                    result.setdefault(row["id"], []).append(old)
            else:
                seen[phrase] = row
    return result


def proposal(first, last, evidence, duration, category, reason, rank, method, title=None):
    start, end = max(0, first["start"]-4), min(duration, last["end"]+5)
    if end <= start or end-start > 90:
        return None
    return Proposal(start, end, (title or first["text"][:85]).strip()[:180], category, reason,
                    evidence, rank, method)


def context_cues(window, repeats, duration):
    """Fallback requires combined context cues; never treat volume/profanity as humor."""
    result = []
    for i, row in enumerate(window):
        context = window[max(0, i-2):min(len(window), i+2)]
        if len(context) < 2:
            continue
        text = " ".join(r["text"] for r in context).casefold()
        surprise = bool(re.search(r"\b(no way|wait what|are you serious|are you kidding|what just happened)\b", text))
        question = "?" in text
        contradiction = bool(re.search(r"\b(no|not|actually|isn't|wasn't|didn't|but)\b", text))
        reaction = bool(re.search(r"\b(laughing|laughs|laughter|oh my god|oh my gosh)\b", text))
        repeated = repeats.get(row["id"], [])
        if repeated:
            category, reason, rank = "callback", "Repeated phrase at least 60 seconds earlier; review whether it is a callback.", 5
            evidence = context + repeated[:2]
        elif question and contradiction and (surprise or reaction):
            category, reason, rank = "misunderstanding", "Question, contrasting reply and reaction occur in the same context.", 4
            evidence = context
        elif surprise and reaction:
            category, reason, rank = "surprise", "A surprised phrase and reaction marker share conversational context.", 3
            evidence = context
        else:
            continue
        item = proposal(context[0], context[-1], evidence, duration, category, reason, rank, "context cues")
        if item:
            result.append(item)
    return result


def model_proposals(raw, window, repeats, duration, rejections=None):
    current = {r["id"]: r for r in window}
    allowed = dict(current)
    for rows in repeats.values():
        allowed.update({r["id"]: r for r in rows})
    proposals = []
    for index, item in enumerate(raw):
        def reject(reason):
            if rejections is not None:
                rejections.append({'proposal': index + 1, 'reason': reason})
        if not isinstance(item, dict):
            reject('The proposal is not a structured clip.')
            continue
        first, last = item.get("first_id"), item.get("last_id")
        ids = item.get("evidence_ids", [])
        if (type(first) is not int or type(last) is not int or first not in current or last not in current
                or first > last or not isinstance(ids, list)
                or any(type(i) is not int or i not in allowed for i in ids)):
            reject('The clip boundaries or evidence IDs are not in this transcript section.')
            continue
        try:
            structure = validate_structure(item, allowed)
        except ValueError as error:
            reject(str(error))
            continue
        # Role IDs are themselves citations. Copy their real source rows instead of
        # requiring the model to repeat every citation in a redundant second list.
        role_ids = {i for role in ROLES for i in structure[role]}
        structure['role_evidence_added'] = sorted(role_ids - set(ids))
        ids = sorted(set(ids) | role_ids)
        category = item.get("category", "other")
        score = item.get('subjective_humor_score', 3)
        if type(score) is not int or not 1 <= score <= 5:
            reject('The model supplied an invalid subjective score.')
            continue
        if not isinstance(category, str) or category not in CATEGORIES:
            category = "other"
        # All displayed quotes/timestamps are copied from actual supplied segments.
        evidence = [allowed[i] for i in dict.fromkeys(ids)]
        candidate = proposal(current[first], current[last], evidence, duration, category,
                             str(item.get("reason", ""))[:1500], score*10-index, "local model order",
                             quote_title(structure, allowed))
        if candidate:
            candidate.structure = {**structure, 'model_title': str(item.get('title', ''))[:180],
                                   'subjective_humor_score': score}
            proposals.append(candidate)
        else:
            reject('The selected clip exceeds 90 seconds or falls outside the recording.')
    return proposals


def deduplicate(items):
    selected = []
    for item in sorted(items, key=lambda p: (-p.rank, p.start)):
        duplicate = any(
            max(0, min(item.end, old.end)-max(item.start, old.start)) >
            min(item.end-item.start, old.end-old.start)*.5 for old in selected)
        if not duplicate:
            selected.append(item)
    return sorted(selected, key=lambda p: (-p.rank, p.start))[:100]


def literal_search(rows, query, duration):
    stop = {"find", "the", "a", "an", "when", "where", "my", "friend", "everyone", "me", "that",
            "is", "was", "on", "of", "and", "to", "for", "moments", "conversation", "most"}
    terms = set(re.findall(r"[a-z0-9']+", query.casefold())) - stop
    if not terms:
        return []
    result = []
    for i, row in enumerate(rows):
        normalized = row["text"].casefold()
        matches = sorted(t for t in terms if re.search(r"\b" + re.escape(t) + r"\b", normalized) or
                         (t in {"laughing", "laughter", "laughs"} and re.search(r"\blaugh\w*\b", normalized)))
        if not matches:
            continue
        context = rows[max(0, i-1):min(len(rows), i+2)]
        item = proposal(context[0], context[-1], context, duration, "other",
                        "Transcript matches: " + ", ".join(matches) + ". This is literal search, not proof of a story claim.",
                        len(matches), "literal search", row["text"][:85])
        if item:
            result.append(item)
    return deduplicate(result)


def analyze(store, source, segments, duration, runner, progress, model=None, query="", diagnostics=None,
            allow_partial=False, personal_notes=None, coverage=False, coverage_target=3):
    if type(coverage_target) is not int or coverage_target < 1 or coverage_target > 100:
        raise ValueError('The requested number of distinct moments must be between 1 and 100.')
    for s in segments:
        s.validate(duration)
    rows = rows_for(segments)
    long_lines = sum(r['end'] - r['start'] >= 15 for r in rows)
    coarse_hint = (f' {long_lines} of {len(rows)} transcript lines last at least 15 seconds; '
                   're-transcribe or import phrase-timestamped SRT lines.'
                   if long_lines >= max(2, len(rows)//4) else '')
    if diagnostics is not None:
        diagnostics.update(lines=len(rows), windows=0, returned=0, valid=0, invalid_sections=[],
                           mode='local Ollama' if model else 'context cues',
                           model_eval_count=0, model_eval_duration=0,
                           coverage_windows=0, coverage_added=0, coverage_empty=0,
                           long_lines=long_lines, rejection_reasons=[])
    if not rows:
        return []
    transcript_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    store.cache_put(f"analysis-transcript:{source}", source, "analysis_transcript", [vars(s) for s in segments])
    if query and model is None:
        candidates = literal_search(rows, query, duration)
    else:
        repeated = callbacks(rows)
        candidates = []
        preferences = store.model_preferences() if model else store.preferences()
        if model and personal_notes:
            preferences = {**preferences, "confirmed_personal_notes": personal_notes}
        if diagnostics is not None and model:
            diagnostics['personal_notes'] = len(personal_notes or [])
        chunks = list(bounded_windows(rows, repeated, query, preferences, runner)) if model else list(windows(rows))
        invalid_sections = []
        for i, chunk in enumerate(chunks):
            runner.check()
            if diagnostics is not None:
                diagnostics['windows'] += 1
            window = chunk.rows if model else chunk
            relevant = chunk.callbacks if model else {
                r["id"]: repeated[r["id"]][:2] for r in window if r["id"] in repeated}
            if model:
                identity = model.identity(runner)
                signature = json.dumps([ANALYSIS_VERSION, source, transcript_hash, window[0]["id"],
                                        window[-1]["id"], relevant, PROMPT_VERSION,
                                        model.base, model.model, context_tokens(model.model),
                                        identity, query, preferences], sort_keys=True)
                key = "analysis:" + hashlib.sha256(signature.encode()).hexdigest()
                raw = store.cache_get(key)
                fresh = raw is None
                if raw is None:
                    raw = model.analyze(window, relevant, query, preferences, runner)
                    if diagnostics is not None:
                        metrics = getattr(model, 'last_metrics', {})
                        diagnostics['model_eval_count'] += metrics.get('eval_count', 0)
                        diagnostics['model_eval_duration'] += metrics.get('eval_duration', 0)
                    if model.identity(runner) != identity:
                        raise ValueError("The local model changed during analysis. Retry with a stable model.")
                rejections = []
                valid = model_proposals(raw, window, relevant, duration, rejections)
                if diagnostics is not None:
                    diagnostics['returned'] += len(raw)
                    diagnostics['valid'] += len(valid)
                    diagnostics['rejection_reasons'].extend(
                        {'section': i+1, **reason} for reason in rejections)
                if raw and not valid:
                    issue = {'section': i+1, 'start': window[0]['start'],
                             'end': window[-1]['end'], 'rejected_proposals': len(raw)}
                    invalid_sections.append(issue)
                    if diagnostics is not None:
                        diagnostics['invalid_sections'].append(issue)
                    if not allow_partial:
                        raise ValueError(f"The model proposed clips in section {i+1}/{len(chunks)} "
                                         f"({issue['start']:.1f}–{issue['end']:.1f}s) "
                                         "without valid source evidence. "
                                         "Each needs ordered setup/payoff references and a context assessment. "
                                         "Try another model or review the transcript; this is not a no-match result."
                                         + (f" First issue: {rejections[0]['reason']}" if rejections else '')
                                         + coarse_hint)
                    progress((i+1)/len(chunks) * (.7 if coverage and model and not query else 1),
                             f"Skipping invalid model section {i+1}/{len(chunks)}")
                    continue  # Never cache an all-invalid section as a no-match.
                if fresh:
                    store.cache_put(key, source, "analysis_window", raw)
                candidates.extend(valid)
            else:
                candidates.extend(context_cues(window, relevant, duration))
            progress((i+1)/len(chunks) * (.7 if coverage and model and not query else 1),
                     f"Analyzing context window {i+1}/{len(chunks)}")
        if invalid_sections and not candidates and not (model and coverage and not query):
            first = invalid_sections[0]
            raise ValueError(f"The model gave invalid source references in {len(invalid_sections)} "
                             f"of {len(chunks)} sections, starting at {first['start']:.1f}–{first['end']:.1f}s. "
                             "No validated candidates remain. Review the transcript or try another local model."
                             + (f" First issue: {diagnostics['rejection_reasons'][0]['reason']}"
                                if diagnostics and diagnostics['rejection_reasons'] else '')
                             + coarse_hint)
        first_pass_invalid = len(invalid_sections)
        candidates = deduplicate(candidates)
        if model and coverage and not query and len(candidates) < coverage_target:
            # Review still-uncovered conversations, without treating a requested
            # number of clips as a quota. Every addition must pass the same source
            # citation and exchange validation as the first pass.
            extra_chunks = list(bounded_windows(rows, repeated, query, preferences, runner, focus="coverage"))
            def excluded(chunk):
                return tuple(r['id'] for r in chunk.rows if any(
                    r['id'] >= item.structure['first_id'] and r['id'] <= item.structure['last_id']
                    for item in candidates))
            extra_chunks.sort(key=lambda chunk: (len(excluded(chunk)), chunk.rows[0]['start']))
            for i, chunk in enumerate(extra_chunks):
                runner.check()
                if len(candidates) >= coverage_target:
                    break
                blocked = excluded(chunk)
                if len(chunk.rows) - len(blocked) < 2:
                    continue
                window, relevant = chunk.rows, chunk.callbacks
                identity = model.identity(runner)
                signature = json.dumps([ANALYSIS_VERSION, source, transcript_hash, window[0]['id'],
                                        window[-1]['id'], relevant, PROMPT_VERSION, 'coverage', blocked,
                                        model.base, model.model, context_tokens(model.model), identity,
                                        preferences], sort_keys=True)
                key = 'analysis:' + hashlib.sha256(signature.encode()).hexdigest()
                raw = store.cache_get(key)
                fresh = raw is None
                if fresh:
                    raw = model.analyze(window, relevant, query, preferences, runner,
                                        focus='coverage', excluded_ids=blocked)
                    if diagnostics is not None:
                        metrics = getattr(model, 'last_metrics', {})
                        diagnostics['model_eval_count'] += metrics.get('eval_count', 0)
                        diagnostics['model_eval_duration'] += metrics.get('eval_duration', 0)
                    if model.identity(runner) != identity:
                        raise ValueError('The local model changed during coverage analysis. Retry with a stable model.')
                rejections = []
                valid = model_proposals(raw, window, relevant, duration, rejections)
                if diagnostics is not None:
                    diagnostics['coverage_windows'] += 1
                    diagnostics['returned'] += len(raw)
                    diagnostics['valid'] += len(valid)
                    diagnostics['rejection_reasons'].extend(
                        {'section': f'coverage {i+1}', **reason} for reason in rejections)
                    if not raw:
                        diagnostics['coverage_empty'] += 1
                if raw and not valid:
                    issue = {'section': f'coverage {i+1}', 'start': window[0]['start'],
                             'end': window[-1]['end'], 'rejected_proposals': len(raw)}
                    invalid_sections.append(issue)
                    if diagnostics is not None:
                        diagnostics['invalid_sections'].append(issue)
                    # Preserve earlier validated moments while reporting the
                    # sections that could not be trusted.
                    if not allow_partial:
                        raise ValueError(f"Coverage review at {issue['start']:.1f}–{issue['end']:.1f}s "
                                         'returned invalid source evidence. Try another model or review the transcript.'
                                         + (f" First issue: {rejections[0]['reason']}" if rejections else ''))
                    progress(.7 + .3 * (i+1)/len(extra_chunks),
                             f"Skipping invalid second review {i+1}/{len(extra_chunks)}")
                    continue
                if fresh:
                    store.cache_put(key, source, 'analysis_window', raw)
                for item in valid:
                    if any(old.structure['first_id'] <= item.structure['last_id'] and
                           old.structure['last_id'] >= item.structure['first_id']
                           for old in candidates):
                        continue
                    merged = deduplicate(candidates + [item])
                    if item in merged and len(merged) > len(candidates):
                        candidates = merged
                        if diagnostics is not None:
                            diagnostics['coverage_added'] += 1
                progress(.7 + .3 * (i+1)/len(extra_chunks),
                         f"Reviewing distinct dialogue {i+1}/{len(extra_chunks)}")
        if invalid_sections and not candidates:
            first = invalid_sections[0]
            raise ValueError(f"The model gave invalid source references in {first_pass_invalid} "
                             f"of {len(chunks)} first-pass sections and "
                             f"{len(invalid_sections) - first_pass_invalid} second-pass sections, "
                             f"starting at {first['start']:.1f}–{first['end']:.1f}s. "
                             "No validated candidates remain. Review the transcript or try another local model."
                             + (f" First issue: {diagnostics['rejection_reasons'][0]['reason']}"
                                if diagnostics and diagnostics['rejection_reasons'] else '')
                             + coarse_hint)
    identifiers = []
    for item in candidates:
        runner.check()
        signature = hashlib.sha256(json.dumps(
            [item.method, query.casefold(), round(item.start, 2), round(item.end, 2)]).encode()).hexdigest()
        excerpt = "\n".join(r["text"] for r in rows if r["end"] > item.start and r["start"] < item.end)
        identifiers.append(store.upsert_highlight(source, signature, item.start, item.end, item.title,
                           item.category, item.reason, excerpt, item.evidence, item.method, item.rank, item.structure))
    return identifiers
