from pathlib import Path
import pytest

def test_local_source_is_not_overwritten(tmp_path):
    from engine.media.importer import import_source
    from engine.pipeline.artifacts import file_hash
    p = tmp_path/"Vídeo d'água 01.mp4"
    p.write_bytes(b'original')
    s = import_source(str(p), tmp_path/'project')
    assert s.sha256 == file_hash(p)
    assert p.read_bytes() == b'original'
    assert s.local_path == p.resolve()

def test_url_download_failure_does_not_publish_partial(tmp_path, monkeypatch):
    from engine.media import importer
    from engine.contracts import PipelineError
    def fail(url, root): raise RuntimeError('network unavailable')
    monkeypatch.setattr(importer, '_download', fail)
    with pytest.raises(PipelineError) as error:
        importer.import_source('https://www.youtube.com/watch?v=example', tmp_path)
    assert error.value.code=='SOURCE_UNAVAILABLE'
    assert not (tmp_path/'source.json').exists()

def test_artifact_path_is_content_addressed_and_validated(tmp_path):
    from engine.pipeline.artifacts import write_artifact, read_artifact
    from engine.contracts import Word, PipelineError
    w = Word(id='w1',text='a',start_us=0,end_us=10)
    ref = write_artifact(w,'word',tmp_path)
    assert read_artifact(ref,tmp_path,Word) == w
    (tmp_path/ref.relative_path).write_text('{}')
    with pytest.raises(PipelineError): read_artifact(ref,tmp_path,Word)

def test_url_download_progress_hook_honors_cancellation(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    from engine.media import importer
    from engine.contracts import PipelineError
    monkeypatch.setattr('engine.media.probe.locate_tools', lambda: (tmp_path / 'ffmpeg.exe', tmp_path / 'ffprobe.exe'))
    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def extract_info(self, url, download=True):
            for hook in self.opts.get('progress_hooks', []):
                hook({'downloaded_bytes': 1024, 'total_bytes': 4096})
            return {'title': 'Fixture'}
    monkeypatch.setitem(sys.modules, 'yt_dlp', SimpleNamespace(YoutubeDL=FakeYDL))
    with pytest.raises(PipelineError) as exc:
        importer.import_source('https://www.youtube.com/watch?v=example', tmp_path, cancelled=lambda: True)
    assert exc.value.code == 'CANCELLED'

