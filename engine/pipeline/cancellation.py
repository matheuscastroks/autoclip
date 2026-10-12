import os,subprocess,time
from engine.contracts import PipelineError

def run_process(args,*,cancelled=lambda:False,grace_s=5,timeout_s=None,**kwargs):
    kwargs.pop('shell',None)
    capture=kwargs.pop('capture_output',False)
    if capture: kwargs.update(stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if os.name=='nt': kwargs.setdefault('creationflags',subprocess.CREATE_NO_WINDOW)
    process=subprocess.Popen(args,shell=False,**kwargs)
    started=time.monotonic()
    try:
        while True:
            if cancelled(): raise PipelineError('CANCELLED','process','Cancelled; no partial output published.')
            if timeout_s is not None and time.monotonic()-started>timeout_s:
                raise PipelineError('PROCESS_TIMEOUT','process','Process timeout; no partial output published.',True)
            try:
                stdout,stderr=process.communicate(timeout=.2)
                return subprocess.CompletedProcess(args,process.returncode,stdout,stderr)
            except subprocess.TimeoutExpired: pass
    except BaseException:
        if process.poll() is None:
            if os.name=='nt':
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
            else: process.terminate()
            try: process.communicate(timeout=grace_s)
            except subprocess.TimeoutExpired: process.kill();process.communicate()
        raise
