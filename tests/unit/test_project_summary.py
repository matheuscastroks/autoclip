from engine.api.projects import project_summary
from engine.pipeline.artifacts import atomic_json

def test_summary_counts_candidates_not_duplicate_revisions(tmp_path):
    atomic_json(tmp_path/'analysis.json',{'candidates':[{'id':'a'},{'id':'b'}]})
    atomic_json(tmp_path/'analysis-selection.json',{'candidate_ids':['a']})
    for rid in ['00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002']:
        folder=tmp_path/'revisions'/rid
        atomic_json(folder/'candidate.json',{'id':'a'})
        atomic_json(folder/'qa.json',{'technical_pass':True})
        atomic_json(folder/'edl.json',{})
        atomic_json(folder/'captions.json',{})
        (folder/'render.mp4').write_bytes(b'fixture')
    rows=[{'revision_id':rid,'render_path':str(tmp_path/'revisions'/rid/'render.mp4')} for rid in ['00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002']]
    result=project_summary(tmp_path,{'revisions':rows},None)
    assert result['proposed']==2 and result['selected']==1 and result['generated']==1
    atomic_json(tmp_path/'revisions/00000000-0000-0000-0000-000000000002/deleted.json',{})
    assert project_summary(tmp_path,{'revisions':[{'revision_id':'00000000-0000-0000-0000-000000000002'}]},None)['generated']==0
    (tmp_path/'revisions'/rows[0]['revision_id']/'render.mp4').unlink()
    assert project_summary(tmp_path,{'revisions':rows},None)['generated']==0

def test_summary_does_not_reuse_selection_from_another_analysis(tmp_path):
    atomic_json(tmp_path/'analysis.json',{'candidates':[{'id':'a'}]})
    atomic_json(tmp_path/'analysis-selection.json',{'analysis_hash':'old','candidate_ids':['a']})
    assert project_summary(tmp_path,{}, {'status':'running','stage':'transcribe'})=={'proposed':1,'selected':0,'generated':0,'stage':'transcribe'}
