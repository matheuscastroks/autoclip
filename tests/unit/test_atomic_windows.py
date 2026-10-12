from engine.pipeline import artifacts

def test_transient_windows_reader_lock_does_not_abort_atomic_publication(tmp_path,monkeypatch):
    path=tmp_path/'progress.json';artifacts.atomic_json(path,{'processed_us':1})
    original=artifacts.os.replace;attempts=[]
    def locked_once(source,target):
        attempts.append(target)
        if len(attempts)<3:
            exc=PermissionError('Transient Windows sharing lock');exc.winerror=5;raise exc
        return original(source,target)
    monkeypatch.setattr(artifacts.os,'replace',locked_once)
    artifacts.atomic_json(path,{'processed_us':2})
    assert len(attempts)==3 and path.read_text()=='{"processed_us":2}'
    assert not list(tmp_path.glob('*.partial'))
