import subprocess
import pytest

def test_runner_reuses_online_analysis_offline_and_invalidates_vendor(tmp_path,ffmpeg,ffprobe,monkeypatch):
    from engine.contracts import (Word,TranscriptArtifact,AnalysisArtifact,PipelineConfig,ASRConfig,AnalysisConfig,ExportConfig)
    from engine.pipeline.runner import run_project
    from engine.media.importer import import_source
    from engine.pipeline import fingerprints as fp
    p=tmp_path/'short.mp4'
    subprocess.run([str(ffmpeg),'-v','error','-y','-f','lavfi','-i','color=size=160x90:duration=1','-f','lavfi','-i','sine=duration=1','-c:v','libx264','-c:a','aac',str(p)],check=True)
    root=tmp_path/'project';s=import_source(str(p),root);counts={'asr':0,'llm':0}
    class T:
        def transcribe(self,a,c):counts['asr']+=1;return TranscriptArtifact(source_id=a.source_id,source_sha256=a.source_sha256,words=[Word(id='w',text='Teste',start_us=0,end_us=900_000)])
    class A:
        def analyze(self,t,c,**kw):
            assert not c.offline,'Offline must reuse the previous semantic analysis.'
            counts['llm']+=1;return AnalysisArtifact(transcript_id=t.transcript_id,complete=True,covered_word_ids=['w'],model='fixture',prompt_hash='fixture',payload_hashes=[])
    c=PipelineConfig(asr=ASRConfig(model_path=tmp_path/'mock'),analysis=AnalysisConfig(model='fixture',max_calls=1),export=ExportConfig(output_root=root/'out'),ffmpeg=ffmpeg,ffprobe=ffprobe)
    run_project(s,c,root,analyzer=A(),transcriber=T())
    c.analysis.offline=True;c.analysis.max_calls=10
    run_project(s,c,root,analyzer=A(),transcriber=T())
    assert counts=={'asr':1,'llm':1}
    old=fp.file_hash
    monkeypatch.setattr(fp,'file_hash',lambda path:'0'*64 if str(path).endswith('transcribe_backends.py') else old(path))
    c.analysis.offline=False
    run_project(s,c,root,analyzer=A(),transcriber=T())
    assert counts=={'asr':2,'llm':2}
