import json

import pytest


def test_percent_and_eta_are_measured_not_elapsed(tmp_path):
    from engine.pipeline.telemetry import ProgressRecorder
    clock = [0.0]
    recorder = ProgressRecorder(tmp_path, clock=lambda: clock[0])
    recorder.update('transcribe', 0, 100, 'media_us')
    assert recorder.snapshot()['stage_percent'] == 0
    clock[0] = 5
    recorder.update('transcribe', 10, 100, 'media_us')
    assert recorder.snapshot()['stage_eta_seconds'] is None
    clock[0] = 10
    recorder.update('transcribe', 20, 100, 'media_us')
    assert recorder.snapshot()['stage_eta_seconds'] == pytest.approx(40)
    clock[0] = 30
    recorder.flush(force=True)
    assert recorder.snapshot()['stage_percent'] == 20
    assert recorder.snapshot()['advanced_at'] != recorder.snapshot()['heartbeat_at']


def test_unknown_totals_and_terminal_states(tmp_path):
    from engine.pipeline.telemetry import ProgressRecorder
    recorder = ProgressRecorder(tmp_path)
    recorder.update('download', 42, None, 'bytes')
    assert recorder.snapshot()['stage_percent'] is None
    recorder.update('render', 200, 100, 'media_us')
    assert recorder.snapshot()['stage_percent'] == 100
    assert recorder.snapshot()['overall_percent'] != 100
    recorder.finish('failed')
    assert recorder.snapshot()['overall_percent'] != 100
    assert json.loads((tmp_path / 'telemetry.json').read_text())['stage_percent'] == 100


def test_historical_weights_require_three_successes_and_freeze(tmp_path):
    from engine.pipeline.telemetry import DurationHistory, ProgressRecorder
    history = DurationHistory(tmp_path / 'history.json')
    for _ in range(2):
        history.record('cpu-small', {'transcribe': 80, 'analyze': 20})
    assert history.estimates('cpu-small', ['transcribe', 'analyze']) is None
    history.record('cpu-small', {'transcribe': 80, 'analyze': 20})
    weights = history.estimates('cpu-small', ['transcribe', 'analyze'])
    recorder = ProgressRecorder(tmp_path / 'job', weights=weights)
    recorder.update('transcribe', 50, 100, 'media_us')
    assert recorder.snapshot()['overall_percent'] == 40
    recorder.update('transcribe', 100, 100, 'media_us', finished=True)
    recorder.update('analyze', 0, 1, 'items')
    assert recorder.snapshot()['overall_percent'] == 80
    recorder.update('analyze', 1, 1, 'items')
    assert recorder.snapshot()['overall_percent'] == 99
    recorder.finish('completed')
    assert recorder.snapshot()['overall_percent'] == 100
    assert history.estimates('different-model', ['transcribe']) is None


def test_liveness_does_not_assert_task_health():
    from engine.pipeline.telemetry import progress_warning
    assert progress_warning('running', 31, None, None) == 'startup_slow'
    assert progress_warning('running', 125, 1, 125) == 'no_advance'
    assert progress_warning('pending', 125, None, None) is None
    assert progress_warning('completed', 125, 1, 1) is None
