import pytest
from engine.contracts import PipelineError

def test_youtube_block_is_actionable_without_raw_provider_text(tmp_path,monkeypatch):
    from engine.media import importer
    def fail(*args):raise RuntimeError("Sign in to confirm you're not a bot. --cookies secret=value")
    monkeypatch.setattr(importer,'_download',fail)
    with pytest.raises(PipelineError) as info:importer.import_source('https://youtu.be/fixture',tmp_path)
    assert info.value.code=='SOURCE_AUTH_REQUIRED'
    assert 'arquivo local' in str(info.value)
    assert 'secret' not in str(info.value)

def test_missing_file_has_source_specific_message(tmp_path):
    from engine.media.importer import import_source
    with pytest.raises(PipelineError) as info:import_source(str(tmp_path/'missing.mp4'),tmp_path/'project')
    assert info.value.code=='SOURCE_NOT_FOUND'
    assert 'Gemini' not in str(info.value)

def test_invalid_media_is_not_published_as_imported(tmp_path,monkeypatch):
    from engine.api import job_worker
    media=tmp_path/'bad.mp4';media.write_bytes(b'not video')
    root=tmp_path/'project'
    def fail(*args):raise PipelineError('SOURCE_UNAVAILABLE','probe','ffprobe cannot read it')
    monkeypatch.setattr(job_worker,'probe_source',fail)
    with pytest.raises(PipelineError) as info:job_worker.import_probed(str(media),root,tmp_path/'ffprobe')
    assert info.value.code=='SOURCE_INVALID'
    assert not (root/'source.json').exists()
