import json,sqlite3,uuid
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()

class ProjectStore:
    def __init__(self,database:Path):
        self.database=Path(database);self.database.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:
            c.executescript('''PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,path TEXT UNIQUE,name TEXT,created_at TEXT);
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,project_id TEXT,status TEXT,data TEXT);
                CREATE TABLE IF NOT EXISTS project_trash(project_id TEXT PRIMARY KEY,deleted_at TEXT);
            ''')

    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.database,timeout=10);c.row_factory=sqlite3.Row
        try:
            yield c;c.commit()
        except BaseException:c.rollback();raise
        finally:c.close()

    def register(self,path:Path,name:str|None=None)->dict:
        path=Path(path).resolve()
        if not path.is_dir() or not (path/'source.json').is_file():raise ValueError('Escolha uma pasta de projeto que contenha source.json.')
        with self.connect() as c:
            c.execute('INSERT OR IGNORE INTO projects VALUES(?,?,?,?)',(str(uuid.uuid4()),str(path),name or path.name,now()))
            return dict(c.execute('SELECT * FROM projects WHERE path=?',(str(path),)).fetchone())

    def create(self,path:Path,name:str)->dict:
        path=Path(path).resolve();path.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:
            pid=str(uuid.uuid4());c.execute('INSERT INTO projects VALUES(?,?,?,?)',(pid,str(path),name,now()))
        return self.get(pid)

    def list_projects(self)->list[dict]:
        with self.connect() as c:return [dict(r) for r in c.execute('SELECT * FROM projects WHERE id NOT IN (SELECT project_id FROM project_trash) ORDER BY created_at DESC')]

    def trash(self):
        with self.connect() as c:return [dict(r) for r in c.execute('SELECT p.*,t.deleted_at FROM projects p JOIN project_trash t ON p.id=t.project_id ORDER BY t.deleted_at DESC')]

    def set_deleted(self,project_id,deleted):
        self.get(project_id)
        with self.connect() as c:
            if deleted:c.execute('INSERT OR REPLACE INTO project_trash VALUES(?,?)',(project_id,now()))
            else:c.execute('DELETE FROM project_trash WHERE project_id=?',(project_id,))

    def hard_delete(self,project_id:str)->bool:
        self.get(project_id)
        with self.connect() as c:
            c.execute('DELETE FROM jobs WHERE project_id=?',(project_id,))
            c.execute('DELETE FROM project_trash WHERE project_id=?',(project_id,))
            c.execute('DELETE FROM projects WHERE id=?',(project_id,))
        return True

    def delete_finished_job(self,job_id:str)->bool:
        with self.connect() as c:
            return c.execute("DELETE FROM jobs WHERE id=? AND status IN ('completed','rejected')",(job_id,)).rowcount==1

    def get(self,project_id:str)->dict:
        with self.connect() as c:r=c.execute('SELECT * FROM projects WHERE id=?',(project_id,)).fetchone()
        if r is None:raise KeyError(project_id)
        return dict(r)

    def jobs(self)->list[dict]:
        with self.connect() as c:return [json.loads(r['data']) for r in c.execute("SELECT data FROM jobs ORDER BY json_extract(data,'$.created_at') DESC,id DESC")]

    def job(self,job_id):
        with self.connect() as c:r=c.execute('SELECT data FROM jobs WHERE id=?',(job_id,)).fetchone()
        if r is None:raise KeyError(job_id)
        return json.loads(r['data'])

    def save_job(self,job):
        with self.connect() as c:c.execute('INSERT INTO jobs VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET project_id=excluded.project_id,status=excluded.status,data=excluded.data',(job['id'],job['project_id'],job['status'],json.dumps(job,ensure_ascii=False)))
