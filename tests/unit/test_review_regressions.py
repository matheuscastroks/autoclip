import json
from types import SimpleNamespace
from pathlib import Path
import httpx,pytest
from test_gemini import transcript

def test_missing_response_arrays_are_not_successful_empty_analysis():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,PipelineError
    calls=[]
    def request(**kw):calls.append(1);return SimpleNamespace(text='{}')
    with pytest.raises(PipelineError):GeminiAnalyzer(request=request,sleep=lambda _:None).analyze(transcript(),AnalysisConfig(model='fixture',max_calls=3))
    assert len(calls)==2

def test_real_httpx_timeout_retries_without_exceeding_budget():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,PipelineError
    calls=[]
    def request(**kw):calls.append(1);raise httpx.ReadTimeout('timeout')
    with pytest.raises(PipelineError) as e:GeminiAnalyzer(request=request,sleep=lambda _:None).analyze(transcript(),AnalysisConfig(model='fixture',max_calls=2))
    assert len(calls)==2 and e.value.retryable

def test_retry_after_is_capped():
    from engine.adapters.gemini.analyzer import retry_delay
    error=SimpleNamespace(response=SimpleNamespace(headers={'Retry-After':'120'}))
    assert retry_delay(error)==30

def test_quota_error_stops_without_immediate_retry():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer,WorkerRequestError
    from engine.contracts import AnalysisConfig,PipelineError
    calls=[]
    def request(**kw):
        calls.append(1)
        raise WorkerRequestError({'code':429,'type':'ClientError','transport':False})
    with pytest.raises(PipelineError) as error:
        GeminiAnalyzer(request=request,sleep=lambda _:None).analyze(transcript(),AnalysisConfig(model='fixture',max_calls=10))
    assert error.value.code=='PROVIDER_RATE_LIMIT'
    assert len(calls)==1

def test_analysis_cancels_before_second_window():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,Word,PipelineError
    t=transcript();t.segments=[]
    t.words=[Word(id=f'w{i}',text='a',start_us=i*20_000_000,end_us=i*20_000_000+900_000) for i in range(30)]
    calls=[]
    def request(**kw):calls.append(1);return SimpleNamespace(text='{"topics":[],"candidates":[]}')
    with pytest.raises(PipelineError) as e:GeminiAnalyzer(request=request).analyze(t,AnalysisConfig(model='fixture',max_calls=10),cancelled=lambda:len(calls)>=1)
    assert e.value.code=='CANCELLED' and len(calls)==1

def test_complete_model_assets_required_before_loading(tmp_path):
    from engine.adapters.openshorts.transcriber import model_fingerprint
    from engine.contracts import PipelineError
    (tmp_path/'model.bin').write_bytes(b'weights')
    with pytest.raises(PipelineError):model_fingerprint(tmp_path)
    for name in ['config.json','tokenizer.json','vocabulary.txt']:(tmp_path/name).write_text('{}')
    digest=model_fingerprint(tmp_path)
    (tmp_path/'tokenizer.json').write_text('{"updated":true}')
    assert model_fingerprint(tmp_path)!=digest

def test_vendor_and_font_bytes_are_hashed(tmp_path):
    from engine.pipeline.fingerprints import stage_dependencies,font_fingerprint
    assert 'vendor/openshorts/transcribe_backends.py' in stage_dependencies('transcribe')['files']
    font=tmp_path/'font.ttf';font.write_bytes(b'old')
    before=font_fingerprint(font,'fixture')
    font.write_bytes(b'new')
    assert font_fingerprint(font,'fixture')!=before
