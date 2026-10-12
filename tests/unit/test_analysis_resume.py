import json
from types import SimpleNamespace as NS
import pytest
from test_gemini import transcript,FakeError
from engine.contracts import AnalysisConfig,PipelineError
from engine.adapters.gemini.analyzer import GeminiAnalyzer
from engine.adapters.openshorts.windows import build_windows


def long_transcript():
    t=transcript();t.segments=[]
    for i,w in enumerate(t.words):w.end_us=i*5_000_000+900_000;w.start_us=i*5_000_000
    return t


def test_resume_skips_validated_windows_with_a_new_job_budget(tmp_path):
    t=long_transcript();calls=[]
    config=AnalysisConfig(model='fixture',max_calls=20,window_seconds=60)
    windows=build_windows(t,60,config.max_text_chars)
    def interrupted(**kw):
        calls.append(kw)
        if len(calls)==2:raise FakeError(401)
        return NS(text='{"topics":[],"candidates":[]}')
    with pytest.raises(PipelineError):GeminiAnalyzer(request=interrupted,work_root=tmp_path).analyze(t,config)
    resumed=[]
    def request(**kw):resumed.append(kw);return NS(text='{"topics":[],"candidates":[]}')
    config.max_calls=len(windows)-1
    result=GeminiAnalyzer(request=request,work_root=tmp_path).analyze(t,config)
    assert result.complete and len(resumed)==len(windows)-1
    assert calls[0]['contents'] not in [r['contents'] for r in resumed]
    assert set(result.covered_word_ids)=={w.id for w in t.words}


def test_checkpoints_are_invalidated_by_model_and_reject_corruption(tmp_path):
    t=transcript();calls=[]
    def request(**kw):calls.append(kw);return NS(text='{"topics":[],"candidates":[]}')
    config=AnalysisConfig(model='fixture',max_calls=1)
    GeminiAnalyzer(request=request,work_root=tmp_path).analyze(t,config)
    GeminiAnalyzer(request=request,work_root=tmp_path).analyze(t,config)
    assert len(calls)==1
    saved=next((tmp_path/'analysis-checkpoints').glob('*.json'))
    saved.write_text('{}')
    GeminiAnalyzer(request=request,work_root=tmp_path).analyze(t,config)
    assert len(calls)==2
    config.model='changed'
    GeminiAnalyzer(request=request,work_root=tmp_path).analyze(t,config)
    assert len(calls)==3


def test_prompt_has_full_video_context_and_no_three_candidate_rule():
    t=long_transcript();calls=[]
    def request(**kw):calls.append(kw);return NS(text='{"topics":[],"candidates":[]}')
    GeminiAnalyzer(request=request).analyze(t,AnalysisConfig(model='fixture',max_calls=20,window_seconds=60))
    assert '<CONTEXTO_GLOBAL>' in calls[0]['contents']
    assert 'Até três propostas' not in calls[0]['contents']
    assert t.words[-1].text in calls[0]['contents'].split('</CONTEXTO_GLOBAL>')[0]
    assert AnalysisConfig(model='fixture',max_calls=1).timeout_s>=180


def test_candidate_evidence_is_compact_but_full_span_is_not_shortened():
    from engine.adapters.gemini.analyzer import GeminiResponse
    from test_gemini import payload
    t=transcript();value=payload(t)
    value['candidates'][0]['evidence_word_ids']=[w.id for w in t.words[:12]]
    with pytest.raises(ValueError):GeminiResponse.model_validate(value)
    value['candidates'][0]['evidence_word_ids']=['w0','w29']
    accepted=GeminiResponse.model_validate(value).candidates[0]
    assert accepted.start_word_id=='w0' and accepted.end_word_id=='w29'
