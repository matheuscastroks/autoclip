import json
from pathlib import Path
from types import SimpleNamespace
from test_gemini import transcript,payload
from engine.contracts import AnalysisConfig,AnalysisArtifact
from engine.adapters.gemini.analyzer import GeminiAnalyzer

def test_editorial_duration_targets_accept_shorter_and_longer_complete_arguments():
    t=transcript();body=payload(t);seen=[]
    def request(**kw):
        seen.append(kw['contents']);return SimpleNamespace(text=json.dumps(body))
    # 30s complete argument is shorter than preferred (180s) and old 60s floor, but >= 20s technical minimum.
    result=GeminiAnalyzer(request=request).analyze(t,AnalysisConfig(model='fixture',max_calls=4,clip_preferred_seconds=180,clip_max_seconds=300))
    assert result.complete and set(result.covered_word_ids)=={w.id for w in t.words}
    assert len(result.candidates)==1
    assert '180' in seen[0] and '300' in seen[0] and 'no máximo 10' in seen[0]
    assert 'não proponha esse corte' not in seen[0]

def test_technical_minimum_still_rejects_sub_20s_microclips_while_preserving_coverage():
    t=transcript();body=payload(t)
    body['candidates'][0]['end_word_id']='w9'  # ~9.9s < 20s technical minimum
    result=GeminiAnalyzer(request=lambda **kw:SimpleNamespace(text=json.dumps(body))).analyze(t,AnalysisConfig(model='fixture',max_calls=2,clip_preferred_seconds=90,clip_max_seconds=120))
    assert result.complete and set(result.covered_word_ids)=={w.id for w in t.words}
    assert result.candidates==[]

def test_complete_argument_longer_than_preferred_and_max_target_is_accepted(monkeypatch):
    from engine.contracts import Word
    import engine.adapters.gemini.analyzer as module
    t=transcript();t.segments=[]
    # Spread 30 words across ~210 seconds (> preferred 90s and > target max 120s, within technical 600s bound)
    for i,w in enumerate(t.words):
        w.end_us=i*7_000_000+6_000_000
        w.start_us=i*7_000_000
    monkeypatch.setattr(module,'build_windows',lambda *a,**kw:[{'id':'all','words':t.words,'text':'fixture'}])
    result=GeminiAnalyzer(request=lambda **kw:SimpleNamespace(text=json.dumps(payload(t)))).analyze(t,AnalysisConfig(model='fixture',max_calls=1,clip_preferred_seconds=90,clip_max_seconds=120))
    assert len(result.candidates)==1

def test_changing_preferred_duration_does_not_reanalyze_completed_video(tmp_path,monkeypatch):
    from engine.contracts import Source,AudioArtifact,PipelineConfig,ASRConfig,ExportConfig
    from engine.pipeline import runner
    t=transcript()
    source=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'source.mp4',duration_us=40_000_000)
    source.local_path.write_bytes(b'video')
    root=tmp_path/'project';root.mkdir()
    audio=AudioArtifact(source_id=source.id,source_sha256=source.sha256,path=root/'audio.wav',sha256='b'*64,duration_us=40_000_000)
    audio.path.write_bytes(b'audio')
    monkeypatch.setattr(runner,'file_hash',lambda p:source.sha256 if Path(p)==source.local_path else 'c'*64)
    monkeypatch.setattr(runner,'tool_fingerprint',lambda p:{})
    monkeypatch.setattr(runner,'probe_source',lambda *a:source)
    monkeypatch.setattr(runner,'extract_audio',lambda *a:audio)
    calls=[]
    class A:
        def analyze(self,tr,cfg,**kw):
            calls.append((cfg.clip_preferred_seconds,cfg.clip_max_seconds))
            return GeminiAnalyzer(request=lambda **k:SimpleNamespace(text=json.dumps(payload(tr)))).analyze(tr,cfg)
    class T:
        def transcribe(self,*a):return t
    cfg1=PipelineConfig(asr=ASRConfig(model_path=tmp_path),analysis=AnalysisConfig(model='fixture',max_calls=2,clip_preferred_seconds=180,clip_max_seconds=300),export=ExportConfig(output_root=root/'previews'),ffmpeg=tmp_path/'ffmpeg',ffprobe=tmp_path/'ffprobe')
    runner.run_project(source,cfg1,root,transcriber=T(),analyzer=A(),stop_after='analyze')
    assert len(calls)==1
    cfg2=cfg1.model_copy(update={'analysis':cfg1.analysis.model_copy(update={'clip_preferred_seconds':90,'clip_max_seconds':120})})
    runner.run_project(source,cfg2,root,transcriber=T(),analyzer=A(),stop_after='analyze')
    assert len(calls)==1

def test_legacy_analysis_keeps_its_serialized_identity():
    t=transcript()
    a=AnalysisArtifact(transcript_id=t.transcript_id,complete=True,covered_word_ids=[],model='fixture',prompt_hash='x',payload_hashes=[])
    assert 'clip_min_seconds' not in a.model_dump()

def test_consolidation_caps_full_video_at_ten_topics(monkeypatch):
    from engine.contracts import Word
    import engine.adapters.gemini.analyzer as module
    t=transcript();t.segments=[];t.words=[];topics=[];candidates=[]
    template=payload(transcript())['candidates'][0]
    for i in range(12):
        start=i*130_000_000
        t.words.extend([Word(id=f'a{i}',text='Premissa',start_us=start,end_us=start+1_000_000),Word(id=f'b{i}',text='Conclusão',start_us=start+119_000_000,end_us=start+120_000_000)])
        topics.append({'id':f't{i}','label':f'Tópico {i}','summary':'Tema completo','evidence_word_ids':[f'a{i}',f'b{i}']})
        candidates.append({**template,'topic_id':f't{i}','start_word_id':f'a{i}','end_word_id':f'b{i}','evidence_word_ids':[f'a{i}',f'b{i}'],'context_before_word_ids':[],'context_after_word_ids':[]})
    monkeypatch.setattr(module,'build_windows',lambda *a,**kw:[{'id':'all','words':t.words,'text':'fixture'}])
    result=GeminiAnalyzer(request=lambda **kw:SimpleNamespace(text=json.dumps({'topics':topics,'candidates':candidates}))).analyze(t,AnalysisConfig(model='fixture',max_calls=1))
    assert len(result.candidates)==10
    assert len(result.covered_word_ids)==24

