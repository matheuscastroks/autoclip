from uuid import uuid4

import pytest
from pydantic import ValidationError

from test_projects import client, source_folder
from engine.contracts import ProjectRun, Source
from engine.contracts.api import Project, Job, Revision, AnalysisView
from engine.pipeline.artifacts import atomic_json
from scripts.generate_api_types import TARGET, render_types


def test_generated_types_match_pydantic_contracts():
    assert TARGET.read_text(encoding='utf-8') == render_types(), 'Run python scripts/generate_api_types.py'


def test_real_api_responses_follow_shared_contracts(client, tmp_path):
    root = source_folder(tmp_path)
    source = Source.model_validate_json((root / 'source.json').read_bytes())
    # A missing revision must have a defined invalid response, not a different shape of state.
    atomic_json(root / 'project.json', ProjectRun(source=source, status='needs_review', revisions=[{'revision_id': str(uuid4())}]))
    response = client.post('/api/v1/projects/import', json={'path': str(root)})
    project = Project.model_validate(response.json())
    assert project.has_transcript
    assert Project.model_validate(client.get(f'/api/v1/projects/{project.id}').json()).status == 'needs_review'
    view = AnalysisView.model_validate(client.get(f'/api/v1/projects/{project.id}/analysis').json())
    assert view.state == 'not_started'
    revision = Revision.model_validate(client.get(f'/api/v1/projects/{project.id}/revisions').json()[0])
    assert revision.review_status == 'invalid' and not revision.technical_pass
    manager = client.app.state.jobs
    manager.draining = True
    manager.store.save_job({'id': 'legacy', 'project_id': project.id, 'status': 'completed', 'finished_at': 'fixture'})
    job = Job.model_validate(client.get('/api/v1/jobs/legacy').json())
    assert job.status == 'completed' and job.events == []
    schemas = client.app.openapi()['components']['schemas']
    assert schemas['Revision']['properties']['review_status']['enum'] == ['invalid', 'needs_review', 'stale_review', 'approved', 'rejected']


@pytest.mark.parametrize('status', ['ready', 'valid', 'technical_pass'])
def test_technical_outcomes_are_not_editorial_decisions(status):
    with pytest.raises(ValidationError):
        Revision(revision_id='fixture', title='Fixture', technical_pass=True, review_status=status, warnings=[])
