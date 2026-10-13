"""One isolated, cancellable text-only OpenRouter request; no key in arguments/files."""
import sys, json, re, time
from pathlib import Path
import httpx
from engine.adapters.openrouter import credentials
from engine.pipeline.artifacts import atomic_json
from engine.pipeline.analysis_events import EventWriter
from engine.contracts import PipelineError

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def _clean_json_text(raw_text: str) -> str:
    text = raw_text.strip()
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        text = match.group(1).strip()
    return text

def main():
    request, out = map(Path, sys.argv[1:3])
    data = json.loads(request.read_text(encoding='utf-8'))
    secret = ''
    try:
        secret = credentials.get_openrouter_key()
        writer = EventWriter(data.get('events_path'), secret)
        context = data.get('context', {})
        
        headers = {
            "Authorization": f"Bearer {secret}",
            "HTTP-Referer": "https://github.com/matheuscastroks/autoclip",
            "X-Title": "AutoClip Editor",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": data['model'],
            "messages": [
                {"role": "user", "content": data['contents']}
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"}
        }
        
        timeout_s = float(data.get('timeout_s', 180))
        started = time.monotonic()
        
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(OPENROUTER_URL, headers=headers, json=payload)
            
            headers_dict = getattr(resp, 'headers', {})
            retry_after = headers_dict.get('Retry-After')
            
            if resp.status_code == 429:
                err = PipelineError('PROVIDER_RATE_LIMIT', 'analyze', 'O OpenRouter atingiu o limite de requisições deste modelo.')
                err.retry_after = retry_after
                raise err
            elif resp.status_code in (401, 403):
                raise PipelineError('PROVIDER_AUTH', 'analyze', 'Chave de API do OpenRouter inválida ou não autorizada.')
            elif resp.status_code != 200:
                msg = f'OpenRouter retornou erro HTTP {resp.status_code}.'
                try:
                    err_json = resp.json()
                    if 'error' in err_json and 'message' in err_json['error']:
                        msg += f" {err_json['error']['message']}"
                except Exception:
                    pass
                raise PipelineError('PROVIDER_UNAVAILABLE', 'analyze', msg)
                
            res_json = resp.json()
            choices = res_json.get('choices', [])
            if not choices:
                raise PipelineError('PROVIDER_OUTPUT_TRUNCATED', 'analyze', 'OpenRouter retornou resposta sem choices.')
                
            choice = choices[0]
            raw_content = choice.get('message', {}).get('content', '')
            clean_text = _clean_json_text(raw_content)
            
            # Validação rápida de sintaxe JSON
            json.loads(clean_text)
            
            model_version = res_json.get('model') or data['model']
            usage = res_json.get('usage')
            
            atomic_json(out, {
                'text': clean_text,
                'model_version': model_version,
                'usage': usage
            })
            return 0
            
    except Exception as exc:
        headers = getattr(getattr(exc, 'response', None), 'headers', {})
        retry_after = getattr(exc, 'retry_after', None) or headers.get('Retry-After')
        transport_types = (httpx.TimeoutException, httpx.NetworkError, TimeoutError, ConnectionError)
        
        message = str(getattr(exc, 'message', str(exc)))
        if secret:
            try:
                message = message.replace(secret, '[REDACTED]')
            except Exception:
                pass
                
        code = getattr(exc, 'code', None)
        if isinstance(exc, transport_types):
            code = 'PROVIDER_TIMEOUT' if isinstance(exc, (httpx.TimeoutException, TimeoutError)) else 'PROVIDER_UNAVAILABLE'
            
        atomic_json(out, {
            'error': {
                'code': code or 'PROVIDER_UNAVAILABLE',
                'type': type(exc).__name__,
                'message': message[:2000],
                'transport': isinstance(exc, transport_types),
                'retry_after': retry_after,
                'usage': getattr(exc, 'usage', None)
            }
        })
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
