import subprocess,json
from pathlib import Path
import pytest

def test_pipeline_resume_and_export_review_gate(tmp_path,ffmpeg,ffprobe):
    from engine.contracts import (Word,TranscriptArtifact,Candidate,EditorialFlags,AnalysisArtifact,PipelineConfig,ASRConfig,AnalysisConfig,ExportConfig,PipelineError,EditorialChecks)
    from engine.pipeline.runner import run_project,export_approved
    from engine.media.importer import import_source
    from engine.pipeline.artifacts import atomic_json
    from engine.editorial.review import record_review,review_fingerprint
    from engine.editorial.report import create_report
    source_file=tmp_path/'fixture.mp4'
    subprocess.run([str(ffmpeg),'-v','error','-y','-f','lavfi','-i','color=c=blue:size=320x180:rate=30:duration=21','-f','lavfi','-i','sine=frequency=440:duration=21','-c:v','libx264','-c:a','aac',str(source_file)],check=True)
    root=tmp_path/'project';source=import_source(str(source_file),root)
    counts={'asr':0,'llm':0}
    class Transcriber:
        def transcribe(self,audio,config):
            counts['asr']+=1
            words=[Word(id=f'w{i}',text=('Não' if i==0 else 'palavra.'),start_us=i*1_000_000,end_us=i*1_000_000+900_000) for i in range(21)]
            return TranscriptArtifact(source_id=audio.source_id,source_sha256=audio.source_sha256,words=words)
    class Analyzer:
        def analyze(self,t,config):
            counts['llm']+=1
            c=Candidate(topic_id='topic',start_word_id='w0',end_word_id='w20',evidence_word_ids=['w0','w20'],rationale='Synthetic fixture, not editorial evaluation.',editorial=EditorialFlags(completeness='yes',standalone_context='yes',qualification_preserved='yes'))
            return AnalysisArtifact(transcript_id=t.transcript_id,complete=True,covered_word_ids=[w.id for w in t.words],model='fixture',prompt_hash='fixture',payload_hashes=[],candidates=[c])
    config=PipelineConfig(asr=ASRConfig(model_path=tmp_path/'fake-model'),analysis=AnalysisConfig(model='fixture',max_calls=1),export=ExportConfig(output_root=root/'previews'),ffmpeg=ffmpeg,ffprobe=ffprobe)
    state=run_project(source,config,root,analyzer=Analyzer(),transcriber=Transcriber())
    assert state.status=='needs_review' and len(state.revisions)==1
    assert create_report(root).exists()
    with pytest.raises(PipelineError) as e:export_approved(root)
    assert e.value.code=='REVIEW_REQUIRED'
    resumed=run_project(source,config,root,analyzer=Analyzer(),transcriber=Transcriber())
    assert counts=={'asr':1,'llm':1} and resumed.revisions==state.revisions
    revision=state.revisions[0]['revision_id']
    checks=EditorialChecks(completeness=True,context=True,qualifications=True,words_and_boundaries=True,audiovisual=True)
    atomic_json(root/'revisions'/revision/'review.json',record_review(__import__('uuid').UUID(revision),'approved',checks,'TEST ONLY: simulated human decision on generated fixture.',review_fingerprint(root,__import__('uuid').UUID(revision))))
    packages=export_approved(root)
    assert (Path(packages[0])/'manifest.json').exists()
    assert (Path(packages[0])/'edl.json').exists()
    cap_file=root/'revisions'/revision/'captions.json'
    altered=json.loads(cap_file.read_text(encoding='utf-8'));altered['words'][0]['display_text']='Alterado depois da aprovação'
    atomic_json(cap_file,altered)
    with pytest.raises(PipelineError) as stale:export_approved(root)
    assert stale.value.code=='STALE_REVIEW'
