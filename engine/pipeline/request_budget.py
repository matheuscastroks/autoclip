"""Durable authorization ledger: reserve an attempt before any provider request."""
import sqlite3,time
from pathlib import Path
from engine.contracts import PipelineError

class RequestBudget:
    def __init__(self,path:Path,limit:int):
        if limit<1:raise ValueError('Positive request limit required')
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as c:
            c.executescript('CREATE TABLE IF NOT EXISTS policy(request_limit INTEGER); CREATE TABLE IF NOT EXISTS attempts(number INTEGER PRIMARY KEY,payload_hash TEXT,created REAL);')
            existing=c.execute('SELECT request_limit FROM policy').fetchone()
            if existing and existing[0]!=limit:raise ValueError('Existing authorization limit cannot be changed; create a new explicitly authorized job.')
            if not existing:c.execute('INSERT INTO policy VALUES(?)',(limit,))
        self.limit=limit

    @property
    def used(self):
        with sqlite3.connect(self.path) as c:return c.execute('SELECT count(*) FROM attempts').fetchone()[0]

    @property
    def remaining(self):return self.limit-self.used

    def reserve(self,payload_hash:str)->int:
        with sqlite3.connect(self.path,timeout=10) as c:
            c.execute('BEGIN IMMEDIATE');number=c.execute('SELECT count(*) FROM attempts').fetchone()[0]+1
            if number>self.limit:raise PipelineError('PROVIDER_BUDGET','analyze','Persistent request budget exhausted; explicit new authorization required.')
            c.execute('INSERT INTO attempts VALUES(?,?,?)',(number,payload_hash,time.time()))
        return number
