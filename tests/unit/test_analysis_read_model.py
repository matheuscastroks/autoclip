from uuid import uuid4
import pytest
from fastapi import HTTPException
from test_gemini import transcript,payload
from engine.contracts import AnalysisArtifact,Candidate,Topic
from engine.pipeline.artifacts import atomic_json,object_hash
from engine.api.analysis_view import analysis_view,save_selection

def fixture(root):
    t=transcript();c=Candidate.model_validate(payload(t)['candidates'][0])
    a=AnalysisArtifact(transcript_id=t.transcript_id,complete=True,covered_word_ids=[w.id for w in t.words],model='fixture',prompt_hash='fixture',payload_hashes=[],candidates=[c],topics=[Topic(id=c.topic_id,label='Corrupção',summary='Resumo',evidence_word_ids=[t.words[0].id]),Topic(id='other',label=' CORRUPCAO ',summary='Outra evidência',evidence_word_ids=[t.words[1].id]),Topic(id='negated',label='Não corrupção',summary='Negação',evidence_word_ids=[])])
    atomic_json(root/'transcript.json',t);atomic_json(root/'analysis.json',a)
    return t,a

def test_complete_view_measures_words_and_groups_conservatively(tmp_path):
    t,a=fixture(tmp_path);view=analysis_view(tmp_path)
    assert view['state']=='completed' and view['analysis_hash']==object_hash(a)
    assert len(view['topic_groups'])==2
    assert len(view['topic_groups'][0]['topic_ids'])==2
    assert view['proposals'][0]['duration_us']==t.words[-1].end_us-t.words[0].start_us
    selected=save_selection(tmp_path,view['analysis_hash'],[str(a.candidates[0].id)])
    assert selected['candidate_ids']==[str(a.candidates[0].id)]
    with pytest.raises(HTTPException):save_selection(tmp_path,'a'*64,[str(a.candidates[0].id)])
    with pytest.raises(HTTPException):save_selection(tmp_path,view['analysis_hash'],[str(uuid4())])

def test_active_job_never_shows_previous_complete_analysis(tmp_path):
    t,a=fixture(tmp_path);folder=tmp_path/'job';folder.mkdir()
    job={'id':'new','status':'running','operation':'analyze'}
    assert analysis_view(tmp_path,job,folder)['proposals']==[]
    atomic_json(folder/'analysis-preview.json',{'analysis':a.model_copy(update={'complete':False}),'completed_windows':1,'total_windows':2})
    view=analysis_view(tmp_path,job,folder)
    assert view['state']=='partial' and view['analysis_hash'] is None and view['completed_windows']==1
