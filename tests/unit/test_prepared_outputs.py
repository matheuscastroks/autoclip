import json
from pathlib import Path

import pytest

from test_review_export_gate import revision_project
from engine.contracts import CropArtifact, EDLArtifact, PipelineError, Source
from engine.pipeline.artifacts import atomic_json, file_hash


def prepared_project(tmp_path):
    from engine.pipeline.outputs import save_preparation

    root, folder, rid = revision_project(tmp_path)
    edl = EDLArtifact.model_validate_json((folder / 'edl.json').read_bytes())
    atomic_json(folder / 'crop.json', CropArtifact(source_id=edl.source_id, edl_revision_id=rid))
    save_preparation(root, folder, analysis_hash='a' * 64, plan_hash='b' * 64)
    (folder / 'render.json').unlink()
    (folder / 'qa.json').unlink()
    return root, folder, rid


def fake_render(self, source, edl, crop, caps, config):
    from engine.contracts import RenderArtifact

    config.output_root.mkdir(parents=True, exist_ok=True)
    path = config.output_root / f'{edl.revision_id}.mp4'
    path.write_bytes(config.profile.name.encode())
    return RenderArtifact(revision_id=edl.revision_id, path=path, sha256=file_hash(path), size_bytes=path.stat().st_size)


def test_preview_is_independent_and_final_reuses_shared_files(tmp_path, monkeypatch):
    from engine.pipeline import outputs
    from engine.contracts import PREVIEW_PROFILE, FINAL_PROFILE, ExportValidation

    root, folder, rid = prepared_project(tmp_path)
    before = {p.name: p.read_bytes() for p in folder.iterdir() if p.suffix in ('.json', '.ass', '.srt')}
    monkeypatch.setattr(outputs.FFmpegRenderer, 'render', fake_render)
    monkeypatch.setattr(outputs, 'tool_fingerprint', lambda _: {})
    monkeypatch.setattr(outputs, 'verify_preview', lambda *a, **k: {'dimensions': True, 'duration': True})
    monkeypatch.setattr(outputs, 'verify_render', lambda *a, **k: ExportValidation(revision_id=rid, technical_pass=True, checks={}))
    preview, reused = outputs.render_output(root, rid, PREVIEW_PROFILE, Path('ffmpeg'), Path('ffprobe'))
    assert not reused and preview.profile.name == 'preview'
    assert (folder / 'preview.json').is_file()
    assert not (folder / 'render.json').exists() and not (folder / 'qa.json').exists()
    final, _ = outputs.render_output(root, rid, FINAL_PROFILE, Path('ffmpeg'), Path('ffprobe'))
    assert final.path != preview.render.path and (folder / 'qa.json').is_file()
    for name, content in before.items():
        assert (folder / name).read_bytes() == content
    _, reused = outputs.render_output(root, rid, FINAL_PROFILE, Path('ffmpeg'), Path('ffprobe'))
    assert reused
    assert not (folder / 'review.json').exists()


def test_corruption_or_cancel_preserves_completed_preview(tmp_path, monkeypatch):
    from engine.pipeline import outputs
    from engine.contracts import PREVIEW_PROFILE, FINAL_PROFILE

    root, folder, rid = prepared_project(tmp_path)
    monkeypatch.setattr(outputs.FFmpegRenderer, 'render', fake_render)
    monkeypatch.setattr(outputs, 'tool_fingerprint', lambda _: {})
    monkeypatch.setattr(outputs, 'verify_preview', lambda *a, **k: {'dimensions': True})
    preview, _ = outputs.render_output(root, rid, PREVIEW_PROFILE, Path('f'), Path('p'))
    with pytest.raises(PipelineError, match='Cancellation'):
        outputs.render_output(root, rid, FINAL_PROFILE, Path('f'), Path('p'), cancelled=lambda: True)
    (folder / 'captions.ass').write_text('unexpected change')
    with pytest.raises(PipelineError) as error:
        outputs.render_output(root, rid, FINAL_PROFILE, Path('f'), Path('p'))
    assert error.value.code == 'PREPARATION_CHANGED'
    assert preview.render.path.is_file() and (folder / 'preview.json').is_file()
    assert not (folder / 'render.json').exists()


def test_final_entrypoint_never_invokes_editorial_pipeline(tmp_path, monkeypatch):
    from engine.pipeline import runner, outputs
    from engine.contracts import ExportValidation

    root, folder, rid = prepared_project(tmp_path)
    monkeypatch.setattr(runner, 'run_project', lambda *a, **kw: pytest.fail('No ASR/AI or replanning'))
    monkeypatch.setattr(outputs.FFmpegRenderer, 'render', fake_render)
    monkeypatch.setattr(outputs, 'tool_fingerprint', lambda _: {})
    monkeypatch.setattr(outputs, 'verify_render', lambda *a, **kw: ExportValidation(revision_id=rid, technical_pass=True, checks={}))
    result = runner.render_final(root, [str(rid)], Path('f'), Path('p'))
    assert result.status == 'needs_review'
    assert json.loads((folder / 'render.json').read_text())['revision_id'] == str(rid)
    with pytest.raises(PipelineError) as error:
        runner.export_approved(root)
    assert error.value.code == 'NO_APPROVED_CLIPS'


def test_source_timing_metadata_is_bound_to_preparation(tmp_path):
    from engine.pipeline.outputs import load_preparation

    root, folder, rid = prepared_project(tmp_path)
    source=Source.model_validate_json((root/'source.json').read_bytes())
    source.probe['video_origin_us']=10_000_000
    atomic_json(root/'source.json',source)
    with pytest.raises(PipelineError) as error:
        load_preparation(root,rid)
    assert error.value.code=='PREPARATION_CHANGED'


def test_missing_cache_checkpoint_does_not_discard_published_preview(tmp_path,monkeypatch):
    from engine.pipeline import outputs
    from engine.contracts import PREVIEW_PROFILE
    root,folder,rid=prepared_project(tmp_path)
    monkeypatch.setattr(outputs.FFmpegRenderer,'render',fake_render)
    monkeypatch.setattr(outputs,'tool_fingerprint',lambda _: {})
    monkeypatch.setattr(outputs,'verify_preview',lambda *a: {'fixture':True})
    preview,_=outputs.render_output(root,rid,PREVIEW_PROFILE,Path('f'),Path('p'))
    for checkpoint in (root/'stages/output_preview').glob('*.json'):checkpoint.unlink()
    monkeypatch.setattr(outputs.FFmpegRenderer,'render',lambda *a: pytest.fail('Published output must survive cache metadata loss'))
    restored,reused=outputs.render_output(root,rid,PREVIEW_PROFILE,Path('f'),Path('p'))
    assert reused and restored.render.path==preview.render.path
    assert preview.render.path.read_bytes()==b'preview'
