import os,subprocess,time,threading,queue
from engine.contracts import PipelineError

def run_process(args,*,cancelled=lambda:False,grace_s=5,timeout_s=None,on_stdout_line=None,**kwargs):
    kwargs.pop('shell',None)
    kwargs.setdefault('stdin',subprocess.DEVNULL)
    capture=kwargs.pop('capture_output',False)
    if capture: kwargs.update(stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if os.name=='nt': kwargs.setdefault('creationflags',subprocess.CREATE_NO_WINDOW)
    process=subprocess.Popen(args,shell=False,**kwargs)
    started=time.monotonic()
    chunks={'stdout':[],'stderr':[]};lines=queue.Queue();readers=[]
    if on_stdout_line:
        def drain(stream,name):
            for line in stream:
                if name=='stdout':lines.put(line)
                # FFmpeg stdout is a small numeric protocol; keep error output bounded.
                chunks[name].append(line)
                if len(chunks[name])>2000:del chunks[name][:1000]
            stream.close()
        for name in ('stdout','stderr'):
            reader=threading.Thread(target=drain,args=(getattr(process,name),name),daemon=True);reader.start();readers.append(reader)
    try:
        while True:
            if cancelled(): raise PipelineError('CANCELLED','process','Cancelled; no partial output published.')
            if timeout_s is not None and time.monotonic()-started>timeout_s:
                raise PipelineError('PROCESS_TIMEOUT','process','Process timeout; no partial output published.',True)
            if on_stdout_line:
                while not lines.empty():on_stdout_line(lines.get_nowait())
                if process.poll() is not None:
                    for reader in readers:reader.join(timeout=2)
                    while not lines.empty():on_stdout_line(lines.get_nowait())
                    return subprocess.CompletedProcess(args,process.returncode,''.join(chunks['stdout']),''.join(chunks['stderr']))
                time.sleep(.05);continue
            try:
                stdout,stderr=process.communicate(timeout=.2)
                return subprocess.CompletedProcess(args,process.returncode,stdout,stderr)
            except subprocess.TimeoutExpired: pass
    except BaseException:
        if process.poll() is None:
            if os.name=='nt':
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
            else: process.terminate()
            try:
                if on_stdout_line:process.wait(timeout=grace_s)
                else:process.communicate(timeout=grace_s)
            except subprocess.TimeoutExpired:
                process.kill()
                if on_stdout_line:process.wait()
                else:process.communicate()
        for reader in readers:reader.join(timeout=2)
        raise
