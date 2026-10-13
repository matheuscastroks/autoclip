import json
import pytest
from pathlib import Path
from engine.contracts import PipelineError

def test_openrouter_worker_success(tmp_path, monkeypatch):
    from engine.adapters.openrouter import request_worker
    
    req_file = tmp_path / 'req.json'
    out_file = tmp_path / 'out.json'
    req_file.write_text(json.dumps({
        'model': 'openrouter/free',
        'contents': 'Analise este texto',
        'timeout_s': 10,
    }), encoding='utf-8')
    
    expected_response_json = json.dumps({
        'topics': [{'id': 't1', 'label': 'Tema 1', 'summary': 'Resumo do tema', 'evidence_word_ids': ['w1']}],
        'candidates': []
    })
    
    class FakeResponse:
        status_code = 200
        headers = {}
        def json(self):
            return {
                'id': 'gen-123',
                'model': 'meta-llama/llama-3.3-70b-instruct:free',
                'choices': [{
                    'message': {'content': expected_response_json},
                    'finish_reason': 'stop'
                }],
                'usage': {'prompt_tokens': 100, 'completion_tokens': 50}
            }
    
    monkeypatch.setattr('engine.adapters.openrouter.credentials.get_openrouter_key', lambda: 'sk-or-v1-secret')
    monkeypatch.setattr('httpx.Client.post', lambda self, url, **kw: FakeResponse())
    
    monkeypatch.setattr('sys.argv', ['worker', str(req_file), str(out_file)])
    ret = request_worker.main()
    assert ret == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding='utf-8'))
    assert 'text' in data
    assert 'topics' in json.loads(data['text'])
    assert data['model_version'] == 'meta-llama/llama-3.3-70b-instruct:free'

def test_openrouter_worker_strips_markdown_fences(tmp_path, monkeypatch):
    from engine.adapters.openrouter import request_worker
    
    req_file = tmp_path / 'req.json'
    out_file = tmp_path / 'out.json'
    req_file.write_text(json.dumps({
        'model': 'openrouter/free',
        'contents': 'Analise',
        'timeout_s': 10,
    }), encoding='utf-8')
    
    fenced_content = '```json\n{"topics": [], "candidates": []}\n```'
    
    class FakeResponse:
        status_code = 200
        headers = {}
        def json(self):
            return {
                'id': 'gen-123',
                'model': 'test-model',
                'choices': [{
                    'message': {'content': fenced_content},
                    'finish_reason': 'stop'
                }]
            }
            
    monkeypatch.setattr('engine.adapters.openrouter.credentials.get_openrouter_key', lambda: 'sk-or-v1-secret')
    monkeypatch.setattr('httpx.Client.post', lambda self, url, **kw: FakeResponse())
    monkeypatch.setattr('sys.argv', ['worker', str(req_file), str(out_file)])
    
    ret = request_worker.main()
    assert ret == 0
    data = json.loads(out_file.read_text(encoding='utf-8'))
    parsed = json.loads(data['text'])
    assert parsed == {"topics": [], "candidates": []}

def test_openrouter_worker_handles_rate_limit(tmp_path, monkeypatch):
    from engine.adapters.openrouter import request_worker
    
    req_file = tmp_path / 'req.json'
    out_file = tmp_path / 'out.json'
    req_file.write_text(json.dumps({
        'model': 'openrouter/free',
        'contents': 'Analise',
        'timeout_s': 10,
    }), encoding='utf-8')
    
    class FakeRateLimitResponse:
        status_code = 429
        headers = {'Retry-After': '5'}
        text = 'Rate limit reached'
        def json(self):
            return {'error': {'message': 'Rate limit exceeded'}}
            
    monkeypatch.setattr('engine.adapters.openrouter.credentials.get_openrouter_key', lambda: 'sk-or-v1-secret')
    monkeypatch.setattr('httpx.Client.post', lambda self, url, **kw: FakeRateLimitResponse())
    monkeypatch.setattr('sys.argv', ['worker', str(req_file), str(out_file)])
    
    ret = request_worker.main()
    assert ret == 1
    data = json.loads(out_file.read_text(encoding='utf-8'))
    assert data['error']['code'] == 'PROVIDER_RATE_LIMIT'
    assert data['error']['retry_after'] == '5'
