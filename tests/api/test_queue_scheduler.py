import json
from types import SimpleNamespace
import pytest
from engine.api.jobs import JobManager
from engine.api.store import ProjectStore
from engine.pipeline.artifacts import atomic_json

@pytest.fixture
def queue(tmp_path):
    store=ProjectStore(tmp_path/'.autoclip/library.sqlite');spawned=[]
    def spawn(*args,**kwargs):spawned.append(args);return SimpleNamespace(pid=0,poll=lambda:None)
    manager=JobManager(store,tmp_path,spawn=spawn);manager.close()
    projects=[store.create(tmp_path/f'p{i}',str(i))['id'] for i in range(4)]
    yield manager,projects,spawned
    manager.close()

def finish(manager,job,status='completed'):
    atomic_json(manager.root/job['id']/'result.json',{'status':status})
    manager.dispatch()

def test_projects_run_in_parallel_and_same_project_is_serial(queue):
    m,p,spawned=queue
    a=m.start(p[0],'transcribe',{});b=m.start(p[1],'analyze',{})
    c=m.start(p[0],'export',{});d=m.start(p[2],'transcribe',{})
    assert a['status']==b['status']=='running' and len(spawned)==2
    assert c['status']==d['status']=='pending'
    assert 'projeto' in m.status(c['id'])['queue_reason']
    finish(m,a)
    assert m.status(c['id'])['status']=='running'
    assert m.status(d['id'])['status']=='pending'
    finish(m,b,'failed')
    assert m.status(d['id'])['status']=='running'

def test_provider_queue_does_not_block_unrelated_local_task(queue):
    m,p,spawned=queue
    a=m.start(p[0],'analyze',{});b=m.start(p[1],'analyze',{});c=m.start(p[2],'transcribe',{})
    assert a['status']==c['status']=='running' and b['status']=='pending'
    assert m.start(p[1],'analyze',{})['id']==b['id']
    finish(m,a)
    assert m.status(b['id'])['status']=='running'

def test_automatic_preparation_can_run_beside_another_projects_analysis(queue):
    m,p,spawned=queue
    a=m.start(p[0],'prepare',{'source_input':'fixture.mp4'})
    b=m.start(p[1],'analyze',{})
    assert a['status']==b['status']=='running' and len(spawned)==2

def test_pending_cancel_and_restart_preserve_remaining_queue(queue):
    m,p,spawned=queue
    a=m.start(p[0],'transcribe',{});b=m.start(p[0],'analyze',{});c=m.start(p[0],'export',{})
    assert m.cancel(b['id'])['status']=='cancelled' and len(spawned)==1
    second=JobManager(m.store,m.workspace,spawn=m.spawn);second.close()
    assert second.status(a['id'])['status']=='interrupted'
    assert second.status(c['id'])['status']=='pending'
    second.dispatch()
    assert second.status(c['id'])['status']=='running'

def test_failed_worker_start_does_not_stop_queue(queue):
    m,p,spawned=queue
    m.spawn=lambda *a,**kw:(_ for _ in ()).throw(OSError('fixture'))
    assert m.start(p[0],'transcribe',{})['status']=='failed'
    m.spawn=lambda *a,**kw:SimpleNamespace(pid=0,poll=lambda:None)
    assert m.start(p[1],'transcribe',{})['status']=='running'

def test_render_only_enqueues_candidates_not_already_queued(queue,monkeypatch):
    from engine.api import analysis_view,reviews
    m,p,spawned=queue
    monkeypatch.setattr(analysis_view,'save_selection',lambda *a:None)
    monkeypatch.setattr(analysis_view,'validate_selection',lambda *a:None)
    monkeypatch.setattr(reviews,'list_revisions',lambda *a:[])
    options={'analysis_hash':'a'*64,'candidate_ids':['first','second']}
    first=m.start(p[0],'render',options)
    repeated=m.start(p[0],'render',options)
    assert repeated['id']==first['id'] and repeated['ignored_queued']==2
    more=m.start(p[0],'render',{**options,'candidate_ids':['second','third']})
    request=json.loads((m.root/more['id']/'request.json').read_text())
    assert more['status']=='pending' and request['selection']['candidate_ids']==['third']
    assert more['ignored_queued']==1 and len(spawned)==1

def test_completed_ready_candidates_are_not_spawned_again(queue,monkeypatch):
    from engine.api import analysis_view,reviews
    m,p,spawned=queue
    monkeypatch.setattr(analysis_view,'save_selection',lambda *a:None)
    monkeypatch.setattr(reviews,'list_revisions',lambda *a:[{'candidate_id':'first','technical_pass':True}])
    options={'analysis_hash':'a'*64,'candidate_ids':['first']}
    first=m.start(p[0],'render',options)
    atomic_json(m.root/first['id']/'progress.json',{'items':[{'candidate_id':'first','revision_id':'r','state':'ready','title':'Ready'}]})
    from engine.pipeline.artifacts import file_hash
    root=m.store.get(p[0])['path'];video=__import__('pathlib').Path(root)/'preview.mp4';video.write_bytes(b'render')
    atomic_json(__import__('pathlib').Path(root)/'revisions/r/render.json',{'path':str(video),'sha256':file_hash(video)})
    finish(m,first)
    repeat=m.start(p[0],'render',options)
    assert repeat['status']=='completed' and repeat['ignored_ready']==1
    assert repeat['enqueued_items']==0 and len(spawned)==1
