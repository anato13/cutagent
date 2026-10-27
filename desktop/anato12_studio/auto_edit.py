"""Experimental unattended selection with conservative boundaries and checked exports."""
import copy
from dataclasses import dataclass
import json
import math
from pathlib import Path
import time

from .drafts import DraftOptions, create_bundle
from .editorial_story import find_context_bridges, plan_story
from .editorial_style import (STYLE_DEFAULT, STYLE_GROUP_COMEDY, plan_group_opening,
                              selection_priority, validate_style)
from .exchange import exchange_evidence
from .finder import rows_for
from .finder_jobs import run_pipeline
from .local_model import LocalModel
from .model import Clip, number
from .quality import ensure_capabilities, verify_bundle
from .store import fingerprint
from .video import Cancelled


@dataclass
class AutoOptions:
    max_main_seconds: float = 600
    max_ranges: int = 5
    max_short_seconds: float = 60
    burn_captions: bool = False
    save_srt: bool = False

    def validate(self):
        self.max_main_seconds = number(self.max_main_seconds, 1, 7200, 'Main video limit')
        self.max_short_seconds = number(self.max_short_seconds, 1, 180, 'Maximum Short length')
        if type(self.max_ranges) is not int or not 1 <= self.max_ranges <= 20:
            raise ValueError('Choose between 1 and 20 complete ranges.')
        DraftOptions(self.max_short_seconds, burn_captions=self.burn_captions,
                     save_srt=self.save_srt).validate()


def union_duration(items):
    ranges = sorted(Clip('', h['start'], h['end']).frame_range() for h in items)
    total, previous_end = 0, 0
    for start, duration in ranges:
        end = start + duration
        total += max(0, end - max(start, previous_end))
        previous_end = max(previous_end, end)
    return total


def fits_short(item, options):
    return Clip('', item['start'], item['end']).frame_range()[1] <= options.max_short_seconds + .00001


def select_ranges(media, source, candidates, rejected, preferences, options, runner=None,
                  editing_style=STYLE_DEFAULT):
    """No fabricated approvals; reject stale evidence and absent callback setup."""
    validate_style(editing_style)
    def check():
        if runner is not None:
            runner.check()

    check()
    options.validate()
    for segment in media.transcript:
        check()
        copy.copy(segment).validate(media.duration)
    rows = rows_for(media.transcript)
    eligible, skipped = [], []
    ordered = sorted(candidates, key=lambda h: (h['status'] != 'approved',
        -selection_priority(h, preferences, editing_style), h['start'], h['id']))
    for candidate in ordered:
        check()
        item = copy.deepcopy(candidate)
        reason = ''
        if item['source'] != source or item['status'] not in {'approved', 'unreviewed'}:
            reason = 'Wrong source or rejected decision'
        elif item['status'] != 'approved':
            if item['method'] != 'local model order':
                reason = 'Unreviewed cue/search results are not autonomous model selections'
            else:
                try:
                    item['exchange'] = exchange_evidence(item, rows)
                    if item['exchange']['needs_context']:
                        reason = 'The model requested additional context; do not export this exchange unattended'
                    elif any(e['start'] < item['start'] or e['end'] > item['end']
                             for e in json.loads(item['evidence'])):
                        reason = 'Required setup/callback evidence is outside the selected range'
                except (ValueError, TypeError, KeyError) as error:
                    reason = str(error) or 'Invalid transcript evidence'
        else:
            item['exchange'] = {'reference_check': 'human_approved', 'semantic_quality': 'NOT_EVALUATED'}
        if not reason:
            try:
                clip = Clip(media.id, item['start'], item['end'])
                clip.validate(media)
                item['start'], item['end'] = clip.start, clip.end
                # Extend, never cut off a transcript line intersecting either boundary.
                # Frame-aligned outer bounds prevent rounding into a line.
                changed = True
                while changed:
                    check()
                    a, b = item['start'], item['end']
                    for i, row in enumerate(rows):
                        if i % 256 == 0:
                            check()
                        if row['end'] > a and row['start'] < b:
                            item['start'] = min(item['start'], row['start'])
                            item['end'] = max(item['end'], row['end'])
                    item['start'] = max(0, math.floor(item['start'] * 30 + 1e-7) / 30)
                    item['end'] = min(media.duration, math.ceil(item['end'] * 30 - 1e-7) / 30)
                    changed = (a, b) != (item['start'], item['end'])
                    if item['end'] - item['start'] > 90:
                        reason = 'Whole dialogue exceeds the 90-second selection limit'
                        break
                if any(r['start'] < item['end'] and r['end'] > item['start'] for r in rejected):
                    reason = 'Overlaps a range you rejected'
            except (ValueError, TypeError):
                reason = 'Invalid source boundaries'
        if reason:
            skipped.append({'highlight': item['id'], 'reason': reason})
        else:
            item['original_range'] = [candidate['start'], candidate['end']]
            eligible.append(item)

    def choose(reserved=None):
        chosen = [reserved] if reserved is not None else []
        excluded = []
        for item in eligible:
            check()
            if item is reserved:
                continue
            if any(h['start'] <= item['start'] and h['end'] >= item['end'] for h in chosen):
                reason = 'Already covered by a selected range'
            elif any(max(0, min(h['end'], item['end']) - max(h['start'], item['start'])) >
                     .5 * min(h['end']-h['start'], item['end']-item['start']) for h in chosen):
                reason = 'Expanded dialogue substantially overlaps an already selected exchange'
            elif (len(chosen) >= options.max_ranges or
                  union_duration(chosen + [item]) > options.max_main_seconds + .00001):
                reason = 'Would exceed the selected budget; dialogue was not truncated'
            else:
                chosen.append(item)
                continue
            if reserved is not None:
                reason += '; space reserved for a complete Short'
            excluded.append({'highlight': item['id'], 'reason': reason})
        return chosen, excluded

    chosen, excluded = choose()
    if not any(fits_short(h, options) for h in chosen):
        # Preserve the ordinary ranking whenever it can produce both formats.
        # Otherwise reserve the highest-priority eligible Short, then refill the
        # remaining budget. Never truncate a long exchange just to make a Short.
        for item in eligible:
            check()
            if fits_short(item, options) and union_duration([item]) <= options.max_main_seconds + .00001:
                chosen, excluded = choose(item)
                break
    check()
    return sorted(chosen, key=lambda h: (h['start'], h['end'])), skipped + excluded


def run_auto_edit(store, source, media, params, job_id, ffmpeg, ffprobe, runner, progress):
    options = AutoOptions(**params['auto_options'])
    current = [0.0, 0.0]
    def report(value, message):
        current[0] = max(current[0], value)
        progress(current[0], message)
        if time.monotonic() - current[1] > .5:
            store.update_job(job_id, 'running', current[0], message)
            current[1] = time.monotonic()
    store.update_job(job_id, 'running', 0, 'Starting Auto Edit')
    try:
        options.validate()
        editing_style = validate_style(params.get('editing_style', STYLE_DEFAULT))
        if not params.get('contextual') or not params.get('model') or params.get('transcribe_only'):
            raise ValueError('Auto Edit needs an explicitly selected local model in AI Clip Finder.')
        runner.check()
        if not Path(params['output_parent']).is_dir():
            raise ValueError('The output folder is unavailable. Choose an existing folder for a new run.')
        if fingerprint(media.path) != source:
            raise ValueError('The source changed. Import it again before Auto Edit.')
        client = LocalModel(params['url'], params['model'])
        identity = client.identity(runner)
        result = run_pipeline(store, source, media, params, job_id, ffmpeg, runner,
                              lambda v, m: report(v*.45, m), track_job=False)
        if client.identity(runner) != identity:
            raise ValueError('The local model changed during Auto Edit. Rerun with a stable model.')
        media = copy.deepcopy(media)
        media.transcript = result['segments']
        by_id = {h['id']: h for h in store.approved_for_source(source)}
        by_id.update({identifier: store.highlight(identifier) for identifier in result['ids']})
        rejected = store.rejected_for_source(source)
        selected, skipped = select_ranges(media, source, list(by_id.values()), rejected,
                                           store.preferences(), options, runner, editing_style)
        if not selected:
            reasons = '; '.join(dict.fromkeys(s['reason'] for s in skipped))[:1800]
            raise ValueError('No usable complete exchanges were found. No video was created. '
                             'Inspect the transcript/model results or approve a complete range and rerun.' +
                             (' Selection checks: ' + reasons if reasons else ''))
        if params.get('require_multi') and options.max_ranges > 1 and len(selected) < 2:
            diag = result.get('diagnostics', {})
            reasons = '; '.join(dict.fromkeys(s['reason'] for s in skipped))[:500]
            raise ValueError('Only one distinct complete moment is usable after checking '
                             f"{diag.get('windows', 0)} first-pass and {diag.get('coverage_windows', 0)} "
                             'second-pass dialogue sections. No one-moment main video or duplicate Short '
                             'was exported. Review the timestamped transcript, approve more distinct clips, '
                             'or try another local model.' +
                             (' Selection checks: ' + reasons if reasons else ''))
        if not any(fits_short(h, options) for h in selected):
            raise ValueError('No complete range fits the Short limit. Increase the limit and rerun; no dialogue was truncated.')
        bridges = (find_context_bridges(selected, media.transcript, source, rejected,
                                        options.max_ranges, options.max_main_seconds,
                                        media.duration, runner)
                   if params.get('story_playbook') else [])
        if bridges:
            selected = sorted(selected + bridges, key=lambda item: (item['start'], item['end']))
        story_plan = (plan_story(selected, media.transcript, options.max_short_seconds,
                                 store.preferences(), runner)
                      if params.get('story_playbook') else None)
        if story_plan is not None:
            story_plan['context_bridges'] = [
                {'id': item['id'], 'start': item['start'], 'end': item['end'],
                 'source_ids': item['exchange']['source_ids'], 'reason': item['reason']}
                for item in bridges]
        group_plan = (plan_group_opening(selected, options.max_short_seconds,
                                         store.preferences(), runner)
                      if editing_style == STYLE_GROUP_COMEDY else None)
        opening_id = story_plan['opening_id'] if story_plan else None
        if group_plan and not opening_id:
            opening_id = group_plan['opening_id']
        if group_plan:
            group_plan['applied'] = bool(opening_id and opening_id == group_plan['opening_id'])
            if opening_id and not group_plan['applied']:
                group_plan['reason'] += ' The source-linked story opening took precedence.'
        if story_plan and group_plan and group_plan['opening_id'] == opening_id:
            story_plan['opening_id'] = opening_id
            story_plan['main_order'] = ([opening_id] + [item['id'] for item in selected
                                         if item['id'] != opening_id] if opening_id else
                                        [item['id'] for item in selected])
            if opening_id:
                story_plan['reason'] = group_plan['reason']
        recipes = ['trim_join', 'portrait_fit']
        if options.burn_captions or options.save_srt:
            recipes.append('captions')
        engine = ensure_capabilities(store, recipes, ffmpeg, ffprobe, runner,
                                     lambda v, m: report(.45+v*.1, m))
        def check(folder, manifest):
            verify_bundle(folder, manifest, ffmpeg, ffprobe, runner, lambda v, m: report(.9+v*.09, m))
        details = {'status': 'EXPERIMENTAL', 'job': job_id, 'engine': engine, 'tested_recipes': recipes,
                   'selection': [{**{k: h[k] for k in ('id', 'start', 'end', 'status', 'original_range', 'exchange')},
                                  'context_only': bool(h.get('context_only'))}
                                 for h in selected],
                   'skipped': skipped, 'preferences': store.model_preferences(),
                   'analysis_diagnostics': result.get('diagnostics', {}),
                   'model': params['model'], 'model_identity': identity, 'query': params.get('query', ''),
                   'story_strategy': (
                       'A short source-dialogue bridge may connect selected exchanges; '
                       'a source-linked short opening may move first. No semantic payoff verification.'
                       if story_plan else
                       'Group-comedy priority may move a source-cited model reaction to the opening; '
                       'the rest stays chronological. Reaction meaning is unverified.'
                       if group_plan else
                       'Chronological complete exchanges; no semantic hook or narrative rewriting.'),
                   'story_plan': story_plan, 'editing_style': editing_style,
                   'group_comedy_plan': group_plan,
                   'short_strategy': 'Preserve ranked selection when possible; otherwise reserve one complete eligible Short.',
                   'humor_quality': 'NOT_EVALUATED'}
        output = create_bundle(media, source, selected, params['output_parent'],
                               DraftOptions(options.max_short_seconds, 'fit', options.burn_captions,
                                            options.save_srt, True,
                                            opening_id=opening_id), ffmpeg, runner,
                               lambda v, m: report(.55+v*.35, m), selection='automatic',
                               before_publish=check, extra_manifest=details)
        history_warning = ''
        try:
            store.update_job(job_id, 'completed', 1, 'Auto Edit saved: ' + output['directory'])
        except Exception as error:
            history_warning = f'Videos were saved, but job history could not be updated: {error}'
        # Once the whole checked folder is published, late Cancel must not report a false rollback.
        return {**output, 'committed': True, 'job_id': job_id, 'history_warning': history_warning,
                'story_opening': opening_id, 'story_plan': story_plan,
                'group_comedy_plan': group_plan, 'context_bridges': len(bridges)}
    except Cancelled:
        try:
            store.update_job(job_id, 'cancelled', current[0], 'Cancelled; rerun uses completed analysis caches')
        except Exception:
            pass  # Preserve cancellation even if history storage is unavailable.
        raise
    except Exception as error:
        try:
            store.update_job(job_id, 'failed', current[0], str(error))
        except Exception:
            pass  # The original actionable failure must not become a history error.
        raise
