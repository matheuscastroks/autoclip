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
        decision = {'decision':'approved','content_hash':'0'*64,'notes':'',
                    'checks':{key:True for key in ('completeness','context','qualifications','words_and_boundaries','audiovisual')}}
        assert client.post(f'/api/v1/projects/{pid}/revisions/{rid}/decision',json=decision).status_code == 400
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


def test_damaged_preparation_preserves_playable_preview_without_reading_source(tmp_path,monkeypatch):
    from engine.pipeline import outputs
    from engine.api.reviews import list_revisions
    root,folder,rid=prepared_project(tmp_path)
    monkeypatch.setattr(outputs.FFmpegRenderer,'render',fake_render)
    monkeypatch.setattr(outputs,'tool_fingerprint',lambda _: {})
    monkeypatch.setattr(outputs,'verify_preview',lambda *a: {'fixture':True})
    outputs.render_output(root,rid,PREVIEW_PROFILE,Path('f'),Path('p'))
    real_hash=outputs.file_hash
    def no_source_read(path):
        assert Path(path).resolve()!=(root/'source.mp4').resolve(), 'Listing must not hash the full source'
        return real_hash(path)
    monkeypatch.setattr(outputs,'file_hash',no_source_read)
    assert list_revisions(root)[0]['preview']['state']=='available'
    (folder/'captions.ass').write_text('damaged')
    row=list_revisions(root)[0]
    assert row['preview']['state']=='available' and not row['can_render_final']
    (folder/'captions.json').write_text('{broken')
    row=list_revisions(root)[0]
    assert row['preview']['state']=='available' and not row['technical_pass']


def test_final_queue_subtracts_overlapping_revisions(tmp_path):
    from uuid import uuid4
    from engine.api.app import create_app
    from engine.contracts import Candidate,CaptionArtifact,CropArtifact,EDLArtifact,ProjectRun
    from engine.pipeline.outputs import save_preparation
    from engine.pipeline.artifacts import atomic_json

    root,folder,rid=prepared_project(tmp_path)
    ids=[str(rid)]
    state=ProjectRun.model_validate_json((root/'project.json').read_bytes())
    for _ in range(2):
        other=uuid4();target=root/'revisions'/str(other);target.mkdir()
        for name,model,field in [('edl',EDLArtifact,'revision_id'),('captions',CaptionArtifact,'edl_revision_id'),('crop',CropArtifact,'edl_revision_id')]:
            artifact=model.model_validate_json((folder/(name+'.json')).read_bytes()).model_copy(update={field:other})
            atomic_json(target/(name+'.json'),artifact)
        atomic_json(target/'candidate.json',Candidate.model_validate_json((folder/'candidate.json').read_bytes()))
        save_preparation(root,target,analysis_hash='a'*64,plan_hash='b'*64)
        ids.append(str(other));state.revisions.append({'revision_id':str(other)})
    atomic_json(root/'project.json',state)
    app=create_app(tmp_path/'queue-workspace','fixture')
    app.state.jobs.dispatch=lambda:None
    with TestClient(app,base_url='http://127.0.0.1',headers={'Authorization':'Bearer fixture'}) as client:
        pid=app.state.store.register(root)['id']
        def start(chosen):return client.post(f'/api/v1/projects/{pid}/jobs',json={'operation':'render_final','options':{'revision_ids':chosen}}).json()
        first=start(ids[:2])
        assert start(list(reversed(ids[:2])))['id']==first['id']
        assert start([ids[1]])['id']==first['id']
        partial=start(ids[1:])
        assert partial['id']!=first['id'] and partial['enqueued_items']==1 and partial['ignored_queued']==1


def test_completed_final_is_playable_after_restart_before_index_update(tmp_path,monkeypatch):
    from engine.pipeline import outputs
    from engine.api.app import create_app
    from engine.contracts import FINAL_PROFILE,ExportValidation
    root,folder,rid=prepared_project(tmp_path)
    monkeypatch.setattr(outputs.FFmpegRenderer,'render',fake_render)
    monkeypatch.setattr(outputs,'tool_fingerprint',lambda _: {})
    monkeypatch.setattr(outputs,'verify_render',lambda *a:ExportValidation(revision_id=rid,technical_pass=True,checks={}))
    outputs.render_output(root,rid,FINAL_PROFILE,Path('f'),Path('p'))
    app=create_app(tmp_path/'restart-workspace','fixture')
    with TestClient(app,base_url='http://127.0.0.1',headers={'Authorization':'Bearer fixture'}) as client:
        pid=app.state.store.register(root)['id']
        ticket=client.get(f'/api/v1/projects/{pid}/media/{rid}/ticket')
        assert ticket.status_code==200,ticket.text
