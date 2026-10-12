import json
from pathlib import Path
from engine.contracts import *
from engine.pipeline.artifacts import file_hash

def test_transcribe_boundary_never_calls_analyzer(tmp_path,monkeypatch):
    from engine.pipeline import runner
    from engine.pipeline.artifacts import atomic_json
    source=Source(local_path=tmp_path/'source.mp4',sha256='a'*64,duration_us=30_000_000)
    audio=AudioArtifact(source_id=source.id,source_sha256=source.sha256,path=tmp_path/'project'/'audio.wav',sha256='b'*64,duration_us=30_000_000)
    audio.path.parent.mkdir(parents=True,exist_ok=True);audio.path.write_bytes(b'fixture')
    transcript=TranscriptArtifact(source_id=source.id,source_sha256=source.sha256,words=[Word(id='w1',text='Teste',start_us=0,end_us=1_000_000)])
    monkeypatch.setattr(runner,'file_hash',lambda p:source.sha256)
    monkeypatch.setattr(runner,'tool_fingerprint',lambda p:{})
    monkeypatch.setattr(runner,'probe_source',lambda *a:source)
    monkeypatch.setattr(runner,'extract_audio',lambda *a:audio)
    class Transcriber:
        def transcribe(self,*a):return transcript
    class Analyzer:
        def analyze(self,*a,**kw):raise AssertionError('No provider at transcribe boundary')
    config=PipelineConfig(asr=ASRConfig(model_path=tmp_path),analysis=AnalysisConfig(model='fixture',max_calls=1),export=ExportConfig(output_root=tmp_path/'previews'),ffmpeg=tmp_path/'ffmpeg',ffprobe=tmp_path/'ffprobe')
    state=runner.run_project(source,config,tmp_path/'project',transcriber=Transcriber(),analyzer=Analyzer(),stop_after='transcribe')
    assert state.status=='transcribed' and state.transcript_path.is_file()

def test_analyze_boundary_never_renders(tmp_path,monkeypatch):
    from engine.pipeline import runner
    source=Source(local_path=tmp_path/'source.mp4',sha256='a'*64,duration_us=30_000_000)
    audio=AudioArtifact(source_id=source.id,source_sha256=source.sha256,path=tmp_path/'project'/'audio.wav',sha256='b'*64,duration_us=30_000_000);audio.path.parent.mkdir(parents=True,exist_ok=True);audio.path.write_bytes(b'fixture')
    transcript=TranscriptArtifact(source_id=source.id,source_sha256=source.sha256,words=[Word(id='w1',text='Teste',start_us=0,end_us=1_000_000)])
    monkeypatch.setattr(runner,'file_hash',lambda p:source.sha256);monkeypatch.setattr(runner,'tool_fingerprint',lambda p:{})
    monkeypatch.setattr(runner,'probe_source',lambda *a:source);monkeypatch.setattr(runner,'extract_audio',lambda *a:audio)
    class T:
        def transcribe(self,*a):return transcript
    class A:
        def analyze(self,*a,**kw):return AnalysisArtifact(transcript_id=transcript.transcript_id,complete=True,covered_word_ids=['w1'],model='fixture',prompt_hash='fixture',payload_hashes=['fixture'])
    monkeypatch.setattr(runner,'FFmpegRenderer',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('No render at analyze boundary')))
    config=PipelineConfig(asr=ASRConfig(model_path=tmp_path),analysis=AnalysisConfig(model='fixture',max_calls=1),export=ExportConfig(output_root=tmp_path/'previews'),ffmpeg=tmp_path/'ffmpeg',ffprobe=tmp_path/'ffprobe')
    assert runner.run_project(source,config,tmp_path/'project',transcriber=T(),analyzer=A(),stop_after='analyze').status=='analyzed'

