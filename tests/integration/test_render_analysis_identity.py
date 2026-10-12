from engine.contracts import Source,AudioArtifact,TranscriptArtifact,Word,AnalysisArtifact,PipelineConfig,ASRConfig,AnalysisConfig,ExportConfig
from engine.pipeline.artifacts import atomic_json

def test_precomputed_analysis_does_not_seed_current_model_cache(tmp_path,monkeypatch):
    from engine.pipeline import runner
    source=Source(local_path=tmp_path/'source.mp4',sha256='a'*64,duration_us=30_000_000)
    root=tmp_path/'project';root.mkdir()
    audio=AudioArtifact(source_id=source.id,source_sha256=source.sha256,path=root/'audio.wav',sha256='b'*64,duration_us=30_000_000);audio.path.write_bytes(b'fixture')
    transcript=TranscriptArtifact(source_id=source.id,source_sha256=source.sha256,words=[Word(id='w1',text='Teste',start_us=0,end_us=1_000_000)])
    old=AnalysisArtifact(transcript_id=transcript.transcript_id,complete=True,covered_word_ids=['w1'],model='old-model',prompt_hash='fixture',payload_hashes=['fixture'])
    monkeypatch.setattr(runner,'file_hash',lambda p:source.sha256);monkeypatch.setattr(runner,'tool_fingerprint',lambda p:{})
    monkeypatch.setattr(runner,'probe_source',lambda *a:source);monkeypatch.setattr(runner,'extract_audio',lambda *a:audio)
    class T:
        def transcribe(self,*a):return transcript
    class A:
        def analyze(self,*a,**kw):raise AssertionError('Render must not analyze')
    config=PipelineConfig(asr=ASRConfig(model_path=tmp_path),analysis=AnalysisConfig(model='new-model',max_calls=1),export=ExportConfig(output_root=root/'previews'),ffmpeg=tmp_path/'ffmpeg',ffprobe=tmp_path/'ffprobe')
    state=runner.run_project(source,config,root,transcriber=T(),analyzer=A(),precomputed_analysis=old)
    assert state.status=='no_candidates'
    assert not list((root/'stages/analyze').glob('*.json'))
    assert AnalysisArtifact.model_validate_json((root/'analysis.json').read_bytes()).model=='old-model'
