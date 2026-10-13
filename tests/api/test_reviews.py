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

@pytest.mark.parametrize('operation,expected',[('transcribe',200),('analyze',200),('render',409),('export',409),('prepare',409),('import',409)])
def test_delete_cut_only_blocks_operations_that_can_modify_delivery(client,tmp_path,monkeypatch,operation,expected):
    from engine.api import reviews
    root=source_folder(tmp_path)
    pid=client.post('/api/v1/projects/import',json={'path':str(root)}).json()['id']
    monkeypatch.setattr(client.app.state.store,'jobs',lambda:[{'id':'job','project_id':pid,'operation':operation}])
    monkeypatch.setattr(client.app.state.jobs,'status',lambda _: {'status':'running'})
    calls=[]
    monkeypatch.setattr(reviews,'set_deleted',lambda *args: calls.append(args) or {'deleted':True})
    assert client.delete(f'/api/v1/projects/{pid}/revisions/cut').status_code==expected
    assert len(calls)==(1 if expected==200 else 0)
