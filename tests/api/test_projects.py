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
