"""Minimal worker liveness, intentionally imported before media/provider modules."""
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path


def start_startup_monitor(folder):
    folder = Path(folder)
    if not (folder / 'request.json').is_file():
        return
    stamp = datetime.now(timezone.utc).isoformat()
    state = {'pid': os.getpid(), 'started_at': stamp, 'heartbeat_at': stamp, 'phase': 'initializing'}
    lock = threading.Lock()

    def write():
        temp = folder / f'.startup-{os.getpid()}.partial'
        try:
            temp.write_text(json.dumps(state), encoding='utf-8')
            os.replace(temp, folder / 'startup.json')
        except OSError:
            # Observability must not turn a successfully running task into a failure.
            temp.unlink(missing_ok=True)

    def running():
        with lock:
            state['phase'] = 'running'
            state['heartbeat_at'] = datetime.now(timezone.utc).isoformat()
            write()

    def heartbeat():
        while True:
            threading.Event().wait(5)
            with lock:
                state['heartbeat_at'] = datetime.now(timezone.utc).isoformat()
                write()

    write()
    threading.Thread(target=heartbeat, name='job-heartbeat', daemon=True).start()
    return running
