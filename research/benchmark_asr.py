"""Invoke three upstream ASR implementations on the same fixed CPU sample."""
import argparse, dataclasses, hashlib, importlib.metadata, json, os, pathlib, sys, time, traceback

ROOT = pathlib.Path(__file__).parent
parser = argparse.ArgumentParser()
parser.add_argument('candidate', choices=['steezy', 'openshorts', 'autoclip'])
parser.add_argument('--download-model', action='store_true')
args = parser.parse_args()
model_dir = ROOT / 'models/whisper-small'
if args.download_model:
    from huggingface_hub import snapshot_download
    snapshot_download('Systran/faster-whisper-small', local_dir=str(model_dir))
wav = ROOT / 'results/common-120s.wav'
record = {'candidate': args.candidate, 'device': 'cpu', 'compute_type': 'int8', 'model': 'Systran/faster-whisper-small', 'sample_sha256': hashlib.file_digest(wav.open('rb'), 'sha256').hexdigest(), 'sample_start_in_source_s': 60, 'sample_duration_s': 120, 'faster_whisper_version': importlib.metadata.version('faster-whisper'), 'pyav_version': importlib.metadata.version('av'), 'status': 'failed'}
start = time.perf_counter()
try:
    if args.candidate == 'steezy':
        sys.path.insert(0, str(ROOT / 'snapshots/Steezy-code__clipper/source'))
        from clipper.config import Config
        from clipper.transcribe import transcribe
        transcript = transcribe(str(wav), Config(whisper_model=str(model_dir), whisper_device='cpu', use_nvenc=False))
    elif args.candidate == 'openshorts':
        sys.path.insert(0, str(ROOT / 'snapshots/Marsic1__openshorts/source'))
        os.environ.update(WHISPER_MODEL=str(model_dir), WHISPER_DEVICE='cpu', WHISPER_COMPUTE='int8')
        from transcribe_backends import _transcribe_with_whisper
        transcript = _transcribe_with_whisper(str(wav))
    else:
        sys.path.insert(0, str(ROOT / 'snapshots/Gutsken__Autoclip/source/backend'))
        from autoclip.pipeline.transcribe import transcribe, resolve_compute
        from autoclip.config import WhisperSettings
        from autoclip.system import GPUInfo
        import autoclip.pipeline.transcribe as module
        # Force CPU for this benchmark instead of auto hardware selection.
        module.resolve_compute = lambda settings: ('cpu', 'int8')
        transcript = dataclasses.asdict(transcribe(wav, WhisperSettings(model=str(model_dir), language='pt', compute_type='int8')))
        record['adaptation'] = 'resolve_compute forced to cpu/int8; language explicitly pt'
    record.update(status='completed', transcript=transcript)
except Exception as exc:
    record['error'] = str(exc)
    traceback.print_exc()
record['wall_seconds'] = round(time.perf_counter() - start, 3)
(ROOT / 'results' / (args.candidate + '-asr.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in record.items() if k != 'transcript'}, ensure_ascii=False))
sys.exit(0 if record['status'] == 'completed' else 1)
