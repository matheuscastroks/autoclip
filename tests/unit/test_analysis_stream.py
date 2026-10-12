import json
from types import SimpleNamespace as NS
from test_gemini import transcript,payload

def chunk(text,thought=False):return NS(candidates=[NS(content=NS(parts=[NS(text=text,thought=thought)]))],model_version='fixture',usage_metadata=None)

def test_worker_stream_separates_summaries_from_json_and_redacts(monkeypatch,tmp_path):
    from engine.adapters.gemini import request_worker as worker
    request=tmp_path/'request.json';out=tmp_path/'out.json';events=tmp_path/'events.jsonl'
    request.write_text(json.dumps({'model':'gemini-2.5-flash','contents':'text','timeout_s':30,'show_thought_summaries':True,'events_path':str(events),'context':{'window_id':'window-1','attempt':1}}))
    seen=[];body=json.dumps(payload(transcript()))
    def generate(**kw):
        seen.append(kw['config'])
        yield chunk('Conferindo a conclusão. fixture-secret',True)
        yield chunk(body[:20]);yield chunk(body[20:])
    monkeypatch.setattr(worker,'get_gemini_key',lambda:'fixture-secret')
    monkeypatch.setattr(worker.genai,'Client',lambda **kw:NS(models=NS(get=lambda **kw:NS(thinking=True),generate_content_stream=generate),close=lambda:None))
    monkeypatch.setattr(worker.sys,'argv',['worker',str(request),str(out)])
    assert worker.main()==0
    assert json.loads(out.read_text())['text']==body
    assert seen[0]['thinking_config']['include_thoughts'] is True
    rows=[json.loads(line) for line in events.read_text(encoding='utf-8').splitlines()]
    assert any(e['kind']=='thought_summary' and 'Conferindo' in e['message'] for e in rows)
    assert 'fixture-secret' not in events.read_text(encoding='utf-8')
    assert not any(e['kind']=='window_validated' for e in rows)

def test_analyzer_records_only_validated_topics_and_attempts(tmp_path):
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig
    path=tmp_path/'events.jsonl';t=transcript()
    seen=[]
    def request(**kw):
        seen.append(kw);return NS(text=json.dumps(payload(t)))
    config=AnalysisConfig(model='fixture',max_calls=1,clip_preferred_seconds=60,clip_max_seconds=180)
    result=GeminiAnalyzer(request=request,events_path=path).analyze(t,config)
    assert result.complete and '180' in seen[0]['contents']
    events=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    assert any(e['kind']=='request_started' and e['attempt']==1 for e in events)
    validated=next(e for e in events if e['kind']=='window_validated')
    assert validated['topics'][0]['label']=='tema' and validated['candidates'][0]['rationale']

def test_partial_event_is_ignored_until_complete(tmp_path):
    from engine.pipeline.analysis_events import read_events
    path=tmp_path/'events.jsonl';path.write_text('{"kind":"thought_summary","message":"ok"}\n{"kind":')
    assert read_events(path)[0]['message']=='ok'

def test_hard_process_timeout_is_transport_error_but_cancellation_is_preserved(tmp_path,monkeypatch):
    from engine.adapters.gemini import analyzer
    from engine.contracts import PipelineError
    import pytest
    def timeout(*args,**kwargs):raise PipelineError('PROCESS_TIMEOUT','process','Timeout')
    monkeypatch.setattr(analyzer,'run_process',timeout)
    with pytest.raises(analyzer.WorkerRequestError) as exc:analyzer.isolated_request(tmp_path,lambda:False,1,model='fixture',contents='text')
    assert exc.value.transport
    def cancelled(*args,**kwargs):raise PipelineError('CANCELLED','process','Cancelled')
    monkeypatch.setattr(analyzer,'run_process',cancelled)
    with pytest.raises(PipelineError) as exc:analyzer.isolated_request(tmp_path,lambda:True,1,model='fixture',contents='text')
    assert exc.value.code=='CANCELLED'
