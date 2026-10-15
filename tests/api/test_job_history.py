import shutil

from test_projects import client
from engine.api.store import now


def add_job(client, job_id, status):
    manager = client.app.state.jobs
    manager.draining = True
    manager.store.save_job({'id': job_id, 'project_id': 'fixture', 'operation': 'render', 'status': status, 'created_at': now()})
    folder = manager.root / job_id
    folder.mkdir()
    (folder / 'request.json').write_text('{}')
    (folder / 'stdout.log').write_text('fixture')
    return folder


def test_clear_history_removes_disposable_files_but_retains_resume_data(client):
    completed = add_job(client, 'completed', 'completed')
    failed = add_job(client, 'failed', 'failed')
    active = add_job(client, 'pending', 'pending')
    response = client.post('/api/v1/jobs/clear-history')
    assert response.json() == {'cleared': 1, 'preserved': 1, 'errors': []}
    assert not completed.exists()
    assert (failed / 'request.json').is_file()
    assert (active / 'request.json').is_file()
    assert {row['id'] for row in client.app.state.store.jobs()} == {'failed', 'pending'}


def test_failed_cleanup_preserves_history_for_retry(client, monkeypatch):
    folder = add_job(client, 'completed', 'completed')
    monkeypatch.setattr(shutil, 'rmtree', lambda path: (_ for _ in ()).throw(PermissionError('fixture')))
    response = client.post('/api/v1/jobs/clear-history')
    assert response.json()['cleared'] == 0
    assert response.json()['errors'][0]['job_id'] == 'completed'
    assert folder.is_dir()
    assert client.app.state.store.job('completed')


def test_clear_history_rejects_paths_outside_jobs_root(client):
    manager = client.app.state.jobs
    manager.draining = True
    outside = manager.root.parent / 'outside'
    outside.mkdir()
    (outside / 'keep').write_text('fixture')
    manager.store.save_job({'id': '../outside', 'project_id': 'fixture', 'status': 'completed', 'created_at': now()})
    response = client.post('/api/v1/jobs/clear-history')
    assert response.json()['cleared'] == 0
    assert response.json()['errors']
    assert (outside / 'keep').read_text() == 'fixture'
