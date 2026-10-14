import json
from pathlib import Path
import pytest

TOKEN='test-session-token'

@pytest.fixture
def client(tmp_path):
    from fastapi.testclient import TestClient
    from engine.api.app import create_app
    app=create_app(tmp_path,TOKEN)
    with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Authorization':'Bearer '+TOKEN}) as c:
        yield c

def source_folder(tmp_path):
    from engine.contracts import Source,TranscriptArtifact,Word
    from engine.pipeline.artifacts import atomic_json,file_hash
    root=tmp_path/'vídeo com espaços';root.mkdir()
    media=root/'original.mp4';media.write_bytes(b'test video content')
    source=Source(local_path=media,sha256=file_hash(media),original_title='Uma conversa',duration_us=30_000_000)
    atomic_json(root/'source.json',source)
    atomic_json(root/'transcript.json',TranscriptArtifact(source_id=source.id,source_sha256=source.sha256,words=[Word(id='w1',text='Olá',start_us=0,end_us=1_000_000)]))
    return root

def test_register_partial_project_without_inventing_clips(client,tmp_path):
    folder=source_folder(tmp_path)
    response=client.post('/api/v1/projects/import',json={'path':str(folder)})
    assert response.status_code==200
    pid=response.json()['id']
    assert client.post('/api/v1/projects/import',json={'path':str(folder)}).json()['id']==pid
    assert len(client.get('/api/v1/projects').json())==1
    detail=client.get('/api/v1/projects/'+pid).json()
    assert detail['has_transcript'] and detail['status']=='transcribed'
    assert detail['revisions']==[]
    transcript=client.get(f'/api/v1/projects/{pid}/transcript').json()
    assert transcript['words'][0]['text']=='Olá'

def test_malformed_artifact_is_visible_as_warning(client,tmp_path):
    root=source_folder(tmp_path);(root/'transcript.json').write_text('{broken')
    detail=client.post('/api/v1/projects/import',json={'path':str(root)}).json()
    assert detail['warnings'] and not detail['has_transcript']

def test_registry_survives_restart(tmp_path):
    from engine.api.store import ProjectStore
    root=source_folder(tmp_path);db=tmp_path/'library.sqlite'
    first=ProjectStore(db).register(root)
    assert ProjectStore(db).get(first['id'])['path']==str(root.resolve())

def test_config_and_credential_never_return_secret(client,monkeypatch):
    client.app.state.gemini_connection.catalog=lambda key:[]
    import engine.api.settings as settings
    saved=[]
    monkeypatch.setattr(settings,'set_gemini_key',lambda key:saved.append(key))
    monkeypatch.setattr(settings,'get_gemini_key',lambda:'secret-fixture-key')
    r=client.put('/api/v1/config/credential',json={'key':'secret-fixture-key'})
    assert r.status_code==200 and saved==['secret-fixture-key']
    assert 'secret-fixture-key' not in r.text
    assert 'secret-fixture-key' not in client.get('/api/v1/config').text

def test_import_missing_path_returns_readable_failure(client):
    r=client.post('/api/v1/projects/import',json={'path':'missing/not/a/project'})
    assert r.status_code==400 and r.json()['detail']

def test_permanent_delete_removes_managed_folder_and_sqlite_record(client,tmp_path):
    # Criar projeto gerenciado
    r=client.post('/api/v1/projects',json={'name':'Test Project','source_input':str(source_folder(tmp_path)),'automatic':False})
    assert r.status_code==200
    pid=r.json()['project']['id']
    job_id=r.json()['job']['id']
    proj_dir=Path(r.json()['project']['path'])
    assert proj_dir.is_dir()

    # Tentativa com job ativo deve retornar 409 (Review Focus #1)
    conflict_res=client.delete(f'/api/v1/projects/{pid}?permanent=true')
    assert conflict_res.status_code==409

    # Marcar job como concluído
    job=client.app.state.store.job(job_id)
    job['status']='completed'
    job['finished_at']='2026-10-14T00:00:00Z'
    client.app.state.store.save_job(job)

    # Excluir permanentemente
    del_res=client.delete(f'/api/v1/projects/{pid}?permanent=true')
    assert del_res.status_code==200
    assert del_res.json()=={'deleted':True}

    # Verificar que diretório gerenciado foi removido fisicamente
    assert not proj_dir.exists()
    # E que projeto sumiu do banco
    get_res=client.get(f'/api/v1/projects/{pid}')
    assert get_res.status_code==404


def test_clear_job_history_removes_only_terminal_jobs(client):
    from engine.api.store import now
    store=client.app.state.store
    # Inserir jobs em vários estados
    store.save_job({'id':'job-comp','project_id':'p1','status':'completed','created_at':now()})
    store.save_job({'id':'job-fail','project_id':'p1','status':'failed','created_at':now()})
    store.save_job({'id':'job-run','project_id':'p1','status':'running','created_at':now()})

    res=client.post('/api/v1/jobs/clear-history')
    assert res.status_code==200
    assert res.json()['cleared']>=2

    # Job em execução deve permanecer
    assert client.get('/api/v1/jobs').status_code in (200, 404, 405) # ou verificar via store
    remaining_ids=[j['id'] for j in store.jobs()]
    assert 'job-run' in remaining_ids
    assert 'job-comp' not in remaining_ids
    assert 'job-fail' not in remaining_ids

