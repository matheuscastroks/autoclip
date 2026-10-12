"""Append-only, local analysis feedback. Provider text is never executable."""
import json
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4


class EventWriter:
    def __init__(self,path=None,secret=''):
        self.path=Path(path) if path else None
        self.secret=secret

    def emit(self,kind,message='',**data):
        if self.path is None:return
        def clean(value):
            if isinstance(value,str):return value.replace(self.secret,'[REDACTED]') if self.secret else value
            if isinstance(value,list):return [clean(v) for v in value]
            if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
            return value
        row=clean({'schema_version':'1.0','id':str(uuid4()),'at':datetime.now(timezone.utc).isoformat(),'kind':kind,'message':message,**data})
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('a',encoding='utf-8') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')


def read_events(path,limit=200,offset=None):
    """Ignore incomplete trailing writes; bounded reads for API polling."""
    from collections import deque
    rows=deque(maxlen=limit);index=0
    try:
        with Path(path).open(encoding='utf-8',errors='replace') as stream:
            for line in stream:
                if not line.endswith('\n'):continue
                try:row=json.loads(line)
                except ValueError:continue
                if not isinstance(row,dict):continue
                if offset is None:rows.append(row)
                elif index>=offset and len(rows)<limit:rows.append(row)
                index+=1
                if offset is not None and len(rows)>=limit:break
    except OSError:return []
    return list(rows)
