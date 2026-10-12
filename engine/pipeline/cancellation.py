import os,subprocess
from engine.contracts import PipelineError

def run_process(args,*,cancelled=lambda:False,grace_s=5,**kwargs):
    kwargs.pop('shell',None)
    capture=kwargs.pop('capture_output',False)
    if capture: kwargs.update(stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if os.name=='nt': kwargs.setdefault('creationflags',subprocess.CREATE_NO_WINDOW)
    process=subprocess.Popen(args,shell=False,**kwargs)
    try:
        while True:
            if cancelled(): raise PipelineError('CANCELLED','process','Cancelled; no partial output published.')
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
