import pytest
from test_gemini import transcript,payload

def test_candidate_bounds_and_overlap():
    from engine.editorial.select import select_candidates
    from engine.contracts import AnalysisArtifact,SelectionConfig,Candidate
    t=transcript(); c=Candidate.model_validate(payload(t)['candidates'][0])
    a=AnalysisArtifact(transcript_id=t.transcript_id,complete=True,covered_word_ids=[w.id for w in t.words],model='fixture',prompt_hash='fixture',payload_hashes=[],candidates=[c,c.model_copy(update={'id':__import__('uuid').uuid4()})])
    result=select_candidates(a,t,SelectionConfig())
    assert len(result.candidates)==1 and len(result.rejected)==1
    a.candidates[0].end_word_id='missing'
    assert select_candidates(a,t,SelectionConfig()).rejected

def test_no_or_uncertain_editorial_flags_are_not_automatically_selected():
    from engine.editorial.select import select_candidates
    from engine.contracts import AnalysisArtifact,SelectionConfig,Candidate
    t=transcript();c=Candidate.model_validate(payload(t)['candidates'][0]);c.editorial.qualification_preserved='uncertain'
    a=AnalysisArtifact(transcript_id=t.transcript_id,complete=True,covered_word_ids=[w.id for w in t.words],model='fixture',prompt_hash='fixture',payload_hashes=[],candidates=[c])
    assert select_candidates(a,t,SelectionConfig()).candidates==[]
