import pytest
from engine.contracts import Source, TranscriptArtifact, Word, Segment
from engine.pipeline.artifacts import atomic_json, file_hash

TOKEN = 'test-session-token'

@pytest.fixture
def client(tmp_path):
    from fastapi.testclient import TestClient
    from engine.api.app import create_app
    app = create_app(tmp_path, TOKEN)
    with TestClient(app, base_url='http://127.0.0.1:8765', headers={'Authorization': 'Bearer ' + TOKEN}) as c:
        yield c

def project_with_transcript(tmp_path):
    root = tmp_path / 'project_edit'; root.mkdir()
    media = root / 'original.mp4'; media.write_bytes(b'video')
    source = Source(local_path=media, sha256=file_hash(media), original_title='Vídeo', duration_us=10_000_000)
    words = [
        Word(id='w0', text='Primeira', start_us=0, end_us=1_000_000),
        Word(id='w1', text='frase', start_us=1_000_000, end_us=2_000_000),
    ]
    segments = [
        Segment(id='s0', text='Primeira frase', start_us=0, end_us=2_000_000, word_ids=['w0', 'w1'])
    ]
    atomic_json(root / 'source.json', source)
    atomic_json(root / 'transcript.json', TranscriptArtifact(
        source_id=source.id,
        source_sha256=source.sha256,
        words=words,
        segments=segments,
    ))
    return root

def test_put_transcript_updates_content_and_word_count(client, tmp_path):
    folder = project_with_transcript(tmp_path)
    import_resp = client.post('/api/v1/projects/import', json={'path': str(folder)})
    assert import_resp.status_code == 200
    pid = import_resp.json()['id']

    # Update segment s0
    put_resp = client.put(f'/api/v1/projects/{pid}/transcript', json={
        'segments': [{'id': 's0', 'text': 'Segunda frase modificada'}]
    })
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data['segments'][0]['text'] == 'Segunda frase modificada'

    # Check detail word count reflects new word count
    detail = client.get(f'/api/v1/projects/{pid}').json()
    assert detail['word_count'] == 3
