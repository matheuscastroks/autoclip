import json
from types import SimpleNamespace

def test_worker_uses_json_schema_field(monkeypatch,tmp_path):
    from engine.adapters.gemini import request_worker as worker
    request=tmp_path/'request.json';out=tmp_path/'out.json'
    request.write_text(json.dumps({'model':'fixture','contents':'text only','timeout_s':30}))
    seen=[]
    def generate(**kw):
        seen.append(kw['config'])
        yield SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[SimpleNamespace(text='{"topics":[],"candidates":[]}',thought=False)]))],model_version='fixture',usage_metadata=None)
    monkeypatch.setattr(worker,'get_gemini_key',lambda:'fixture-secret')
    monkeypatch.setattr(worker.genai,'Client',lambda **kw:SimpleNamespace(models=SimpleNamespace(generate_content_stream=generate,get=lambda **kw:SimpleNamespace(thinking=False)),close=lambda:None))
    monkeypatch.setattr(worker.sys,'argv',['worker',str(request),str(out)])
    assert worker.main()==0
    assert 'response_schema' not in seen[0]
    assert seen[0]['response_json_schema']['additionalProperties'] is False

def test_isolated_request_prepares_request_file_for_worker(monkeypatch, tmp_path):
    from engine.adapters.gemini.analyzer import _isolated_request
    from engine.adapters.gemini import request_worker as worker
    from pathlib import Path

    verified_request = {}

    def mock_run_process(cmd, cancelled, timeout_s, **kw):
        req_path = Path(cmd[-2])
        resp_path = Path(cmd[-1])
        assert req_path.exists(), "request.json MUST exist before worker is invoked"
        data = json.loads(req_path.read_text(encoding='utf-8'))
        verified_request.update(data)
        
        def generate(**kw):
            yield SimpleNamespace(
                candidates=[SimpleNamespace(content=SimpleNamespace(parts=[SimpleNamespace(text='{"topics":[],"candidates":[]}', thought=False)]))],
                model_version='gemini-2.5-flash',
                usage_metadata=None
            )
        monkeypatch.setattr(worker, 'get_gemini_key', lambda: 'fake-secret')
        monkeypatch.setattr(worker.genai, 'Client', lambda **kw: SimpleNamespace(
            models=SimpleNamespace(generate_content_stream=generate, get=lambda **kw: SimpleNamespace(thinking=False)),
            close=lambda: None
        ))
        monkeypatch.setattr(worker.sys, 'argv', ['worker', str(req_path), str(resp_path)])
        assert worker.main() == 0

    monkeypatch.setattr('engine.adapters.gemini.analyzer.run_process', mock_run_process)

    events = tmp_path / 'events.jsonl'
    res = _isolated_request(
        tmp_path,
        cancelled=lambda: False,
        timeout=25,
        model='gemini-2.5-flash',
        contents='Transcript contents to analyze',
        events_path=events,
        context={'segment': 1},
        show_thought_summaries=True,
    )

    assert verified_request['model'] == 'gemini-2.5-flash'
    assert verified_request['contents'] == 'Transcript contents to analyze'
    assert verified_request['timeout_s'] == 25
    assert verified_request['events_path'] == str(events)
    assert verified_request['context'] == {'segment': 1}
    assert verified_request['show_thought_summaries'] is True

    assert res.text == '{"topics":[],"candidates":[]}'
    assert res.model_version == 'gemini-2.5-flash'

