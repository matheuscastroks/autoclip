"""Offline frozen-worker smoke with generated media, never user projects or AI."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

import psutil

from engine.media.probe import locate_tools
from engine.pipeline.artifacts import atomic_json


def run_job(engine, folder, request, timeout):
    folder.mkdir()
    atomic_json(folder / 'request.json', request)
    phases = set()
    with (folder / 'stdout.log').open('wb') as log:
        process = subprocess.Popen([str(engine), 'job-worker', str(folder)], stdout=log,
                                   stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        deadline = time.monotonic() + timeout
        try:
            while process.poll() is None:
                try:
                    data = json.loads((folder / 'telemetry.json').read_text())
                    if data.get('phase'):
                        phases.add(data['phase'])
                except (OSError, ValueError):
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError('Isolated worker exceeded smoke-test deadline')
                time.sleep(0.1)
        finally:
            if process.poll() is None:
                (folder / 'cancel').touch()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Only descendants of the process created by this test.
                    try:
                        owned = psutil.Process(process.pid)
                        for child in owned.children(recursive=True):
                            child.kill()
                        owned.kill()
                    except psutil.NoSuchProcess:
                        pass
                    process.wait(timeout=10)
    startup = json.loads((folder / 'startup.json').read_text())
    result = json.loads((folder / 'result.json').read_text())
    telemetry = json.loads((folder / 'telemetry.json').read_text())
    return {'exit_code': process.returncode, 'startup_confirmed': startup['phase'] == 'running',
            'status': result['status'], 'error_code': (result.get('error') or {}).get('code'),
            'stage_percent': telemetry.get('stage_percent'),
            'overall_percent': telemetry.get('overall_percent'),
            'observed_phases': sorted(phases)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--asr-model', type=Path)
    parser.add_argument('--timeout-seconds', type=int, default=120)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    scratch = root / '.runtime-tmp'
    scratch.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix='progress-native-', dir=scratch))
    ffmpeg, ffprobe = locate_tools()
    source = workspace / 'synthetic.mp4'
    subprocess.run([str(ffmpeg), '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                    'color=c=gray:size=320x180:rate=30:duration=4', '-f', 'lavfi', '-i',
                    'anullsrc=r=48000:cl=mono', '-t', '4', '-c:v', 'libx264', '-c:a', 'aac',
                    str(source)], check=True, timeout=30)
    request = {'workspace': str(workspace), 'project_root': str(workspace / 'project'),
               'source_input': str(source), 'operation': 'import',
               'settings': {'ffmpeg': str(ffmpeg), 'ffprobe': str(ffprobe),
                            'asr_model_path': str(args.asr_model.resolve()) if args.asr_model else '',
                            'gemini_model': 'unused-offline-smoke', 'max_calls': 1,
                            'window_seconds': 180, 'max_text_chars': 6000}}
    report = {'import': run_job(args.engine.resolve(), workspace / 'import', request, args.timeout_seconds),
              'paid_calls': 0, 'synthetic_media_seconds': 4}
    assert report['import']['status'] == 'completed' and report['import']['overall_percent'] == 100
    if args.asr_model:
        request['operation'] = 'transcribe'
        report['transcribe'] = run_job(args.engine.resolve(), workspace / 'transcribe', request, args.timeout_seconds)
        assert report['transcribe']['status'] == 'failed'  # silence is not a transcript
        assert report['transcribe']['overall_percent'] != 100
        assert 'transcribe' in report['transcribe']['observed_phases']
    atomic_json(workspace / 'report.json', report)
    print(json.dumps({'report': str(workspace / 'report.json'), **report}, indent=2))


if __name__ == '__main__':
    main()
