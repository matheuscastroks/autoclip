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
