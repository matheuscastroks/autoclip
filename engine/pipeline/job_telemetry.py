"""Job-scoped observation, isolated from media artifacts and provider inputs."""
import json
import math
import os
import platform
import sqlite3
from pathlib import Path

from engine.pipeline.artifacts import object_hash
from engine.pipeline.telemetry import AnalysisProgress, DurationHistory, ProgressRecorder, observing


def read_optional(path):
    try:
        value=json.loads(Path(path).read_text(encoding='utf-8'))
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError):
        return {}


def run_observed(folder, run):
    folder = Path(folder)
    request = json.loads((folder / 'request.json').read_text(encoding='utf-8'))
    operation = request['operation']
    settings = request.get('settings', {})
    root = Path(request['project_root'])
    source = read_optional(root / 'source.json')
    duration = source.get('duration_us', 0) or 0
    phases = {
        'prepare': ['audio', 'transcribe', 'analyze'],
        'transcribe': ['audio', 'transcribe'], 'analyze': ['analyze'],
        'preview': ['edit_plan', 'captions', 'reframe', 'render', 'verify'],
        'render': ['edit_plan', 'captions', 'reframe', 'render', 'verify'],
        'render_final': ['render_final', 'verify'],
    }.get(operation, [])
    selection = request.get('selection', {})
    count = len(selection.get('candidate_ids') or selection.get('revision_ids') or [])
    work_items={}
    if selection.get('revision_ids'):
        from uuid import UUID
        for rid in selection['revision_ids']:
            try:
                edl=read_optional(root/'revisions'/str(UUID(rid))/'edl.json')
                work_items[rid]=max(1,edl.get('duration_us',0))
            except ValueError:
                pass
    elif selection.get('candidate_ids'):
        transcript=read_optional(root/'transcript.json')
        words={w['id']:w for w in transcript.get('words',[])}
        for candidate in read_optional(root/'analysis.json').get('candidates',[]):
            if candidate['id'] in selection['candidate_ids']:
                start=words.get(candidate.get('start_word_id'),{}).get('start_us',0)
                end=words.get(candidate.get('end_word_id'),{}).get('end_us',start)
                work_items[candidate['id']]=max(1,end-start)
    identity={'operation': operation,
                       'model': Path(settings.get('asr_model_path', '')).name,
                       'provider': settings.get('ai_provider'),
                       'ai_model': settings.get('openrouter_model') if settings.get('ai_provider') == 'openrouter' else settings.get('gemini_model'),
                       'window': settings.get('window_seconds'), 'max_chars': settings.get('max_text_chars'),
                       'pause': settings.get('pause_mode'), 'count': count,
                       'hardware': [platform.machine(), platform.processor(), os.cpu_count()]}
    def history_key():
        return object_hash({**identity,'duration_bucket':int(math.log2(max(1,duration/1e6))),
                            'output_bucket':int(math.log2(max(1,sum(work_items.values())/1e6)))})
    key=history_key()
    history_path=Path(request['workspace'])/'.autoclip'/'progress-history.sqlite' if request.get('workspace') else folder/'progress-history.sqlite'
    history = DurationHistory(history_path)
    weights = history.estimates(key, phases) if duration else None
    recorder = ProgressRecorder(folder, weights=weights,work_items=work_items)
    def update(*args,**kwargs):
        nonlocal duration,key
        if not duration and args[0] in ('audio','transcribe','analyze'):
            duration=read_optional(root/'source.json').get('duration_us',0) or 0
            if duration:
                key=history_key()
                recorder.weights=history.estimates(key,phases) or {}
        recorder.update(*args,**kwargs)
    result = None
    try:
        with observing(AnalysisProgress(update)):
            result = run(folder)
        return result
    finally:
        status = 'failed'
        try:
            status = json.loads((folder / 'result.json').read_text(encoding='utf-8'))['status']
        except (OSError, ValueError, KeyError):
            pass
        recorder.finish(status)
        if status == 'completed' and recorder.durations:
            try:
                history.record(key, recorder.durations)
            except (OSError,sqlite3.Error):
                pass
