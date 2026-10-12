from types import SimpleNamespace
from uuid import uuid4
import pytest

def test_transcriber_forces_pt_cpu_int8_and_preserves_words(tmp_path):
    from engine.adapters.openshorts.transcriber import OpenShortsTranscriber
    from engine.contracts import AudioArtifact,ASRConfig
    calls={}
    class Model:
        def transcribe(self,path,**kw):
            calls.update(kw)
            words=[SimpleNamespace(word=' Não',start=0.,end=.2,probability=.9),SimpleNamespace(word=' concordo.',start=.2,end=.7,probability=None)]
            return iter([SimpleNamespace(start=0.,end=.7,text='Não concordo.',words=words)]),SimpleNamespace(language='pt')
    def factory(path,**kw): calls.update(kw);return Model()
    wav=tmp_path/'a.wav';wav.write_bytes(b'fixture')
    audio=AudioArtifact(source_id=uuid4(),source_sha256='a'*64,path=wav,sha256='b'*64,duration_us=1_000_000)
    transcriber=OpenShortsTranscriber(model_factory=factory)
    t=transcriber.transcribe(audio,ASRConfig(model_path=tmp_path/'model'))
    assert calls['language']=='pt' and calls['device']=='cpu' and calls['compute_type']=='int8'
    assert t.words[0].text=='Não' and t.words[0].end_us==200_000
    assert t.words[1].probability is None
    assert t.segments[0].word_ids==['w0000000','w0000001']

def test_empty_asr_returns_no_speech_without_remote_fallback(tmp_path):
    from engine.adapters.openshorts.transcriber import OpenShortsTranscriber
    from engine.contracts import AudioArtifact,ASRConfig,PipelineError
    class Model:
        def transcribe(self,*a,**kw): return iter([]),SimpleNamespace(language='pt')
    audio=AudioArtifact(source_id=uuid4(),source_sha256='a'*64,path=tmp_path/'a.wav',sha256='b'*64,duration_us=1_000_000)
    with pytest.raises(PipelineError) as e: OpenShortsTranscriber(model_factory=lambda *a,**kw:Model()).transcribe(audio,ASRConfig(model_path=tmp_path/'model'))
    assert e.value.code=='NO_SPEECH'

def test_windows_utf8_progress():
    from engine.adapters.openshorts.transcriber import configure_utf8
    configure_utf8()
    # Explicit helper is safe for pytest capture and normal Windows console.
