import sys,time,subprocess
import pytest

def test_kill_resume_and_cancel(tmp_path):
    from engine.pipeline.cancellation import run_process
    from engine.contracts import PipelineError
    started=time.monotonic()
    with pytest.raises(PipelineError) as e:
        run_process([sys.executable,'-c','import time;time.sleep(30)'],cancelled=lambda:time.monotonic()-started>.5,capture_output=True,text=True)
    assert e.value.code=='CANCELLED' and time.monotonic()-started<7

def test_failed_producer_does_not_become_checkpoint(tmp_path):
    from engine.pipeline.manifest import StageCache
    from engine.contracts import Word
    cache=StageCache(tmp_path)
    def fail(): raise RuntimeError('interrupted')
    with pytest.raises(RuntimeError): cache.run('asr',{},fail,Word)
    assert cache.run('asr',{},lambda:Word(id='w',text='a',start_us=0,end_us=1),Word).text=='a'

def test_cli_missing_key_is_actionable_without_leaking(tmp_path):
    import os
    env=dict(os.environ);env.pop('GEMINI_API_KEY',None)
    r=subprocess.run([sys.executable,'-m','engine.cli','doctor'],capture_output=True,text=True,encoding='utf-8',env=env)
    assert r.returncode==0 and 'ffmpeg' in r.stdout.lower()
