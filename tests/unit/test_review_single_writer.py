from uuid import uuid4
from engine.contracts import Source,ProjectRun,EditorialChecks
from engine.pipeline.artifacts import atomic_json
from engine.api import reviews

def test_decision_does_not_replace_worker_owned_revision_list(tmp_path,monkeypatch):
    rid=str(uuid4());folder=tmp_path/'revisions'/rid;folder.mkdir(parents=True)
    state=ProjectRun(source=Source(local_path=tmp_path/'source.mp4',sha256='a'*64),status='processing',revisions=[{'revision_id':rid},{'revision_id':str(uuid4())}])
    atomic_json(tmp_path/'project.json',state);before=(tmp_path/'project.json').read_bytes()
    monkeypatch.setattr(reviews,'list_revisions',lambda root:[{'revision_id':rid,'technical_pass':True}])
    monkeypatch.setattr(reviews,'review_fingerprint',lambda *args:'a'*64)
    writes=[]
    def write(path,value):writes.append(path.name);atomic_json(path,value)
    monkeypatch.setattr(reviews,'atomic_json',write)
    checks=EditorialChecks(completeness=True,context=True,qualifications=True,words_and_boundaries=True,audiovisual=True)
    reviews.decide(tmp_path,rid,'approved',checks,'fixture','a'*64)
    assert (folder/'review.json').is_file()
    assert (tmp_path/'project.json').read_bytes()==before and 'project.json' not in writes
