import hashlib
from types import SimpleNamespace

from engine.pipeline.telemetry import observing


def test_transcription_observer_preserves_segments_and_options():
    from engine.adapters.openshorts.transcription_progress import progress_model
    from vendor.openshorts.transcribe_backends import transcribe_explicit
    from vendor.openshorts.subtitles import WHISPER_TRANSCRIBE_PARAMS
    seen = []

    class Model:
        def transcribe(self, path, **options):
            assert path == 'synthetic.wav'
            assert options == dict(WHISPER_TRANSCRIBE_PARAMS, language='pt')
            segment = SimpleNamespace(start=0.0, end=2.0, text=' Olá', words=[
                SimpleNamespace(word=' Olá', start=0.0, end=2.0, probability=0.9)])
            return iter([segment]), SimpleNamespace(language='pt')

    with observing(lambda *args, **kwargs: seen.append((args, kwargs))):
        result = transcribe_explicit('synthetic.wav', progress_model(Model(), 4_000_000), 'pt')
    assert result['segments'][0]['words'][0]['word'] == ' Olá'
    assert result['segments'][0]['end'] == 2.0
    assert any(args[:3] == ('transcribe', 2_000_000, 4_000_000) for args, _ in seen)


def test_hash_reports_bytes_without_changing_digest(tmp_path):
    from engine.pipeline.artifacts import file_hash
    path = tmp_path / 'synthetic.bin'
    data = b'abc' * 400_000
    path.write_bytes(data)
    seen = []
    with observing(lambda *args, **kwargs: seen.append(args)):
        digest = file_hash(path)
    assert digest == hashlib.sha256(data).hexdigest()
    assert any(args[:4] == ('integrity', len(data), len(data), 'bytes') for args in seen)


def test_analysis_only_counts_validated_or_reused_windows(tmp_path):
    from engine.pipeline.analysis_events import EventWriter
    from engine.pipeline.telemetry import AnalysisProgress
    seen = []
    analyzer = AnalysisProgress(lambda *args, **kwargs: seen.append(args))
    writer = EventWriter(tmp_path / 'events.jsonl')
    with observing(analyzer):
        writer.emit('analysis_started', windows=2, completed_windows=0)
        writer.emit('window_started', window_id='one', windows=2)
        writer.emit('response_rejected', window_id='one', windows=2)
        assert seen[-1][:3] == ('analyze', 0, 2)
        writer.emit('window_validated', window_id='one', windows=2)
        writer.emit('window_validated', window_id='one', windows=2)
        assert seen[-1][:3] == ('analyze', 1, 2)
        writer.emit('window_reused', window_id='two', windows=2)
        assert seen[-1][:3] == ('analyze', 2, 2)


def test_cancelled_copy_preserves_existing_target(tmp_path):
    import pytest
    from engine.contracts import PipelineError
    from engine.pipeline.transfer import copy_observed
    source, target = tmp_path / 'source', tmp_path / 'target'
    source.write_bytes(b'synthetic')
    target.write_bytes(b'previous')
    with pytest.raises(PipelineError):
        copy_observed(source, target, cancelled=lambda: True)
    assert target.read_bytes() == b'previous'
    assert not list(tmp_path.glob('*.partial'))


def test_wav_progress_uses_data_bytes_when_copyts_reports_zero(tmp_path):
    import wave
    from engine.media.audio_progress import WavProgress
    path=tmp_path/'audio.wav'
    with wave.open(str(path),'wb') as stream:
        stream.setparams((1,2,16000,0,'NONE','not compressed'))
        stream.writeframes(b'\x00'*32000)
    seen=[]
    progress=WavProgress(path,1_000_000,lambda done,total:seen.append((done,total)))
    progress.line('out_time_us=0')
    progress.line('total_size=16044')
    assert seen[-1]==(500_000,1_000_000)
