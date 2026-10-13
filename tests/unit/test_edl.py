from uuid import uuid4
import pytest
from test_gemini import transcript,payload

def test_continuous_edl_preserves_every_word_and_source_bounds(tmp_path):
    from engine.contracts import Source,Candidate
    from engine.editorial.edl import plan_continuous_edit,source_at,output_at
    t=transcript();s=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'source.mp4',duration_us=40_000_000)
    c=Candidate.model_validate(payload(t)['candidates'][0]);edl=plan_continuous_edit(c,t,s)
    assert edl.removed==[] and len(edl.spans)==1 and edl.spans[0].output_start_us==0
    assert edl.protected_word_ids==[w.id for w in t.words]
    assert source_at(edl,0)==0 and output_at(edl,1_000_000)==1_000_000
    assert source_at(edl,edl.duration_us) is None

def test_source_output_roundtrip_at_join():
    from engine.contracts import EDLArtifact,Span
    from engine.editorial.edl import source_at,output_at
    e=EDLArtifact(source_id=uuid4(),transcript_id=uuid4(),spans=[Span(source_start_us=10,source_end_us=20,output_start_us=0,output_end_us=10),Span(source_start_us=30,source_end_us=40,output_start_us=10,output_end_us=20)],duration_us=20,protected_word_ids=[])
    assert source_at(e,10)==30
    assert output_at(e,25) is None
    assert output_at(e,source_at(e,19))==19

def test_configured_five_minute_policy_accepts_clip_over_three_minutes(tmp_path):
    from engine.contracts import Source,Candidate,SelectionConfig
    from engine.editorial.edl import plan_continuous_edit
    t=transcript()
    for i,w in enumerate(t.words):w.end_us=i*8_000_000+1_000_000;w.start_us=i*8_000_000
    s=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'s.mp4',duration_us=300_000_000)
    result=plan_continuous_edit(Candidate.model_validate(payload(t)['candidates'][0]),t,s,selection=SelectionConfig(min_us=60_000_000,max_us=300_000_000))
    assert 180_000_000<result.duration_us<=300_000_000

def test_padding_never_trims_a_word_to_fit_60_seconds(tmp_path):
    from engine.contracts import Source,Candidate,PipelineError
    from engine.editorial.edl import plan_continuous_edit
    t=transcript();t.words[-1].end_us=60_100_000
    s=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'s.mp4',duration_us=90_000_000)
    with pytest.raises(PipelineError): plan_continuous_edit(Candidate.model_validate(payload(t)['candidates'][0]),t,s)
