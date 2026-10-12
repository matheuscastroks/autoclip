import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_projects import client,source_folder


def test_project_trash_survives_discovery_and_restores_source(client,tmp_path):
    from engine.api.projects import discover
    directory=tmp_path/'poc-projects';directory.mkdir()
    root=source_folder(directory)
    pid=client.post('/api/v1/projects/import',json={'path':str(root)}).json()['id']
    assert client.delete('/api/v1/projects/'+pid).status_code==200
    discover(client.app.state.store,tmp_path)
    assert client.get('/api/v1/projects').json()==[]
    assert (root/'original.mp4').read_bytes()==b'test video content'
    assert client.get('/api/v1/trash').json()[0]['id']==pid
    assert client.post('/api/v1/trash/'+pid+'/restore').status_code==200
    assert client.get('/api/v1/projects').json()[0]['id']==pid


def test_automatic_creation_persists_authorization_and_budget(client,monkeypatch):
    import engine.api.settings as settings
    monkeypatch.setattr(settings,'get_gemini_key',lambda:'fixture')
    class Process:
        pid=0
        def poll(self):return None
    manager=client.app.state.jobs;manager.spawn=lambda *a,**kw:Process()
    value={'name':'Automatic','source_input':'fixture.mp4','automatic':True,'authorize_text':True,'max_calls':3}
    response=client.post('/api/v1/projects',json=value)
    assert response.status_code==200
    job=response.json()['job'];assert job['operation']=='prepare' and job['request_limit']==3
    request=json.loads((manager.root/job['id']/'request.json').read_text())
    assert request['operation']=='prepare' and request['settings']['max_calls']==3


def test_automatic_creation_without_consent_creates_nothing(client):
    response=client.post('/api/v1/projects',json={'name':'Automatic','source_input':'fixture.mp4','automatic':True})
    assert response.status_code==400
    assert not client.get('/api/v1/projects').json() and not client.get('/api/v1/jobs').json()


def test_active_project_cannot_be_deleted(client,tmp_path):
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    jobs=client.app.state.jobs
    class Process:
        pid=0
        def poll(self):return None
    jobs.spawn=lambda *a,**kw:Process()
    jobs.start(pid,'transcribe',{})
    assert client.delete('/api/v1/projects/'+pid).status_code==409


def test_prepare_requires_authorization_and_does_not_resume_analysis_budget(client,tmp_path):
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    assert client.post(f'/api/v1/projects/{pid}/jobs',json={'operation':'prepare','options':{}}).status_code==400
    class Process:
        pid=0
        def poll(self):return None
    jobs=client.app.state.jobs;jobs.spawn=lambda *a,**kw:Process()
    job=jobs.start(pid,'prepare',{'authorize_text':True})
    assert job['operation']=='prepare'
    folder=jobs.root/job['id']
    (folder/'result.json').write_text(json.dumps({'status':'failed'}))
    with pytest.raises(ValueError):jobs.resume(job['id'])


def test_prepare_worker_runs_in_order_stops_before_render(tmp_path,monkeypatch):
    import engine.api.job_worker as worker
    root=source_folder(tmp_path);folder=tmp_path/'job';folder.mkdir()
    settings={'asr_model_path':str(tmp_path),'gemini_model':'fixture','max_calls':2,'window_seconds':600,'max_text_chars':60000,'ffmpeg':'ffmpeg','ffprobe':'ffprobe'}
    (folder/'request.json').write_text(json.dumps({'project_root':str(root),'settings':settings,'operation':'prepare','source_input':None}))
    steps=[]
    monkeypatch.setattr(worker,'run_project',lambda *a,**kw: steps.append(kw['stop_after']) or SimpleNamespace(status='analyzed'))
    monkeypatch.setattr(worker,'GeminiAnalyzer',lambda **kw:object())
    assert worker.main(folder)==0
    assert steps==['transcribe','analyze']
    progress=json.loads((folder/'progress.json').read_text())
    assert progress['steps']['analyze']=='completed' and progress['steps']['render']=='pending'


def test_prepare_worker_stops_after_transcription_failure(tmp_path,monkeypatch):
    import engine.api.job_worker as worker
    root=source_folder(tmp_path);folder=tmp_path/'job';folder.mkdir()
    (folder/'request.json').write_text(json.dumps({'project_root':str(root),'settings':{'asr_model_path':str(tmp_path),'gemini_model':'fixture','max_calls':2,'window_seconds':600,'max_text_chars':60000,'ffmpeg':'ffmpeg','ffprobe':'ffprobe'},'operation':'prepare','source_input':None}))
    def fail(*a,**kw):raise RuntimeError('fixture')
    monkeypatch.setattr(worker,'run_project',fail)
    monkeypatch.setattr(worker,'GeminiAnalyzer',lambda **kw:pytest.fail('Analysis must not start'))
    assert worker.main(folder)==1
    assert json.loads((folder/'progress.json').read_text())['steps']['transcribe']=='failed'


def test_deleted_cut_is_hidden_and_restorable(client,tmp_path):
    from uuid import uuid4
    root=source_folder(tmp_path);rid=str(uuid4());(root/'revisions'/rid).mkdir(parents=True)
    (root/'project.json').write_text(json.dumps({'revisions':[{'revision_id':rid}]}))
    pid=client.post('/api/v1/projects/import',json={'path':str(root)}).json()['id']
    endpoint=f'/api/v1/projects/{pid}/revisions/{rid}'
    assert len(client.get(f'/api/v1/projects/{pid}/revisions').json())==1
    assert client.delete(endpoint).status_code==200
    assert client.get(f'/api/v1/projects/{pid}/revisions').json()==[]
    assert client.get(f'/api/v1/projects/{pid}/deleted-revisions').json()[0]['revision_id']==rid
    assert client.post(endpoint+'/restore').status_code==200
    assert len(client.get(f'/api/v1/projects/{pid}/revisions').json())==1


def test_deleted_cut_survives_new_analysis_state(tmp_path):
    from engine.api.reviews import set_deleted,list_deleted
    from uuid import uuid4
    root=source_folder(tmp_path);rid=str(uuid4());(root/'revisions'/rid).mkdir(parents=True)
    row={'revision_id':rid,'render_path':str(root/'preview.mp4')}
    (root/'project.json').write_text(json.dumps({'revisions':[row]}))
    set_deleted(root,rid,True)
    (root/'project.json').write_text(json.dumps({'revisions':[]}))
    assert list_deleted(root)[0]['revision_id']==rid
    set_deleted(root,rid,False)
    assert json.loads((root/'project.json').read_text())['revisions']==[row]


def test_thumbnail_is_generated_once_locally(tmp_path,monkeypatch):
    from engine.api.thumbnails import thumbnail
    root=source_folder(tmp_path);calls=[]
    def render(cmd,**kwargs):
        calls.append(cmd);Path(cmd[-1]).write_bytes(b'JPEG-fixture');return SimpleNamespace(returncode=0)
    monkeypatch.setattr('engine.api.thumbnails.subprocess.run',render)
    first=thumbnail(root,'ffmpeg')
    assert first.read_bytes()==b'JPEG-fixture'
    assert thumbnail(root,'ffmpeg')==first and len(calls)==1
