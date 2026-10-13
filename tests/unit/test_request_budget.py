import pytest
from pathlib import Path

def test_counter_is_durable_and_denies_after_restart(tmp_path):
    from engine.pipeline.request_budget import RequestBudget
    from engine.contracts import PipelineError
    path=tmp_path/'budget.sqlite'
    assert RequestBudget(path,2).reserve('a')==1
    assert RequestBudget(path,2).reserve('b')==2
    with pytest.raises(PipelineError):RequestBudget(path,2).reserve('c')
    with pytest.raises(ValueError):RequestBudget(path,3)

def test_provider_retry_reserves_each_attempt(tmp_path):
    from engine.pipeline.request_budget import RequestBudget
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,PipelineError
    from test_gemini import transcript,FakeError
    calls=[];budget=RequestBudget(tmp_path/'budget.sqlite',2)
    def request(**kw):calls.append(1);raise FakeError(503)
    with pytest.raises(PipelineError):GeminiAnalyzer(request=request,sleep=lambda _:None,budget=budget).analyze(transcript(),AnalysisConfig(model='fixture',max_calls=2))
    assert len(calls)==2 and budget.used==2
