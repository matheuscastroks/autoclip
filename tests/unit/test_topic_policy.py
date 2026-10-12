import json
from types import SimpleNamespace
from test_gemini import transcript,payload
from engine.contracts import AnalysisConfig,AnalysisArtifact
from engine.adapters.gemini.analyzer import GeminiAnalyzer

def test_new_policy_rejects_microclips_and_preserves_full_coverage():
    t=transcript();body=payload(t);seen=[]
    def request(**kw):
        seen.append(kw['contents']);return SimpleNamespace(text=json.dumps(body))
    result=GeminiAnalyzer(request=request).analyze(t,AnalysisConfig(model='fixture',max_calls=4,clip_min_seconds=60,clip_preferred_seconds=180,clip_max_seconds=300))
    assert result.complete and set(result.covered_word_ids)=={w.id for w in t.words}
    assert result.candidates==[]
    assert '60–300 segundos' in seen[0] and 'no máximo 10' in seen[0]
    assert result.model_dump()['clip_min_seconds']==60

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
    result=GeminiAnalyzer(request=lambda **kw:SimpleNamespace(text=json.dumps({'topics':topics,'candidates':candidates}))).analyze(t,AnalysisConfig(model='fixture',max_calls=1,clip_min_seconds=60))
    assert len(result.candidates)==10
    assert len(result.covered_word_ids)==24
