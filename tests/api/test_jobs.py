import json,pytest
from pathlib import Path
from test_projects import client,source_folder


def test_api_exposes_measured_progress_and_startup_warning(client):
    from datetime import datetime, timezone, timedelta
    from engine.pipeline.artifacts import atomic_json
    jobs = client.app.state.jobs
    started = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    jobs.store.save_job({'id': 'telemetry', 'project_id': 'p', 'operation': 'prepare',
                         'status': 'running', 'started_at': started})
    jobs.processes['telemetry'] = type('Alive', (), {'poll': lambda self: None})()
    response = client.get('/api/v1/jobs/telemetry').json()
    assert response['progress']['warning'] == 'startup_slow'
    assert response['progress']['stage_percent'] is None
    folder = jobs.root / 'telemetry'
    atomic_json(folder / 'telemetry.json', {'phase': 'transcribe', 'stage_percent': 25,
                'overall_percent': None, 'advanced_at': datetime.now(timezone.utc).isoformat()})
    atomic_json(folder / 'startup.json', {'heartbeat_at': datetime.now(timezone.utc).isoformat()})
    response = client.get('/api/v1/jobs/telemetry').json()
    assert response['progress']['stage_percent'] == 25
    assert response['progress']['overall_percent'] is None
    assert response['progress']['elapsed_seconds'] >= 60
    assert response['progress']['warning'] is None


def test_serialized_legacy_counter_retains_percent_but_verify_does_not(client):
    from engine.pipeline.artifacts import atomic_json
    jobs=client.app.state.jobs
    jobs.store.save_job({'id':'legacy-progress','project_id':'p','operation':'render',
                         'status':'running'})
    jobs.processes['legacy-progress']=type('Alive',(),{'poll':lambda self:None})()
    folder=jobs.root/'legacy-progress'
    atomic_json(folder/'progress.json',{'stage':'render','phase':'render','processed_us':50,'total_us':100})
    response=client.get('/api/v1/jobs/legacy-progress').json()
    assert response['progress']['stage_percent']==50
    atomic_json(folder/'telemetry.json',{'phase':'verify','stage_percent':None})
    response=client.get('/api/v1/jobs/legacy-progress').json()
    assert response['progress']['stage_percent'] is None

def test_one_job_at_a_time_and_cancellation(tmp_path):
    from engine.api.jobs import JobManager
    from engine.api.store import ProjectStore
    store=ProjectStore(tmp_path/'.autoclip/library.sqlite');row=store.register(source_folder(tmp_path))
    class Process:
        pid=0
        def poll(self):return None
    manager=JobManager(store,tmp_path,spawn=lambda *a,**kw:Process())
    first=manager.start(row['id'],'transcribe',{})
    assert manager.start(row['id'],'transcribe',{})['id']==first['id']
    manager.cancel(first['id'])
    assert (tmp_path/'.autoclip/jobs'/first['id']/'cancel').is_file()
    manager.close()

def test_dead_owned_worker_becomes_interrupted(tmp_path):
    from engine.api.jobs import JobManager
    from engine.api.store import ProjectStore
    store=ProjectStore(tmp_path/'library.sqlite')
    store.save_job({'id':'dead','project_id':'p','status':'running','pid':0,'worker_created':0})
    manager=JobManager(store,tmp_path)
    assert manager.status('dead')['status']=='interrupted'

def test_analysis_starts_without_text_checkbox(client,tmp_path):
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    class Process:
        pid=0
        def poll(self):return None
    client.app.state.jobs.spawn=lambda *a,**kw:Process()
    r=client.post(f'/api/v1/projects/{pid}/jobs',json={'operation':'analyze','options':{}})
    assert r.status_code==200 and r.json()['request_mode']=='automatic'
    assert len(client.get('/api/v1/jobs').json())==1

def test_job_polling_never_reorders_latest_analysis(client):
    store=client.app.state.store
    for jid,date in [('old','2026-10-12T10:00:00+00:00'),('new','2026-10-12T11:00:00+00:00')]:
        store.save_job({'id':jid,'project_id':'fixture','status':'completed','operation':'analyze','created_at':date,'events':[]})
    for _ in range(4):
        assert [j['id'] for j in client.get('/api/v1/jobs').json()]==['new','old']

def test_failed_import_is_consistent_and_retry_can_use_local_file(client,tmp_path):
    from types import SimpleNamespace
    jobs=client.app.state.jobs;store=client.app.state.store
    row=store.create(tmp_path/'failed-import','Importação bloqueada')
    jobs.spawn=lambda *a,**kw:SimpleNamespace(pid=0,poll=lambda:None)
    old=jobs.start(row['id'],'prepare',{'source_input':'https://youtu.be/fixture'})
    folder=jobs.root/old['id']
    (folder/'result.json').write_text(json.dumps({'status':'failed','error':{'code':'SOURCE_UNAVAILABLE','message':'generic'}}))
    (folder/'progress.json').write_text(json.dumps({'stage':'import','steps':{'import':'failed','transcribe':'pending','analyze':'pending'}}))
    (folder/'stdout.log').write_text("ERROR: Sign in to confirm you're not a bot.")
    detail=client.get('/api/v1/projects/'+row['id']).json()
    assert detail['status']=='failed'
    assert detail['error']['code']=='SOURCE_AUTH_REQUIRED'
    assert client.get('/api/v1/projects').json()[0]['status']=='failed'
    result=client.post('/api/v1/jobs/'+old['id']+'/resume',json={'source_input':str(tmp_path/'authorized.mp4')})
    assert result.status_code==200
    request=json.loads((jobs.root/result.json()['id']/'request.json').read_text())
    assert request['source_input']==str(tmp_path/'authorized.mp4')
    assert request['operation']=='prepare'
    detail=client.get('/api/v1/projects/'+row['id']).json()
    assert detail['status']=='processing' and detail['error'] is None

def test_retry_cannot_replace_source_of_existing_project(client,tmp_path):
    from types import SimpleNamespace
    from engine.api.launcher import engine_fingerprint
    assert client.get('/api/v1/health').json().get('engine_fingerprint')==engine_fingerprint()
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    unsupported=client.post(f'/api/v1/projects/{pid}/jobs',json={'operation':'legacy_unknown','options':{}})
    assert unsupported.status_code==400 and unsupported.json()['detail']=='Operação não suportada.'
    jobs=client.app.state.jobs;jobs.spawn=lambda *a,**kw:SimpleNamespace(pid=0,poll=lambda:None)
    old=jobs.start(pid,'prepare',{})
    (jobs.root/old['id']/'result.json').write_text(json.dumps({'status':'failed'}))
    res=client.post('/api/v1/jobs/'+old['id']+'/resume',json={'source_input':'replacement.mp4'})
    assert res.status_code==400 and 'não pode ser substituída' in res.json()['detail']


def test_terminal_job_polling_does_not_trigger_redundant_sqlite_writes(client, monkeypatch):
    store = client.app.state.store
    jobs = client.app.state.jobs
    store.save_job({'id': 'finished-job', 'project_id': 'p1', 'status': 'completed', 'finished_at': '2026-10-14T02:00:00Z', 'events': []})
    
    save_calls = []
    original_save = store.save_job
    def tracked_save(job):
        save_calls.append(job['id'])
        return original_save(job)
    monkeypatch.setattr(store, 'save_job', tracked_save)

    # Poll multiple times
    for _ in range(5):
        res = client.get('/api/v1/jobs').json()
        assert any(j['id'] == 'finished-job' for j in res)

    # Must be 0 saves because the job is terminal and unchanged!
    assert 'finished-job' not in save_calls

