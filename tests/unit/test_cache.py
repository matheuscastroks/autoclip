import pytest

def test_modified_source_model_prompt_and_caption_invalidate_only_dependents(tmp_path):
    from engine.pipeline.manifest import StageCache
    from engine.contracts import Word
    calls=[];cache=StageCache(tmp_path)
    def produce(): calls.append(1);return Word(id='w1',text='a',start_us=0,end_us=1)
    cache.run('asr',{'source':'a','model':'m1'},produce,Word)
    cache.run('asr',{'source':'a','model':'m1'},produce,Word)
    assert len(calls)==1
    cache.run('asr',{'source':'a','model':'m2'},produce,Word)
    assert len(calls)==2
    cache.run('captions',{'asr':'one','caption':'v1'},produce,Word)
    cache.run('captions',{'asr':'one','caption':'v2'},produce,Word)
    assert len(calls)==4
    cache.run('asr',{'source':'a','model':'m2'},produce,Word)
    assert len(calls)==4

def test_corrupt_or_partial_artifact_is_not_reused(tmp_path):
    from engine.pipeline.manifest import StageCache
    from engine.contracts import Word
    calls=[];cache=StageCache(tmp_path)
    def make(): calls.append(1);return Word(id='w',text='a',start_us=0,end_us=1)
    cache.run('x',{},make,Word)
    next((tmp_path/'artifacts/x').glob('*.json')).write_text('{}')
    cache.run('x',{},make,Word)
    assert len(calls)==2

def test_two_projects_never_share_outputs(tmp_path):
    from engine.pipeline.manifest import StageCache
    from engine.contracts import Word
    calls=[]
    def make(): calls.append(1);return Word(id='w',text='a',start_us=0,end_us=1)
    for folder in ['a','b']: StageCache(tmp_path/folder).run('x',{},make,Word)
    assert len(calls)==2
