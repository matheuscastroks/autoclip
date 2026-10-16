import pytest
from pathlib import Path

def test_only_verified_owned_instance_is_reused(tmp_path,monkeypatch):
    from engine.api import launcher
    from engine.pipeline.artifacts import atomic_json
    marker=tmp_path/'.autoclip/session.json'
    atomic_json(marker,{'pid':100,'port':8765,'token':'fixture','worker_created':1,'workspace':str(tmp_path)})
    monkeypatch.setattr(launcher,'owned_instance',lambda *a:True)
    monkeypatch.setattr(launcher,'ready',lambda *a:True)
    monkeypatch.setattr(launcher,'start_server',lambda *a:pytest.fail('Should reuse owned instance'))
    assert launcher.launch(tmp_path,open_browser=False).startswith('http://127.0.0.1:8765/#session=')

def test_stale_or_untrusted_instance_is_not_reused(tmp_path,monkeypatch):
    from engine.api import launcher
    from engine.pipeline.artifacts import atomic_json
    atomic_json(tmp_path/'.autoclip/session.json',{'pid':0,'port':8765,'token':'fixture','worker_created':0})
    monkeypatch.setattr(launcher,'owned_instance',lambda *a:False)
    called=[]
    monkeypatch.setattr(launcher,'start_server',lambda root:called.append(root) or {'port':9999,'token':'new'})
    assert '9999' in launcher.launch(tmp_path,open_browser=False)
    assert called==[tmp_path.resolve()]

def test_server_argv_preserves_unicode_spaces_without_shell(tmp_path):
    from engine.api.launcher import server_command
    root=tmp_path/'projeto com espaços e ação'
    argv=server_command(root)
    assert argv[-1]==str(root.resolve()) and argv[-2]=='engine.api.server'
    assert 'shell' not in argv

def test_missing_build_is_an_actionable_error(tmp_path):
    from engine.api.launcher import start_server
    with pytest.raises(RuntimeError,match='interface'):
        start_server(tmp_path)

def test_outdated_engine_fingerprint_restarts_owned_instance(tmp_path,monkeypatch):
    import io,json
    from engine.api import launcher
    from engine.pipeline.artifacts import atomic_json
    session={'pid':100,'port':8765,'token':'fixture','worker_created':1,'workspace':str(tmp_path)}
    atomic_json(tmp_path/'.autoclip/session.json',session)
    monkeypatch.setattr(launcher,'owned_instance',lambda *a:True)
    requests=[]
    class Opener:
        def open(self,req,timeout=0):
            requests.append((req.get_method(),req.full_url))
            payload={'application':'autoclip-editor','engine_fingerprint':'outdated'} if req.full_url.endswith('/health') else {'stopped':True}
            return io.StringIO(json.dumps(payload))
    monkeypatch.setattr(launcher.urllib.request,'build_opener',lambda *a:Opener())
    assert launcher.ready(session) is False
    called=[]
    monkeypatch.setattr(launcher,'start_server',lambda root:called.append(root) or {'port':9999,'token':'fresh'})
    assert '9999' in launcher.launch(tmp_path,open_browser=False)
    assert called==[tmp_path.resolve()]
    assert ('POST','http://127.0.0.1:8765/api/v1/shutdown') in requests

