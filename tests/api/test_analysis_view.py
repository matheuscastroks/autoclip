from uuid import uuid4
import pytest
from test_projects import client,source_folder
from engine.contracts import TranscriptArtifact,Word,AnalysisArtifact,Candidate,EditorialFlags,Topic
from engine.pipeline.artifacts import atomic_json

@pytest.mark.parametrize('operation', ['render', 'preview'])
def test_analysis_selection_and_worker_snapshot(client,tmp_path,operation):
    root=source_folder(tmp_path)
    t=TranscriptArtifact.model_validate_json((root/'transcript.json').read_bytes())
    t.words=[Word(id='start',text='Primeira',start_us=0,end_us=1_000_000),Word(id='end',text='Conclusão',start_us=29_000_000,end_us=30_000_000)]
    c=Candidate(topic_id='t',start_word_id='start',end_word_id='end',evidence_word_ids=['start','end'],rationale='Argumento completo',editorial=EditorialFlags(completeness='yes',standalone_context='yes',qualification_preserved='yes'))
    other=c.model_copy(update={'id':uuid4()})
    a=AnalysisArtifact(transcript_id=t.transcript_id,topics=[Topic(id='t',label='Tema',summary='Resumo',evidence_word_ids=['start'])],candidates=[c,other],complete=True,covered_word_ids=['start','end'],model='fixture',prompt_hash='fixture',payload_hashes=[])
    atomic_json(root/'transcript.json',t);atomic_json(root/'analysis.json',a)
    pid=client.post('/api/v1/projects/import',json={'path':str(root)}).json()['id']
    view=client.get(f'/api/v1/projects/{pid}/analysis').json()
    assert len(view['proposals'])==2 and view['proposals'][0]['duration_us']==30_000_000
    choice={'analysis_hash':view['analysis_hash'],'candidate_ids':[str(c.id),str(other.id)]}
    assert client.put(f'/api/v1/projects/{pid}/analysis-selection',json=choice).status_code==422
    t.words.extend([Word(id='next',text='Outro',start_us=30_000_000,end_us=31_000_000),Word(id='finish',text='Fim',start_us=59_000_000,end_us=60_000_000)])
    other.start_word_id='next';other.end_word_id='finish';other.evidence_word_ids=['next','finish']
    a.covered_word_ids=[w.id for w in t.words]
    atomic_json(root/'transcript.json',t);atomic_json(root/'analysis.json',a)
    view=client.get(f'/api/v1/projects/{pid}/analysis').json();choice['analysis_hash']=view['analysis_hash']
    assert client.put(f'/api/v1/projects/{pid}/analysis-selection',json=choice).status_code==200
    assert client.get(f'/api/v1/projects/{pid}/analysis-selection').json()['candidate_ids']==choice['candidate_ids']
    invalid={**choice,'analysis_hash':'0'*64}
    assert client.put(f'/api/v1/projects/{pid}/analysis-selection',json=invalid).status_code==409
    class Process:
        pid=0
        def poll(self):return None
    client.app.state.jobs.spawn=lambda *a,**kw:Process()
    response=client.post(f'/api/v1/projects/{pid}/jobs',json={'operation':operation,'options':choice})
    assert response.status_code==200
    assert response.json()['operation']==operation
    import json
    request=json.loads((client.app.state.jobs.root/response.json()['id']/'request.json').read_bytes())
    assert request['selection']==choice
    folder=client.app.state.jobs.root/response.json()['id']
    atomic_json(folder/'result.json',{'status':'failed'})
    atomic_json(folder/'progress.json',{'items':[{'candidate_id':str(c.id),'state':'ready'},{'candidate_id':str(other.id),'state':'failed'}]})
    assert client.post('/api/v1/jobs/'+response.json()['id']+'/resume',json={'candidate_id':str(c.id)}).status_code==400
    resumed=client.post('/api/v1/jobs/'+response.json()['id']+'/resume',json={'candidate_id':str(other.id)})
    assert resumed.status_code==200
    retry=json.loads((client.app.state.jobs.root/resumed.json()['id']/'request.json').read_bytes())
    assert retry['selection']['candidate_ids']==[str(other.id)]
    assert client.get(f'/api/v1/projects/{pid}/analysis-selection').json()['candidate_ids']==choice['candidate_ids']
