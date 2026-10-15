"""Optional job observations. Never part of an editorial/media cache identity."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
import statistics
import time

_observer = ContextVar('job_progress_observer', default=None)
_work_item = ContextVar('job_progress_work_item', default=None)


def set_work_item(item):
    _work_item.set(item)


def observe(phase, completed=None, total=None, unit=None, *, finished=False, reused=False):
    callback = _observer.get()
    if callback:
        extra={'item':_work_item.get()} if _work_item.get() is not None else {}
        callback(phase, completed, total, unit, finished=finished, reused=reused, **extra)


def active():
    return _observer.get() is not None


def protocol_line(line):
    if not line.startswith('AUTOCLIP_PROGRESS '):
        return
    try:
        value = json.loads(line[len('AUTOCLIP_PROGRESS '):])
        if value['phase'] not in ('model_load', 'transcribe'):
            return
        observe(value['phase'], value.get('completed'), value.get('total'), 'media_us')
    except (ValueError, TypeError, KeyError):
        pass


def protocol_observer(phase, completed=None, total=None, unit=None, **kwargs):
    if phase in ('model_load', 'transcribe'):
        print('AUTOCLIP_PROGRESS ' + json.dumps({'phase': phase, 'completed': completed, 'total': total}), flush=True)


class AnalysisProgress:
    def __init__(self, callback):
        self.callback = callback
        self.total = None
        self.done = set()

    def event(self, kind, data):
        if kind == 'analysis_started':
            self.total = data.get('windows')
            self.done = set()
        elif kind in ('window_validated', 'window_reused') and data.get('window_id'):
            self.done.add(data['window_id'])
        else:
            return
        self.callback('analyze', len(self.done), self.total, 'items')

    def __call__(self, phase, completed=None, total=None, unit=None, **kwargs):
        self.callback(phase, completed, total, unit, **kwargs)


def analysis_event(kind, data):
    callback = _observer.get()
    if isinstance(callback, AnalysisProgress):
        callback.event(kind, data)


@contextmanager
def observing(callback):
    token = _observer.set(callback)
    item_token = _work_item.set(None)
    try:
        yield
    finally:
        _observer.reset(token)
        _work_item.reset(item_token)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def progress_warning(status, elapsed, heartbeat_age, advance_age):
    if status not in ('running', 'cancelling'):
        return None
    if heartbeat_age is None and elapsed >= 30:
        return 'startup_slow'
    if heartbeat_age is not None and heartbeat_age >= 30:
        return 'heartbeat_missing'
    if advance_age is not None and advance_age >= 120:
        return 'no_advance'
    return None


class DurationHistory:
    """Bounded, transactional local measurements; no source text or file paths."""
    def __init__(self, path):
        self.path = Path(path)

    def record(self, key, durations):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY, key TEXT, durations TEXT)')
            db.execute('INSERT INTO samples(key,durations) VALUES (?,?)', (key, json.dumps(durations)))
            db.execute('DELETE FROM samples WHERE key=? AND id NOT IN (SELECT id FROM samples WHERE key=? ORDER BY id DESC LIMIT 20)', (key, key))
            db.execute('DELETE FROM samples WHERE key NOT IN (SELECT key FROM samples GROUP BY key ORDER BY max(id) DESC LIMIT 100)')

    def estimates(self, key, phases):
        if not self.path.exists():
            return None
        try:
            with sqlite3.connect(self.path) as db:
                rows = [json.loads(r[0]) for r in db.execute('SELECT durations FROM samples WHERE key=? ORDER BY id DESC LIMIT 20', (key,))]
            values = {phase: [r[phase] for r in rows if isinstance(r.get(phase), (float, int)) and math.isfinite(r[phase]) and r[phase] > 0] for phase in phases}
            if all(len(samples) >= 3 for samples in values.values()) and values:
                return {phase: statistics.median(samples) for phase, samples in values.items()}
        except (sqlite3.Error, ValueError, TypeError):
            pass
        return None


class ProgressRecorder:
    def __init__(self, folder, *, clock=time.monotonic, weights=None, work_items=None):
        self.folder = Path(folder)
        self.clock = clock
        self.started = self.phase_started = clock()
        self.last_write = float('-inf')
        self.phase = None
        self.samples = []
        self.completed_phases = set()
        self.durations = {}
        self.phase_starts = {}
        self.weights = weights or {}
        self.work_items = work_items or {}
        self.fractions = {}
        self.overall = None
        self.state = {'stage_percent': None, 'overall_percent': None,
                      'stage_eta_seconds': None, 'eta_seconds': None,
                      'heartbeat_at': stamp(), 'advanced_at': stamp()}

    def update(self, phase, completed=None, total=None, unit=None, *, finished=False, reused=False, item=None):
        now = self.clock()
        identity=(phase,item)
        changed = self.phase != identity
        if changed:
            self.phase, self.phase_started, self.samples = identity, now, []
            self.state.update(phase=phase, stage_percent=None, stage_eta_seconds=None,
                              completed_units=None, total_units=None, unit=None, advanced_at=stamp())
        if not finished:
            self.phase_starts.setdefault(identity,now)
        valid = isinstance(total, (int, float)) and math.isfinite(total) and total > 0
        valid_done = isinstance(completed, (int, float)) and math.isfinite(completed) and completed >= 0
        previous = self.state.get('completed_units')
        previous_unit = self.state.get('unit')
        done = min(completed, total) if valid and valid_done else completed if valid_done else None
        if unit != previous_unit or (previous is not None and done is not None and done < previous):
            self.samples = []
            self.phase_started = now
        self.state.update(completed_units=done, total_units=total if valid else None,
                          unit=unit, stage_percent=round(done / total * 100, 1) if valid and done is not None else None)
        if done is not None and (previous is None or done > previous or unit != previous_unit):
            self.state['advanced_at'] = stamp()
            self.samples.append((now, done))
            self.samples = self.samples[-30:]
        self.state['stage_eta_seconds'] = None
        if valid and len(self.samples) >= 3:
            first, last = self.samples[0], self.samples[-1]
            elapsed, delta = last[0] - first[0], last[1] - first[1]
            if elapsed >= 10 and delta > 0:
                self.state['stage_eta_seconds'] = max(0, (total - done) * elapsed / delta)
        if finished:
            if not self.work_items or item not in self.work_items:
                self.completed_phases.add(phase)
            self.state['stage_percent'] = 100.0
            self.state['stage_eta_seconds'] = 0.0
            self.state['advanced_at'] = stamp()
            started=self.phase_starts.pop(identity,None)
            if not reused and started is not None:
                self.durations[phase] = self.durations.get(phase, 0) + max(0, now - started)
        if self.weights and phase in self.weights:
            fraction = (self.state['stage_percent'] or 0) / 100
            parts=self.fractions.setdefault(phase,{})
            parts[item]=max(parts.get(item,0),fraction)
            def phase_fraction(name):
                if name in self.completed_phases:return 1.0
                values=self.fractions.get(name,{})
                if self.work_items:
                    return sum(weight*values.get(key,0) for key,weight in self.work_items.items())/sum(self.work_items.values())
                return values.get(None,0)
            earned=sum(value*phase_fraction(name) for name,value in self.weights.items())
            self.overall = min(99, max(self.overall or 0, round(earned / sum(self.weights.values()) * 100, 1)))
            remaining = sum(value*(1-phase_fraction(name)) for name,value in self.weights.items() if name != phase)
            stage_eta = self.state['stage_eta_seconds']
            if stage_eta is None or self.work_items:
                stage_eta = self.weights[phase] * (1 - phase_fraction(phase))
            self.state.update(overall_percent=self.overall, eta_seconds=remaining + stage_eta)
        self.flush(force=changed or finished)

    def snapshot(self):
        return {**self.state, 'elapsed_seconds': max(0, self.clock() - self.started)}

    def flush(self, *, force=False):
        now = self.clock()
        if force or now - self.last_write >= 1:
            from engine.pipeline.artifacts import atomic_json
            self.state['heartbeat_at'] = stamp()
            try:
                atomic_json(self.folder / 'telemetry.json', self.snapshot())
            except OSError:
                # Losing optional feedback must not invalidate a completed render.
                pass
            self.last_write = now

    def finish(self, status):
        self.state['eta_seconds'] = None
        if status == 'completed':
            self.state.update(stage_percent=100.0, overall_percent=100.0, eta_seconds=0.0)
        self.flush(force=True)
