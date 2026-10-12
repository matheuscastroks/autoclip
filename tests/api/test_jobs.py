import json,pytest
from pathlib import Path
from test_projects import client,source_folder

def test_one_job_at_a_time_and_cancellation(tmp_path):
    from engine.api.jobs import JobManager
    from engine.api.store import ProjectStore
    store=ProjectStore(tmp_path/'.autoclip/library.sqlite');row=store.register(source_folder(tmp_path))
    class Process:
        pid=0
        def poll(self):return None
    manager=JobManager(store,tmp_path,spawn=lambda *a,**kw:Process())
    first=manager.start(row['id'],'transcribe',{})
    with pytest.raises(RuntimeError):manager.start(row['id'],'transcribe',{})
    manager.cancel(first['id'])
    assert (tmp_path/'.autoclip/jobs'/first['id']/'cancel').is_file()

def test_dead_owned_worker_becomes_interrupted(tmp_path):
    from engine.api.jobs import JobManager
    from engine.api.store import ProjectStore
    store=ProjectStore(tmp_path/'library.sqlite')
    store.save_job({'id':'dead','project_id':'p','status':'running','pid':0,'worker_created':0})
    manager=JobManager(store,tmp_path)
    assert manager.status('dead')['status']=='interrupted'

def test_analysis_requires_explicit_text_authorization(client,tmp_path):
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    r=client.post(f'/api/v1/projects/{pid}/jobs',json={'operation':'analyze','options':{}})
    assert r.status_code==400
    assert not client.get('/api/v1/jobs').json()
