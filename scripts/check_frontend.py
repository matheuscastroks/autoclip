"""Read-only launch/API smoke. No provider or pipeline operation is called."""
import json,sys,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from engine.api.launcher import launch,ready
from engine.pipeline.artifacts import atomic_json,file_hash
before=file_hash(root/'poc-projects/jones-manoel/transcript.json')
launch(root,open_browser=False)
session=json.loads((root/'.autoclip/session.json').read_text(encoding='utf-8'))
base=f"http://127.0.0.1:{session['port']}"
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def get(route,headers=None):
    request=urllib.request.Request(base+route,headers=headers or {'Authorization':'Bearer '+session['token']})
    with opener.open(request,timeout=10) as response:return response.read()
projects=json.loads(get('/api/v1/projects'));jobs=json.loads(get('/api/v1/jobs'))
assert projects and any(p['has_transcript'] and p['word_count']==5414 for p in projects)
assert any(p['is_manual'] for p in projects)
assert before==file_hash(root/'poc-projects/jones-manoel/transcript.json')
assert b'AutoClip' in get('/')
source=next(p for p in projects if p['word_count']==5414)
ticket=json.loads(get(f"/api/v1/projects/{source['id']}/media/source/ticket"))['url']
data=get(ticket,{'Range':'bytes=0-31'});assert len(data)==32
summary={'status':'passed','port':session['port'],'projects':len(projects),'transcript_words':5414,'transcript_unchanged':True,'jobs_started':len(jobs),'source_range_bytes':len(data),'frontend_served':True,'provider_requests':0}
atomic_json(root/'poc-results/frontend/launch.json',summary)
print(json.dumps(summary,ensure_ascii=False))
