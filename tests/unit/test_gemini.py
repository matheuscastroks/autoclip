from uuid import uuid4
from types import SimpleNamespace
import pytest

def transcript():
    from engine.contracts import TranscriptArtifact,Word,Segment
    ws=[Word(id=f'w{i}',text=('Não' if i==0 else 'ressalva.' if i==29 else 'informação'),start_us=i*1_000_000,end_us=i*1_000_000+900_000) for i in range(30)]
    return TranscriptArtifact(source_sha256='a'*64,words=ws,segments=[Segment(id='s1',word_ids=[w.id for w in ws],text='Não ... ressalva.',start_us=0,end_us=29_900_000)])

def payload(t):
    return {'topics':[{'id':'topic','label':'tema','summary':'tema com ressalva','evidence_word_ids':['w0','w29']}],'candidates':[{'topic_id':'topic','start_word_id':'w0','end_word_id':'w29','evidence_word_ids':['w0','w29'],'rationale':'pensamento completo com ressalva','editorial':{'completeness':'yes','standalone_context':'yes','qualification_preserved':'yes'},'title_suggestion':'Título','description_suggestion':'Descrição'}]}

def test_gemini_request_contains_only_text_and_word_ids():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig
    captured=[]
    def request(**kw): captured.append(kw);return SimpleNamespace(text=__import__('json').dumps(payload(transcript())),model_version='fixture',usage_metadata=None)
    result=GeminiAnalyzer(request=request,sleep=lambda _:None).analyze(transcript(),AnalysisConfig(model='fixture',max_calls=3))
    assert result.complete and 'Não' in captured[0]['contents'] and 'ressalva.' in captured[0]['contents']
    assert isinstance(captured[0]['contents'],str)
    assert 'file_data' not in str(captured) and 'upload' not in str(captured)
    assert len(result.candidates)==1

def test_auth_error_is_not_retried():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,PipelineError
    count=[]
    def request(**kw): count.append(1);raise FakeError(401)
    with pytest.raises(PipelineError) as e: GeminiAnalyzer(request=request,sleep=lambda _:None).analyze(transcript(),AnalysisConfig(model='fixture',max_calls=3))
    assert len(count)==1 and e.value.code=='PROVIDER_AUTH'

class FakeError(Exception):
    def __init__(self,code): self.code=code;super().__init__('sensitive provider body must not be exposed')

def test_429_respects_attempt_budget():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,PipelineError
    count=[]
    def request(**kw): count.append(1);raise FakeError(429)
    with pytest.raises(PipelineError): GeminiAnalyzer(request=request,sleep=lambda _:None).analyze(transcript(),AnalysisConfig(model='fixture',max_calls=1))
    assert len(count)==1

def test_invalid_json_has_one_repair():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,PipelineError
    count=[]
    def request(**kw): count.append(1);return SimpleNamespace(text='not JSON')
    with pytest.raises(PipelineError): GeminiAnalyzer(request=request,sleep=lambda _:None).analyze(transcript(),AnalysisConfig(model='fixture',max_calls=5))
    assert len(count)==2

def test_window_failure_is_not_complete_analysis():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,PipelineError
    t=transcript()
    t.segments=[]
    for i,w in enumerate(t.words):
        w.end_us=i*20_000_000+900_000
        w.start_us=i*20_000_000
    count=[]
    def request(**kw):
        count.append(1)
        if len(count)>1: raise FakeError(401)
        return SimpleNamespace(text='{"topics":[],"candidates":[]}')
    with pytest.raises(PipelineError): GeminiAnalyzer(request=request,sleep=lambda _:None).analyze(t,AnalysisConfig(model='fixture',max_calls=10))

def test_offline_cannot_call_gemini():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,PipelineError
    with pytest.raises(PipelineError): GeminiAnalyzer(request=lambda **kw:pytest.fail('network')).analyze(transcript(),AnalysisConfig(model='fixture',max_calls=1,offline=True))
