"""One cancellable provider request at a time across local worker processes."""
import os,time
from pathlib import Path
from contextlib import contextmanager
from engine.contracts import PipelineError

@contextmanager
def provider_slot(root:Path,cancelled=lambda:False,on_wait=lambda:None):
    path=Path(root)/'.autoclip/provider.lock';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+b') as handle:
        if path.stat().st_size==0:handle.write(b'0');handle.flush()
        acquired=False;reported=False
        try:
            while not acquired:
                if cancelled():raise PipelineError('CANCELLED','analyze','Cancelled while waiting for provider.')
                handle.seek(0)
                try:
                    if os.name=='nt':
                        import msvcrt
                        msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
                    else:
                        import fcntl
                        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    acquired=True
                except OSError:
                    if not reported:on_wait();reported=True
                    time.sleep(.2)
            yield
        finally:
            if acquired:
                handle.seek(0)
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
                else:
                    import fcntl
                    fcntl.flock(handle,fcntl.LOCK_UN)
