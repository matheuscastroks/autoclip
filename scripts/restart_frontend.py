"""Reload an idle owned local service after an engine/UI update, no token output."""
import json,sys,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from engine.api.launcher import launch,owned_instance,ready
session=json.loads((root/'.autoclip/session.json').read_text(encoding='utf-8'))
if owned_instance(session,root) and ready(session):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request=urllib.request.Request(f"http://127.0.0.1:{session['port']}/api/v1/shutdown",method='POST',headers={'Authorization':'Bearer '+session['token']})
    with opener.open(request,timeout=5) as response:json.load(response)
    for _ in range(40):
        if not owned_instance(session,root):break
        time.sleep(.1)
launch(root,open_browser=True)
fresh=json.loads((root/'.autoclip/session.json').read_text(encoding='utf-8'))
print(json.dumps({'status':'restarted','port':fresh['port']}))
