"""Double-click local launcher; secrets stay inside the local user session."""
import contextlib,json,os,secrets,socket,subprocess,sys,time,urllib.request,webbrowser
from pathlib import Path
import psutil
from engine.pipeline.artifacts import atomic_json
from .projects import read_json

def server_command(workspace):return [sys.executable,'-X','utf8','-m','engine.api.server',str(Path(workspace).resolve())]

def owned_instance(session,workspace):
    try:
        if Path(session.get('workspace','')).resolve()!=Path(workspace).resolve():return False
        p=psutil.Process(session['pid']);cmd=p.cmdline()
        return abs(p.create_time()-session['worker_created'])<.1 and 'engine.api.server' in cmd and str(Path(workspace).resolve()) in cmd
    except (KeyError,ValueError,psutil.Error):return False

def ready(session):
    try:
        port=int(session['port'])
        if not 1024<=port<=65535:return False
        request=urllib.request.Request(f'http://127.0.0.1:{port}/api/v1/health',headers={'Authorization':'Bearer '+session['token']})
        # Bypass proxy configuration for the local service.
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request,timeout=.5) as response:return json.load(response).get('application')=='autoclip-editor'
    except Exception:return False

def start_server(workspace):
    workspace=Path(workspace).resolve()
    if not (workspace/'desktop/dist/index.html').is_file():raise RuntimeError('A interface ainda não foi compilada. Reinstale ou prepare a versão local do aplicativo.')
    root=workspace/'.autoclip';root.mkdir(exist_ok=True)
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    session={'port':port,'token':secrets.token_urlsafe(32),'workspace':str(workspace)}
    atomic_json(root/'session.json',session)
    kwargs={'cwd':str(workspace),'stdout':(root/'server.log').open('ab'),'stderr':subprocess.STDOUT}
    if os.name=='nt':kwargs['creationflags']=subprocess.CREATE_NO_WINDOW
    try:process=subprocess.Popen(server_command(workspace),**kwargs)
    finally:kwargs['stdout'].close()
    session['pid']=process.pid;session['worker_created']=psutil.Process(process.pid).create_time();atomic_json(root/'session.json',session)
    for _ in range(80):
        if ready(session):return session
        if process.poll() is not None:break
        time.sleep(.25)
    if process.poll() is None:process.terminate()
    raise RuntimeError('O serviço local não iniciou. Consulte .autoclip/server.log ou reinstale as dependências da versão local.')

@contextlib.contextmanager
def launch_lock(root):
    path=Path(root)/'.autoclip/launcher.lock';path.parent.mkdir(exist_ok=True)
    with path.open('a+b') as lock:
        if path.stat().st_size==0:lock.write(b'0');lock.flush()
        lock.seek(0)
        if os.name=='nt':
            import msvcrt
            for attempt in range(120):
                try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
                except OSError:
                    if attempt==119:raise RuntimeError('Outra abertura ainda está em andamento. Tente novamente em instantes.')
                    time.sleep(.25)
        else:
            import fcntl;fcntl.flock(lock,fcntl.LOCK_EX)
        try:yield
        finally:
            lock.seek(0)
            if os.name=='nt':msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(lock,fcntl.LOCK_UN)

def acquire_session(workspace:Path,on_acquired=None)->tuple[dict,bool]:
    workspace=Path(workspace).resolve()
    with launch_lock(workspace):
        session=read_json(workspace/'.autoclip/session.json',{}) or {}
        created=session.get('stopping',False) or not (owned_instance(session,workspace) and ready(session))
        if created:session=start_server(workspace)
        if on_acquired:on_acquired(session,created)
    return session,created

def launch(workspace:Path,open_browser=True)->str:
    workspace=Path(workspace).resolve()
    def mark_shared(session,created):
        session['shared']=True
        atomic_json(workspace/'.autoclip/session.json',session)
    session,_=acquire_session(workspace,on_acquired=mark_shared)
    url=f"http://127.0.0.1:{session['port']}/#session={session['token']}"
    if open_browser:webbrowser.open(url)
    return url

def main():
    try:launch(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[2])
    except Exception as exc:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root=tk.Tk();root.withdraw();messagebox.showerror('AutoClip — Abertura',str(exc),parent=root);root.destroy()
        except Exception:pass
        return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
