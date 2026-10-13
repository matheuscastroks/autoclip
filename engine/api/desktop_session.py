"""Private stdin/stdout desktop supervisor. Never log session contents."""
import json,os,sys,uuid,urllib.request,urllib.error
from pathlib import Path
import psutil
from . import launcher
from .projects import read_json
from engine.pipeline.artifacts import atomic_json

class DesktopSession:
    def __init__(self,workspace):
        self.workspace=Path(workspace).resolve()
        self.lease=self.workspace/'.autoclip/desktop-leases'/f'{uuid.uuid4().hex}.json'
        launcher.acquire_session(self.workspace,on_acquired=self._register)
    def _register(self,session,owned):
        self.session,self.owned=session,owned
        port=session.get('port')
        if not isinstance(port,int) or not 1024<=port<=65535 or not session.get('token'):raise ValueError('Invalid local session')
        self.origin=f'http://127.0.0.1:{port}'
        for lease in self.lease.parent.glob('*.json'):
            data=read_json(lease,{}) or {}
            try:
                process=psutil.Process(data['pid'])
                live=abs(process.create_time()-data['created'])<.1
            except (KeyError,psutil.Error):live=False
            if not live:lease.unlink(missing_ok=True)
        if any(self.lease.parent.glob('*.json')):self._mark_shared()
        atomic_json(self.lease,{'pid':os.getpid(),'created':psutil.Process().create_time()})
    def _mark_shared(self):
        path=self.workspace/'.autoclip/session.json'
        current=read_json(path,{}) or {}
        current['shared']=True;atomic_json(path,current)
    def handshake(self):return {'schema_version':'1.0','origin':self.origin,'token':self.session['token'],'owned':self.owned}
    def shutdown(self):
        request=urllib.request.Request(self.origin+'/api/v1/shutdown',data=b'',headers={'Authorization':'Bearer '+self.session['token']},method='POST')
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(request,timeout=3):return 'stopped'
        except urllib.error.HTTPError as exc:return 'busy' if exc.code==409 else 'unavailable'
        except Exception:return 'unavailable'
    def close(self):
        with launcher.launch_lock(self.workspace):
            current=read_json(self.workspace/'.autoclip/session.json',{}) or {}
            shared=current.get('shared') or any(p!=self.lease for p in self.lease.parent.glob('*.json'))
            self.lease.unlink(missing_ok=True)
            if not self.owned or shared:return 'shared'
            if current.get('token') not in (None,self.session['token']):return 'unavailable'
            return self.shutdown()

def main():
    session=None
    try:
        session=DesktopSession(Path(sys.argv[1]))
        print(json.dumps(session.handshake()),flush=True)
        for line in sys.stdin:
            if line.strip()=='close':
                result=session.close();session=None
                print(json.dumps({'result':result}),flush=True);return 0
        return 0
    except Exception:
        print(json.dumps({'error':'O motor local não iniciou. Confira os recursos e o log local.'}),flush=True);return 1
    finally:
        if session is not None:session.close()
if __name__=='__main__':raise SystemExit(main())
