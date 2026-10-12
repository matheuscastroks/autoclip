from uuid import uuid4
import pytest
from test_gemini import transcript,payload
from engine.contracts import AnalysisArtifact,Candidate,SelectionConfig,PipelineError
from engine.editorial.select import validate_explicit_candidates

def test_explicit_selection_preserves_more_than_three_and_overlapping_variants():
    t=transcript();c=Candidate.model_validate(payload(t)['candidates'][0])
    choices=[c.model_copy(update={'id':uuid4()}) for _ in range(5)]
    a=AnalysisArtifact(transcript_id=t.transcript_id,complete=True,covered_word_ids=[w.id for w in t.words],model='fixture',prompt_hash='fixture',payload_hashes=[],candidates=choices)
    result=validate_explicit_candidates(a,t,SelectionConfig(),[str(c.id) for c in choices])
    assert len(result.candidates)==5
    choices[0].editorial.completeness='uncertain'
    with pytest.raises(PipelineError):validate_explicit_candidates(a,t,SelectionConfig(),[str(choices[0].id)])
    with pytest.raises(PipelineError):validate_explicit_candidates(a,t,SelectionConfig(),[str(uuid4())])
