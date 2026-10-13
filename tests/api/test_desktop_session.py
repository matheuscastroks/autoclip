from pathlib import Path
from unittest.mock import Mock

def test_reused_session_is_not_owned(monkeypatch,tmp_path):
    from engine.api import desktop_session as d
    monkeypatch.setattr(d.launcher,'acquire_session',lambda root,on_acquired: on_acquired({'port':8765,'token':'fixture'},False))
    s=d.DesktopSession(tmp_path)
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
    monkeypatch.setattr(a,'shutdown',lambda: (_ for _ in ()).throw(AssertionError('shared motor')))
    assert a.close()=='shared'
    b.close()

def test_invalid_session_port_is_rejected(monkeypatch,tmp_path):
    import pytest
    from engine.api import desktop_session as d
    monkeypatch.setattr(d.launcher,'acquire_session',lambda root,on_acquired: on_acquired({'port':80,'token':'fixture'},True))
    with pytest.raises(ValueError):d.DesktopSession(tmp_path)
