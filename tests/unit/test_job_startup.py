import json
import subprocess
import sys


def test_cli_records_worker_startup_even_when_operation_fails(tmp_path):
    (tmp_path / 'request.json').write_text(json.dumps({
        'operation': 'probe', 'project_root': str(tmp_path / 'project'), 'settings': {},
    }))
    result = subprocess.run(
        [sys.executable, '-m', 'engine.cli', 'job-worker', str(tmp_path)],
        capture_output=True, timeout=30,
    )
    assert result.returncode == 1
    assert (tmp_path / 'startup.json').is_file()
    startup = json.loads((tmp_path / 'startup.json').read_text())
    assert startup['heartbeat_at'] and startup['started_at']
    assert startup['phase'] == 'running'
    assert set(startup) == {'pid', 'started_at', 'heartbeat_at', 'phase'}
