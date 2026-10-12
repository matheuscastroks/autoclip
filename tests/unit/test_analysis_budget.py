import pytest
from test_gemini import transcript

def test_windows_can_cover_complete_source_in_one_bounded_request():
    from engine.adapters.openshorts.windows import build_windows
    t=transcript();t.segments=[]
    for i,w in enumerate(t.words):w.end_us=i*50_000_000+900_000;w.start_us=i*50_000_000
    windows=build_windows(t,window_seconds=1800,max_text_chars=300000)
    assert len(windows)==1 and {w.id for w in windows[0]['words']}=={w.id for w in t.words}

def test_insufficient_window_budget_fails_before_any_request():
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig,PipelineError
    t=transcript();t.segments=[]
    for i,w in enumerate(t.words):w.end_us=i*50_000_000+900_000;w.start_us=i*50_000_000
    with pytest.raises(PipelineError) as e:
        GeminiAnalyzer(request=lambda **kw:pytest.fail('request before budget preflight')).analyze(t,AnalysisConfig(model='fixture',max_calls=1))
    assert e.value.code=='PROVIDER_BUDGET'

