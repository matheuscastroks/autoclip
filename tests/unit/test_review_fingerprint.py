import json
from pathlib import Path
from uuid import uuid4
import pytest

def test_changed_caption_or_render_invalidates_human_approval(tmp_path):
    from engine.editorial.review import review_fingerprint
    revision=uuid4();folder=tmp_path/'revisions'/str(revision);folder.mkdir(parents=True)
    for name in ['edl','candidate','captions','render','qa']:
        (folder/(name+'.json')).write_text(json.dumps({'revision':str(revision),'value':name}))
    before=review_fingerprint(tmp_path,revision)
    (folder/'captions.json').write_text('{"changed":true}')
    assert review_fingerprint(tmp_path,revision)!=before

def test_approval_requires_content_hash():
    from engine.editorial.review import record_review
    from engine.contracts import EditorialChecks
    checks=EditorialChecks(completeness=True,context=True,qualifications=True,words_and_boundaries=True,audiovisual=True)
    with pytest.raises(ValueError): record_review(uuid4(),'approved',checks,'missing content binding')
