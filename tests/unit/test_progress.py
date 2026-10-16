import sys
from engine.pipeline.progress import RenderProgress
from engine.pipeline.cancellation import run_process

def test_numeric_progress_monotonic_clamped():
    seen=[];p=RenderProgress(100,lambda done,total:seen.append((done,total)))
    for line in ['out_time_us=20','out_time_us=N/A','out_time_us=10','out_time_us=999']:p.line(line)
    assert seen==[(20,100),(20,100),(100,100)]

def test_stream_drains_stderr_and_delivers_stdout_before_completion():
    seen=[]
    result=run_process([sys.executable,'-c',"import sys;print('out_time_us=20',flush=True);sys.stderr.write('x'*100000);print('progress=end',flush=True)"],capture_output=True,text=True,encoding='utf-8',on_stdout_line=seen.append,timeout_s=10)
    assert result.returncode==0 and any('out_time_us=20' in line for line in seen)

def test_run_process_isolates_stdin_with_devnull(monkeypatch):
    import subprocess
    captured={}
    real_popen=subprocess.Popen
    def spy_popen(args,**kwargs):
        captured['stdin']=kwargs.get('stdin')
        return real_popen(args,**kwargs)
    monkeypatch.setattr(subprocess,'Popen',spy_popen)
    result=run_process([sys.executable,'-c',"import sys;assert sys.stdin.read()==''"],capture_output=True,text=True,timeout_s=5)
    assert result.returncode==0
    assert captured['stdin']==subprocess.DEVNULL

