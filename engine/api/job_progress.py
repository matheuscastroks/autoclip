"""Read-only progress presentation; polling never creates artificial advancement."""
from datetime import datetime, timezone
import math
from engine.pipeline.telemetry import progress_warning
from .projects import read_json


def present_progress(job, folder):
    result = dict(job)
    legacy = job.get('progress') or {}
    telemetry = read_json(folder / 'telemetry.json', {}) or {}
    startup = read_json(folder / 'startup.json', {}) or {}
    progress = {**legacy, **telemetry}
    if not telemetry and legacy.get('phase') in ('audio','transcribe','reframe','render','render_final'):
        done,total=legacy.get('processed_us'),legacy.get('total_us')
        if isinstance(done,(int,float)) and isinstance(total,(int,float)) and math.isfinite(done) and math.isfinite(total) and total>0:
            progress['stage_percent']=min(100,max(0,done/total*100))
    end = datetime.now(timezone.utc)
    if job.get('finished_at'):
        try:
            end = datetime.fromisoformat(job['finished_at'])
        except ValueError:
            pass

    def age(value):
        try:
            return max(0, (end - datetime.fromisoformat(value)).total_seconds())
        except (TypeError, ValueError):
            return None

    elapsed = age(job.get('started_at'))
    if not progress and elapsed is None:
        return result
    progress['elapsed_seconds'] = elapsed
    heartbeat = startup.get('heartbeat_at') or telemetry.get('heartbeat_at')
    progress['heartbeat_at'] = heartbeat
    progress['warning'] = progress_warning(job['status'], elapsed or 0, age(heartbeat),
                                            age(progress.get('advanced_at') or job.get('started_at')))
    result['progress'] = progress
    return result
