"""One isolated, cancellable text-only SDK request; no key in arguments/files."""
import sys,json
from pathlib import Path
import httpx
from google import genai
from google.genai import types
from engine.adapters.gemini.analyzer import GeminiResponse
from engine.adapters.gemini.credentials import get_gemini_key
from engine.pipeline.artifacts import atomic_json

def main():
    request,out=map(Path,sys.argv[1:3]);data=json.loads(request.read_text(encoding='utf-8'));client=None
    try:
        client=genai.Client(api_key=get_gemini_key(),http_options=types.HttpOptions(timeout=data['timeout_s']*1000,retry_options=types.HttpRetryOptions(attempts=1)))
        response=client.models.generate_content(model=data['model'],contents=data['contents'],config={'temperature':0,'response_mime_type':'application/json','response_json_schema':GeminiResponse.model_json_schema()})
        atomic_json(out,{'text':response.text or '', 'model_version':response.model_version,'usage':response.usage_metadata.model_dump(mode='json') if response.usage_metadata else None})
        return 0
    except Exception as exc:
        headers=getattr(getattr(exc,'response',None),'headers',{})
        transport_types=(httpx.TimeoutException,httpx.NetworkError,TimeoutError,ConnectionError)
        try:
            import httpx2
            transport_types+=(httpx2.TimeoutException,httpx2.NetworkError)
        except ImportError:pass
        message=str(getattr(exc,'message',''))
        try:message=message.replace(get_gemini_key(),'[REDACTED]')
        except Exception:message=''
        atomic_json(out,{'error':{'code':getattr(exc,'code',None),'type':type(exc).__name__,'message':message[:2000],'transport':isinstance(exc,transport_types),'retry_after':headers.get('Retry-After')}})
        return 1
    finally:
        if client:client.close()

if __name__=='__main__':raise SystemExit(main())
