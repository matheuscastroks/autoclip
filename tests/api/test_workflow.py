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


def test_automatic_creation_without_checkbox_uses_automatic_requests(client,monkeypatch):
    monkeypatch.setattr('engine.api.settings.get_gemini_key',lambda:'fixture')
    client.app.state.jobs.spawn=lambda *a,**kw:SimpleNamespace(pid=0,poll=lambda:None)
    response=client.post('/api/v1/projects',json={'name':'Automatic','source_input':'fixture.mp4','automatic':True})
    assert response.status_code==200
    job=response.json()['job']
    assert job['request_mode']=='automatic' and job['request_limit'] is None
    request=json.loads((client.app.state.jobs.root/job['id']/'request.json').read_text())
    assert request['settings']['automatic_calls'] is True


def test_active_project_cannot_be_deleted(client,tmp_path):
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    jobs=client.app.state.jobs
    class Process:
        pid=0
        def poll(self):return None
    jobs.spawn=lambda *a,**kw:Process()
    jobs.start(pid,'transcribe',{})
    assert client.delete('/api/v1/projects/'+pid).status_code==409


def test_prepare_without_checkbox_can_restart_with_new_automatic_ledger(client,tmp_path):
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    class Process:
        pid=0
        def poll(self):return None
    jobs=client.app.state.jobs;jobs.spawn=lambda *a,**kw:Process()
    job=jobs.start(pid,'prepare',{})
    assert job['operation']=='prepare'
    folder=jobs.root/job['id']
    (folder/'result.json').write_text(json.dumps({'status':'failed'}))
    resumed=jobs.resume(job['id'])
    assert resumed['id']!=job['id'] and resumed['request_mode']=='automatic'


def test_automatic_policy_covers_actual_windows_despite_saved_one_call(tmp_path):
    from engine.api.job_worker import configure_analysis_requests,pipeline_config
    from engine.contracts import TranscriptArtifact,Word
    from engine.adapters.openshorts.windows import build_windows
    from uuid import uuid4
    transcript=TranscriptArtifact(source_id=uuid4(),source_sha256='a'*64,words=[Word(id=f'w{i}',text='fala',start_us=i*10_000_000,end_us=i*10_000_000+1_000_000) for i in range(210)])
    config=pipeline_config({'asr_model_path':str(tmp_path),'gemini_model':'fixture','max_calls':1,'window_seconds':600,'max_text_chars':60000,'ffmpeg':'ffmpeg','ffprobe':'ffprobe'},tmp_path)
    configure_analysis_requests(config,transcript,{'automatic_calls':True},tmp_path)
    count=len(build_windows(transcript,600,60000))
    assert count>1 and config.analysis.max_calls==4*count
    policy=json.loads((tmp_path/'request-policy.json').read_text())
    assert policy['windows']==count and policy['request_mode']=='automatic'
    from engine.pipeline.request_budget import RequestBudget
    budget=RequestBudget(tmp_path/'budget.sqlite',config.analysis.max_calls)
    for i in range(count):budget.reserve(str(i))
    assert budget.used==count


def test_automatic_policy_rejects_empty_transcript_without_requests(tmp_path):
    from engine.api.job_worker import configure_analysis_requests,pipeline_config
    from engine.contracts import TranscriptArtifact,PipelineError
    from uuid import uuid4
    config=pipeline_config({'asr_model_path':str(tmp_path),'gemini_model':'fixture','max_calls':1,'window_seconds':600,'max_text_chars':60000,'ffmpeg':'ffmpeg','ffprobe':'ffprobe'},tmp_path)
    transcript=TranscriptArtifact(source_id=uuid4(),source_sha256='a'*64,words=[])
    with pytest.raises(PipelineError) as error:configure_analysis_requests(config,transcript,{'automatic_calls':True},tmp_path)
    assert error.value.code=='NO_SPEECH' and not (tmp_path/'budget.sqlite').exists()


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
