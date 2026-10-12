"""One isolated, cancellable text-only SDK request; no key in arguments/files."""
import sys,json,re,time
from pathlib import Path
import httpx
from google import genai
from google.genai import types
from engine.adapters.gemini.analyzer import GeminiResponse
from engine.adapters.gemini.credentials import get_gemini_key
from engine.pipeline.artifacts import atomic_json
from engine.pipeline.analysis_events import EventWriter

def main():
    request,out=map(Path,sys.argv[1:3]);data=json.loads(request.read_text(encoding='utf-8'));client=None
    try:
        secret=get_gemini_key()
        client=genai.Client(api_key=secret,http_options=types.HttpOptions(timeout=data['timeout_s']*1000,retry_options=types.HttpRetryOptions(attempts=1)))
        writer=EventWriter(data.get('events_path'),secret);context=data.get('context',{})
        config={'temperature':0,'response_mime_type':'application/json','response_json_schema':GeminiResponse.model_json_schema()}
        # Requests started by older workers keep their previous thinking policy.
        summaries=data.get('show_thought_summaries',False)
        if summaries:
            try:supported=bool(client.models.get(model=data['model'],config=types.GetModelConfig(http_options=types.HttpOptions(timeout=5000,retry_options=types.HttpRetryOptions(attempts=1)))).thinking)
            except Exception:supported=False
            if supported:
                config['thinking_config']={'include_thoughts':True}
                if re.match(r'^(models/)?gemini-2\.5-',data['model']):config['thinking_config']['thinking_budget']=-1
            else:writer.emit('thoughts_unavailable','Suporte a resumos não confirmado para este modelo. A análise continua sem resumos.',**context)
        else:writer.emit('thoughts_disabled','Exibição de resumos desativada nas configurações.',**context)
        text=[];model_version=None;usage=None;had_summary=False;started=time.monotonic()
        for response in client.models.generate_content_stream(model=data['model'],contents=data['contents'],config=config):
            if time.monotonic()-started>data['timeout_s']:raise TimeoutError()
            model_version=getattr(response,'model_version',None) or model_version
            metadata=getattr(response,'usage_metadata',None)
            if metadata:usage=metadata.model_dump(mode='json')
            candidates=getattr(response,'candidates',None) or []
            parts=getattr(getattr(candidates[0],'content',None),'parts',None) if candidates else []
            for part in parts or []:
                if not getattr(part,'text',None):continue
                if getattr(part,'thought',False):
                    if summaries:writer.emit('thought_summary',part.text,**context);had_summary=True
                else:text.append(part.text)
        if summaries and 'thinking_config' in config and not had_summary:writer.emit('thoughts_unavailable','Gemini não forneceu resumos nesta tentativa.',**context)
        atomic_json(out,{'text':''.join(text),'model_version':model_version,'usage':usage})
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
