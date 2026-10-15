from types import SimpleNamespace
from uuid import uuid4

from engine.contracts import *
from engine.pipeline.artifacts import atomic_json, file_hash, object_hash


def test_preview_then_final_reuses_preparation_without_ai_or_asr(tmp_path, monkeypatch):
    from engine.pipeline import runner, outputs

    root = tmp_path / 'project'
    root.mkdir()
    media = root / 'source.mp4'
    media.write_bytes(b'synthetic stand-in')
    source = Source(local_path=media, sha256=file_hash(media), duration_us=30_000_000)
    audio_path = root / 'audio.wav'
    audio_path.write_bytes(b'audio')
    audio = AudioArtifact(source_id=source.id, source_sha256=source.sha256,
                          path=audio_path, sha256=file_hash(audio_path), duration_us=30_000_000)
    transcript = TranscriptArtifact(source_id=source.id, source_sha256=source.sha256, words=[
        Word(id='w1', text='Primeira', start_us=0, end_us=1_000_000),
        Word(id='w2', text='última', start_us=29_000_000, end_us=30_000_000),
    ])
    candidate = Candidate(topic_id='t', start_word_id='w1', end_word_id='w2',
                          evidence_word_ids=['w1', 'w2'], rationale='Synthetic fixture',
                          editorial=EditorialFlags(completeness='yes', standalone_context='yes', qualification_preserved='yes'))
    analysis = AnalysisArtifact(transcript_id=transcript.transcript_id, candidates=[candidate],
        complete=True, covered_word_ids=['w1', 'w2'], model='fixture', prompt_hash='fixture', payload_hashes=[])
    config = PipelineConfig(asr=ASRConfig(model_path=tmp_path), reframe=ReframeConfig(enabled=False), analysis=AnalysisConfig(model='fixture', max_calls=1),
        export=ExportConfig(output_root=root/'unused'), ffmpeg=tmp_path/'ffmpeg', ffprobe=tmp_path/'ffprobe')
    monkeypatch.setattr(runner, 'probe_source', lambda *a: source)
    monkeypatch.setattr(runner, 'extract_audio', lambda *a: audio)
    monkeypatch.setattr(runner, 'tool_fingerprint', lambda *a: {})
    monkeypatch.setattr(outputs, 'tool_fingerprint', lambda *a: {})
    calls = []
    def render(self, source, edl, crop, caps, config):
        calls.append(config.profile.name)
        config.output_root.mkdir(parents=True, exist_ok=True)
        path = config.output_root / 'output.mp4'
        path.write_bytes(config.profile.name.encode())
        return RenderArtifact(revision_id=edl.revision_id, path=path, sha256=file_hash(path), size_bytes=path.stat().st_size)
    monkeypatch.setattr(outputs.FFmpegRenderer, 'render', render)
    monkeypatch.setattr(outputs, 'verify_preview', lambda *a: {'fixture': True})
    monkeypatch.setattr(outputs, 'verify_render', lambda render, *a: ExportValidation(revision_id=render.revision_id, technical_pass=True, checks={}))
    def preview():
        return runner.run_project(source, config, root, transcriber=SimpleNamespace(transcribe=lambda *a: transcript),
            precomputed_analysis=analysis, candidate_ids=[str(candidate.id)], analysis_hash=object_hash(analysis), stop_after='preview')
    first = preview()
    assert first.status == 'needs_review'
    rid = first.revisions[0]['revision_id']
    folder = root/'revisions'/rid
    shared = {name: (folder/name).read_bytes() for name in ('edl.json', 'captions.json', 'crop.json', 'prepared.json')}
    assert not (folder/'render.json').exists()
    second = preview()
    assert second.revisions[0]['revision_id'] == rid
    assert calls == ['preview']
    monkeypatch.setattr(runner, 'run_project', lambda *a, **kw: (_ for _ in ()).throw(AssertionError('No upstream work')))
    runner.render_final(root, [rid], config.ffmpeg, config.ffprobe)
    assert calls == ['preview', 'final']
    assert all((folder/name).read_bytes() == value for name, value in shared.items())
