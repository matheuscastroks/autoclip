from test_projects import client,source_folder
from engine.contracts import Source,ProjectRun
from engine.pipeline.artifacts import atomic_json
from uuid import uuid4

def test_missing_revision_is_an_invalid_row_not_a_project_failure(client,tmp_path):
    root=source_folder(tmp_path);source=Source.model_validate_json((root/'source.json').read_bytes());rid=str(uuid4())
    atomic_json(root/'project.json',ProjectRun(source=source,status='needs_review',revisions=[{'revision_id':rid}]))
    pid=client.post('/api/v1/projects/import',json={'path':str(root)}).json()['id']
    response=client.get(f'/api/v1/projects/{pid}/revisions')
    assert response.status_code==200
    assert response.json()[0]['review_status']=='invalid'
    assert client.get(f'/api/v1/projects/{pid}/transcript').status_code==200
