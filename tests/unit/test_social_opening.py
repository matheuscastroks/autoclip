from test_gemini import transcript,payload
from engine.contracts import Source,Candidate,CaptionConfig,CaptionRevision
from engine.editorial.edl import plan_continuous_edit
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder

def test_opening_is_separate_from_speech_and_expires_at_seven_seconds(tmp_path):
    t=transcript();original=t.model_dump()
    s=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'s.mp4',duration_us=40_000_000)
    edl=plan_continuous_edit(Candidate.model_validate(payload(t)['candidates'][0]),t,s)
    caps=OpenShortsCaptionBuilder(tmp_path).build(t,edl,CaptionRevision(),CaptionConfig(opening_text='Toda corrupção é igual?'))
    text=caps.ass_path.read_text(encoding='utf-8')
    rows=[line for line in text.splitlines() if line.startswith('Dialogue: 1,')]
    assert len(rows)==3
    assert '0:00:06.70,0:00:07.00,Opening' in rows[-1]
    assert r'\move(' in rows[0] and r'\move(' in rows[-1]
    assert ',3,4,0,8,' in text
    assert 'TODA CORRUPÇÃO É IGUAL?' in rows[0]
    assert caps.opening_text=='Toda corrupção é igual?'
    assert 'corrupção' not in caps.srt_path.read_text().lower()
    assert t.model_dump()==original

def test_opening_cannot_inject_ass_commands(tmp_path):
    from engine.render.opening import add_opening
    p=tmp_path/'subtitle.ass';p.write_text('[V4+ Styles]\n[Events]\n')
    add_opening(p,r'{\pos(0,0)} Olá\N mundo',7_000_000,'Montserrat ExtraBold')
    text=p.read_text()
    assert r'{\pos(0,0)}' not in text
    assert r'\POS(0,0)' not in text

def test_legacy_candidate_serialization_does_not_change_analysis_fingerprint():
    c=Candidate.model_validate(payload(transcript())['candidates'][0])
    assert 'opening_suggestion' not in c.model_dump(mode='json')
    assert c.model_copy(update={'opening_suggestion':'Uma pergunta relevante?'}).model_dump()['opening_suggestion']=='Uma pergunta relevante?'

def test_blank_opening_falls_back_to_the_complete_title():
    from engine.render.opening import opening_for,normalize_opening
    c=Candidate.model_validate(payload(transcript())['candidates'][0])
    assert opening_for(c.model_copy(update={'opening_suggestion':'  '}))=='Título'
    assert normalize_opening(r'{\pos(0,0)}')==''

def test_gemini_structured_opening_reaches_the_candidate_without_altering_word_boundaries():
    import json
    from types import SimpleNamespace
    from engine.adapters.gemini.analyzer import GeminiAnalyzer
    from engine.contracts import AnalysisConfig
    t=transcript();data=payload(t);data['candidates'][0]['opening_suggestion']='Uma ressalva muda o sentido?'
    result=GeminiAnalyzer(request=lambda **kw:SimpleNamespace(text=json.dumps(data),model_version='fixture',usage_metadata=None),sleep=lambda _:None).analyze(t,AnalysisConfig(model='fixture',max_calls=3))
    assert result.candidates[0].opening_suggestion=='Uma ressalva muda o sentido?'
    assert (result.candidates[0].start_word_id,result.candidates[0].end_word_id)==('w0','w29')
