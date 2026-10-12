import os
from pathlib import Path
import pytest

@pytest.mark.real_media
def test_pipeline_real_source_matches_and_exports_are_traceable():
    if os.environ.get('AUTOCLIP_REAL_PROJECT') is None:pytest.skip('Set AUTOCLIP_REAL_PROJECT after a real Gemini run with locally configured credentials.')
    import json
    from engine.contracts import ProjectRun,RenderArtifact,EDLArtifact,CaptionArtifact
    from engine.pipeline.artifacts import file_hash
    root=Path(os.environ['AUTOCLIP_REAL_PROJECT'])
    state=ProjectRun.model_validate_json((root/'project.json').read_bytes())
    assert state.source.sha256=='bc190e8b2d93ab3c3d9d413402d3c11da1a060ea45b2e3ac961f5417cf19c396'
    assert file_hash(state.source.local_path)==state.source.sha256
    analysis=json.loads((root/'analysis.json').read_text(encoding='utf-8'))
    assert analysis['complete'] and analysis['payload_hashes']
    assert len(state.revisions)<=3
    for r in state.revisions:
        folder=root/'revisions'/r['revision_id']
        e=EDLArtifact.model_validate_json((folder/'edl.json').read_bytes())
        c=CaptionArtifact.model_validate_json((folder/'captions.json').read_bytes())
        render=RenderArtifact.model_validate_json((folder/'render.json').read_bytes())
        assert 20_000_000<=e.duration_us<=60_000_000
        assert file_hash(render.path)==render.sha256
        assert c.edl_revision_id==e.revision_id
