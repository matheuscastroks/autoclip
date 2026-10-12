from test_projects import client,source_folder,TOKEN

def test_auth_and_origin_are_required(client):
    assert client.get('/api/v1/projects',headers={'Authorization':'Bearer wrong'}).status_code==401
    assert client.get('/api/v1/projects',headers={'Origin':'https://evil.example'}).status_code==403
    assert client.get('/api/v1/projects',headers={'Origin':'http://127.0.0.1:8765'}).status_code==200
    assert client.get('/api/v1/projects',headers={'Host':'evil.example'}).status_code==403

def test_media_ticket_and_range(client,tmp_path):
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    ticket=client.get(f'/api/v1/projects/{pid}/media/source/ticket').json()['url']
    r=client.get(ticket,headers={'Authorization':'','Range':'bytes=0-3'})
    assert r.status_code==206 and r.content==b'test'
    assert client.get(ticket.replace('source?', 'unknown?'),headers={'Authorization':''}).status_code in (401,403,404)
    assert client.get(f'/api/v1/projects/{pid}/media/source',headers={'Authorization':''}).status_code==401

def test_declared_output_outside_project_is_not_served(client,tmp_path):
    root=source_folder(tmp_path)
    from engine.pipeline.artifacts import atomic_json
    from engine.contracts import ProjectRun,Source
    source=Source.model_validate_json((root/'source.json').read_bytes())
    atomic_json(root/'project.json',ProjectRun(source=source,status='needs_review',revisions=[{'revision_id':'abc','render_path':str(tmp_path/'private.mp4')}]))
    pid=client.post('/api/v1/projects/import',json={'path':str(root)}).json()['id']
    assert client.get(f'/api/v1/projects/{pid}/media/abc/ticket').status_code==404
