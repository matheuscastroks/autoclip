from pathlib import Path

from fastapi.testclient import TestClient

from test_prepared_outputs import prepared_project, fake_render
from engine.contracts import PREVIEW_PROFILE


def test_preview_listing_ticket_and_final_queue_are_distinct(tmp_path, monkeypatch):
    from engine.api.app import create_app
    from engine.pipeline import outputs

    root, folder, rid = prepared_project(tmp_path)
    monkeypatch.setattr(outputs.FFmpegRenderer, 'render', fake_render)
    monkeypatch.setattr(outputs, 'tool_fingerprint', lambda _: {})
    monkeypatch.setattr(outputs, 'verify_preview', lambda *a: {'dimensions': True})
    outputs.render_output(root, rid, PREVIEW_PROFILE, Path('f'), Path('p'))
    app = create_app(tmp_path/'workspace', 'fixture-token')
    app.state.jobs.dispatch = lambda: None
    with TestClient(app, base_url='http://127.0.0.1', headers={'Authorization': 'Bearer fixture-token'}) as client:
        pid = app.state.store.register(root)['id']
        rows = client.get(f'/api/v1/projects/{pid}/revisions').json()
        assert rows[0]['preview']['state'] == 'available'
        assert rows[0]['final_state'] == 'not_generated'
        assert not rows[0]['technical_pass'] and rows[0]['review_status'] != 'approved'
        ticket = client.get(f'/api/v1/projects/{pid}/media/preview-{rid}/ticket')
        assert ticket.status_code == 200
        assert client.get(ticket.json()['url'], headers={'Authorization': ''}).content == b'preview'
        assert client.get(f'/api/v1/projects/{pid}/media/{rid}/ticket').status_code == 404
        payload = {'operation': 'render_final', 'options': {'revision_ids': [str(rid)]}}
        first = client.post(f'/api/v1/projects/{pid}/jobs', json=payload)
        assert first.status_code == 200, first.text
        assert first.json()['operation'] == 'render_final'
        assert client.post(f'/api/v1/projects/{pid}/jobs', json=payload).json()['id'] == first.json()['id']
        assert client.post(f'/api/v1/jobs/{first.json()["id"]}/cancel').json()['status'] == 'cancelled'
        resumed = client.post(f'/api/v1/jobs/{first.json()["id"]}/resume')
        assert resumed.status_code == 200 and resumed.json()['operation'] == 'render_final'
        assert not (folder/'render.json').exists()


def test_preview_path_cannot_escape_project(tmp_path, monkeypatch):
    from engine.api.media import asset_path
    from engine.pipeline import outputs
    from engine.pipeline.artifacts import atomic_json
    from fastapi import HTTPException
    import pytest

    root, folder, rid = prepared_project(tmp_path)
    monkeypatch.setattr(outputs.FFmpegRenderer, 'render', fake_render)
    monkeypatch.setattr(outputs, 'tool_fingerprint', lambda _: {})
    monkeypatch.setattr(outputs, 'verify_preview', lambda *a: {'dimensions': True})
    preview, _ = outputs.render_output(root, rid, PREVIEW_PROFILE, Path('f'), Path('p'))
    preview.render.path = tmp_path/'outside.mp4'
    preview.render.path.write_bytes(b'preview')
    atomic_json(folder/'preview.json', preview)
    with pytest.raises(HTTPException):
        asset_path(root, f'preview-{rid}')
