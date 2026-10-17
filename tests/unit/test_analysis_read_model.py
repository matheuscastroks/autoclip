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

def test_save_selection_rejects_overlapping_candidates(tmp_path):
    t=transcript();c=Candidate.model_validate(payload(t)['candidates'][0])
    c1=c.model_copy(update={'id':uuid4()});c2=c.model_copy(update={'id':uuid4()})
    a=AnalysisArtifact(transcript_id=t.transcript_id,complete=True,covered_word_ids=[w.id for w in t.words],model='fixture',prompt_hash='fixture',payload_hashes=[],candidates=[c1,c2],topics=[Topic(id=c.topic_id,label='Tema',summary='Resumo',evidence_word_ids=[t.words[0].id])])
    atomic_json(tmp_path/'transcript.json',t);atomic_json(tmp_path/'analysis.json',a)
    view=analysis_view(tmp_path)
    with pytest.raises(HTTPException) as exc:
        save_selection(tmp_path,view['analysis_hash'],[str(c1.id),str(c2.id)])
    assert exc.value.status_code==422
    assert 'sobrepõem' in str(exc.value.detail)

def test_active_job_never_shows_previous_complete_analysis(tmp_path):
    t,a=fixture(tmp_path);folder=tmp_path/'job';folder.mkdir()
    job={'id':'new','status':'running','operation':'analyze'}
    assert analysis_view(tmp_path,job,folder)['proposals']==[]
    atomic_json(folder/'analysis-preview.json',{'analysis':a.model_copy(update={'complete':False}),'completed_windows':1,'total_windows':2})
    view=analysis_view(tmp_path,job,folder)
    assert view['state']=='partial' and view['analysis_hash'] is None and view['completed_windows']==1

def test_resume_keeps_durable_partial_visible_before_new_response(tmp_path):
    t,a=fixture(tmp_path)
    atomic_json(tmp_path/'work'/'analysis-preview.json',{'analysis':a.model_copy(update={'complete':False}),'completed_windows':2,'total_windows':5})
    view=analysis_view(tmp_path,{'id':'resumed','status':'running','operation':'analyze'},tmp_path/'new-job')
    assert view['completed_windows']==2 and view['total_windows']==5
    assert view['proposals'] and view['analysis_hash'] is None

def test_analysis_view_and_selection_accept_clips_shorter_and_longer_than_preferred_target(tmp_path):
    from engine.contracts import Word
    t=transcript();t.segments=[]
    # Proposal 1: w0..w9 (~30s, shorter than 60s and preferred 90s)
    # Proposal 2: w10..w29 (~200s, longer than preferred 90s and max_seconds=120s)
    for i in range(10):
        t.words[i]=Word(id=f'w{i}',text='curto',start_us=i*3_000_000,end_us=i*3_000_000+2_900_000)
    for i in range(10,30):
        offset=40_000_000+(i-10)*10_000_000
        t.words[i]=Word(id=f'w{i}',text='longo',start_us=offset,end_us=offset+9_900_000)
    base=Candidate.model_validate(payload(t)['candidates'][0])
    c_short=base.model_copy(update={'id':uuid4(),'start_word_id':'w0','end_word_id':'w9','evidence_word_ids':['w0','w9']})
    c_long=base.model_copy(update={'id':uuid4(),'start_word_id':'w10','end_word_id':'w29','evidence_word_ids':['w10','w29']})
    a=AnalysisArtifact(transcript_id=t.transcript_id,complete=True,covered_word_ids=[w.id for w in t.words],clip_min_seconds=60,model='fixture',prompt_hash='fixture',payload_hashes=[],candidates=[c_short,c_long],topics=[Topic(id=base.topic_id,label='Tema',summary='Resumo',evidence_word_ids=['w0','w29'])])
    atomic_json(tmp_path/'transcript.json',t);atomic_json(tmp_path/'analysis.json',a)
    view=analysis_view(tmp_path,max_seconds=120)
    assert all(p['eligible'] for p in view['proposals'])
    saved=save_selection(tmp_path,view['analysis_hash'],[str(c_short.id),str(c_long.id)],max_seconds=120)
    assert saved['candidate_ids']==[str(c_short.id),str(c_long.id)]


def test_edited_transcript_invalidates_previous_analysis(tmp_path):
    from engine.editorial.transcript_editor import apply_transcript_updates
    from engine.contracts.api import SegmentUpdate
    t, a = fixture(tmp_path)
    view = analysis_view(tmp_path)
    assert view['state'] == 'completed'

    # Edit text in the first segment
    edited = apply_transcript_updates(t, [SegmentUpdate(id=t.segments[0].id, text='Texto alterado pelo editor')])
    atomic_json(tmp_path / 'transcript.json', edited)

    # Analysis view must now detect that the analysis is stale
    stale_view = analysis_view(tmp_path)
    assert stale_view['state'] == 'stale'
    assert 'A análise salva não corresponde à transcrição atual' in stale_view['diagnostic']


