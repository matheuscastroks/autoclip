import pytest
from test_projects import client,source_folder

def test_partial_project_cannot_approve_or_export(client,tmp_path):
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    assert client.get(f'/api/v1/projects/{pid}/revisions').json()==[]
    assert client.post(f'/api/v1/projects/{pid}/revisions/unknown/decision',json={'decision':'approved','checks':{'completeness':True,'context':True,'qualifications':True,'words_and_boundaries':True,'audiovisual':True},'notes':'Fixture','content_hash':'a'*64}).status_code in (400,404)
    assert client.post(f'/api/v1/projects/{pid}/exports').status_code==400

def test_cancelled_native_picker_does_not_create_project(client,monkeypatch):
    from engine.api import native
    monkeypatch.setattr(native,'pick',lambda _:None)
    assert client.post('/api/v1/picker',json={'kind':'project'}).json()['path'] is None
    assert client.get('/api/v1/projects').json()==[]
