from test_projects import client,source_folder

def test_duration_settings_validate_and_persist(client):
    config=client.get('/api/v1/config').json()
    config={k:v for k,v in config.items() if k not in ('schema_version','asr_available','tools_available','gemini_key_configured')}
    config.update(clip_preferred_seconds=60,clip_max_seconds=180,pause_mode='conservative',show_thought_summaries=True)
    assert client.put('/api/v1/config',json=config).status_code==200
    assert client.get('/api/v1/config').json()['clip_max_seconds']==180
    config['clip_preferred_seconds']=181
    assert client.put('/api/v1/config',json=config).status_code==422

def test_job_feedback_is_live_and_history_is_paged_and_project_scoped(client,tmp_path):
    from engine.pipeline.analysis_events import EventWriter
    pid=client.post('/api/v1/projects/import',json={'path':str(source_folder(tmp_path))}).json()['id']
    store=client.app.state.store
    store.save_job({'id':'fixture','project_id':pid,'operation':'analyze','status':'failed','created_at':'','request_limit':3})
    path=client.app.state.jobs.root/'fixture'/'analysis-events.jsonl'
    writer=EventWriter(path);writer.emit('thought_summary','Verificando o encerramento.',window_id='w1',attempt=1)
    writer.emit('analysis_completed','Concluído.')
    assert client.get('/api/v1/jobs').json()[0]['events'][0]['kind']=='thought_summary'
    response=client.get(f'/api/v1/projects/{pid}/analysis-events',params={'job_id':'fixture','offset':0,'limit':1})
    assert response.status_code==200 and response.json()['has_more']
    assert response.json()['events'][0]['message']=='Verificando o encerramento.'
    assert client.get('/api/v1/projects/other/analysis-events',params={'job_id':'fixture'}).status_code==404
