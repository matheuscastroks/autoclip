"""Read model availability without disclosing credentials or sending user content."""
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from engine.adapters.gemini.credentials import get_gemini_key
from google import genai
from google.genai import types
client=None
try:
    client=genai.Client(api_key=get_gemini_key(),http_options=types.HttpOptions(timeout=30000,retry_options=types.HttpRetryOptions(attempts=1)))
    rows=[]
    for model in client.models.list():
        actions=getattr(model,'supported_actions',None) or []
        if any('generatecontent' in a.lower() for a in actions):
            rows.append({'name':model.name,'display_name':model.display_name})
    print(json.dumps({'status':'ok','models':rows},ensure_ascii=False))
except Exception as exc:
    print(json.dumps({'status':'failed','code':getattr(exc,'code',None),'message':'Unable to list models; credential/network/permission check required. No secret printed.'}))
    raise SystemExit(1)
finally:
    if client:client.close()
