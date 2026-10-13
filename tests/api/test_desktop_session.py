from pathlib import Path
from unittest.mock import Mock

def test_reused_session_is_not_owned(monkeypatch,tmp_path):
    from engine.api import desktop_session as d
    monkeypatch.setattr(d.launcher,'acquire_session',lambda root,on_acquired: on_acquired({'port':8765,'token':'fixture'},False))
    s=d.DesktopSession(tmp_path)
    monkeypatch.setattr(s,'active_jobs',lambda:False)
    assert s.handshake()['origin']=='http://127.0.0.1:8765'
    assert s.close()=='shared'

def test_busy_shutdown_preserves_motor(monkeypatch,tmp_path):
    from engine.api import desktop_session as d
    monkeypatch.setattr(d.launcher,'acquire_session',lambda root,on_acquired: on_acquired({'port':8765,'token':'fixture'},True))
    s=d.DesktopSession(tmp_path)
    monkeypatch.setattr(s,'shutdown',lambda:'busy')
    assert s.close()=='busy'

def test_second_window_prevents_owned_shutdown(monkeypatch,tmp_path):
    from engine.api import desktop_session as d
    monkeypatch.setattr(d.launcher,'acquire_session',lambda root,on_acquired: on_acquired({'port':8765,'token':'fixture'},True))
    a=d.DesktopSession(tmp_path);b=d.DesktopSession(tmp_path)
    monkeypatch.setattr(a,'active_jobs',lambda:False)
    monkeypatch.setattr(b,'active_jobs',lambda:False)
    monkeypatch.setattr(a,'shutdown',lambda: (_ for _ in ()).throw(AssertionError('shared motor')))
    assert a.close()=='shared'
    b.close()

def test_invalid_session_port_is_rejected(monkeypatch,tmp_path):
    import pytest
    from engine.api import desktop_session as d
    monkeypatch.setattr(d.launcher,'acquire_session',lambda root,on_acquired: on_acquired({'port':80,'token':'fixture'},True))
    with pytest.raises(ValueError):d.DesktopSession(tmp_path)

def test_shutdown_409_never_kills_process(monkeypatch,tmp_path):
    import urllib.error
    from engine.api import desktop_session as d
    monkeypatch.setattr(d.launcher,'acquire_session',lambda root,on_acquired:on_acquired({'port':8765,'token':'fixture'},True))
    session=d.DesktopSession(tmp_path)
    opener=Mock();opener.open.side_effect=urllib.error.HTTPError('http://127.0.0.1:8765',409,'busy',{},None)
    monkeypatch.setattr(d.urllib.request,'build_opener',lambda *args:opener)
    assert session.shutdown()=='busy'
    request=opener.open.call_args.args[0]
    assert request.get_header('Authorization')=='Bearer fixture'
    assert request.get_method()=='POST'
    session.lease.unlink()

def test_session_registration_is_inside_launcher_lock(monkeypatch,tmp_path):
    from engine.api import launcher
    import contextlib
    locked=[]
    @contextlib.contextmanager
    def lock(root):
        locked.append(True)
        try:yield
        finally:locked.pop()
    monkeypatch.setattr(launcher,'launch_lock',lock)
    monkeypatch.setattr(launcher,'owned_instance',lambda *a:False)
    monkeypatch.setattr(launcher,'start_server',lambda *a:{'port':8765,'token':'fixture'})
    launcher.acquire_session(tmp_path,on_acquired=lambda *a:assert_locked(locked))

def assert_locked(locked):assert locked==[True]
def test_shutdown_blocks_new_jobs_before_process_exit(client,tmp_path):
    from test_projects import source_folder
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    called=[]
    client.app.state.jobs.spawn=lambda *a,**kw:called.append(True)
    assert client.post('/api/v1/shutdown').status_code==200
    response=client.post(f'/api/v1/projects/{pid}/jobs',json={'operation':'transcribe','options':{}})
    assert response.status_code==409 and not called
from test_projects import client

def test_shared_active_motor_warns_without_shutdown(monkeypatch,tmp_path):
    from engine.api import desktop_session as d
    monkeypatch.setattr(d.launcher,'acquire_session',lambda root,on_acquired:on_acquired({'port':8765,'token':'fixture'},False))
    session=d.DesktopSession(tmp_path)
    monkeypatch.setattr(session,'active_jobs',lambda:True)
    monkeypatch.setattr(session,'shutdown',lambda: (_ for _ in ()).throw(AssertionError('shared shutdown')))
    assert session.close()=='busy'
