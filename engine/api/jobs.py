import json,os,subprocess,sys,threading,uuid,time
from pathlib import Path
import psutil
from engine.pipeline.artifacts import atomic_json
from .store import now
from .projects import read_json
from .settings import Settings

ACTIVE=('running','pending','cancelling')

class JobManager:
    def __init__(self,store,workspace,spawn=subprocess.Popen):
        self.store=store;self.workspace=Path(workspace).resolve();self.spawn=spawn;self.processes={};self.lock=threading.Lock()
        self.root=self.workspace/'.autoclip/jobs';self.root.mkdir(parents=True,exist_ok=True)
        for job in self.store.jobs():self.status(job['id'])

    def owned_alive(self,job):
        process=self.processes.get(job['id'])
        if process:return process.poll() is None
        try:
            p=psutil.Process(job.get('pid',0));cmd=p.cmdline()
            return abs(p.create_time()-job.get('worker_created',0))<.1 and 'engine.api.job_worker' in cmd and str(self.root/job['id']) in cmd
        except (psutil.Error,ValueError):return False

    def status(self,job_id):
        job=self.store.job(job_id);folder=self.root/job_id
        result=read_json(folder/'result.json')
        if result:job.update(result)
        elif job['status'] in ACTIVE and not self.owned_alive(job):
            job['status']='interrupted';job['error']={'code':'INTERRUPTED','message':'Tarefa interrompida. Retome explicitamente pela interface.'}
        job['events']=read_json(folder/'events.json',[]) or []
        request_log=folder/'stdout.log'
        if request_log.exists():
            # Never return raw process output or provider content to the UI.
            try:
                lines=request_log.read_text(encoding='utf-8',errors='replace').splitlines()
                stages=[line[7:] for line in lines if line.startswith('Stage: ')]
                if stages:job['stage']=stages[-1]
            except OSError:pass
        budget=folder/'budget.sqlite'
        if budget.exists():
            import sqlite3
            with sqlite3.connect(budget) as c:job['requests_used']=c.execute('SELECT count(*) FROM attempts').fetchone()[0]
        self.store.save_job(job);return job

    def start(self,project_id,operation,options):
        if operation not in ('import','transcribe','analyze','render','export'):raise ValueError('Operação não suportada.')
        if operation=='analyze' and options.get('authorize_text') is not True:raise ValueError('Confirme o envio de texto e o limite de tentativas.')
        row=self.store.get(project_id)
        if (Path(row['path'])/'manual-check.json').exists():raise ValueError('Projeto manual disponível apenas para consulta nesta fase.')
        with self.lock:
            for prior in self.store.jobs():
                if self.status(prior['id'])['status'] in ACTIVE:raise RuntimeError('Uma tarefa já está em execução. Aguarde ou cancele antes de iniciar outra.')
            settings=Settings(self.workspace).get()
            values={k:v for k,v in settings.items() if k not in ('gemini_key_configured','schema_version','tools_available','asr_available')}
            # Only typed request options are accepted by the API; no arbitrary command.
            values.update({k:options[k] for k in ('max_calls','window_seconds','max_text_chars') if k in options})
            jid=str(uuid.uuid4());folder=self.root/jid;folder.mkdir()
            job={'id':jid,'project_id':project_id,'operation':operation,'status':'running','created_at':now(),'requests_used':0,'request_limit':values['max_calls'],'events':[]}
            request={'job_id':jid,'project_id':project_id,'project_root':row['path'],'workspace':str(self.workspace),'operation':operation,'settings':values,'source_input':options.get('source_input')}
            atomic_json(folder/'request.json',request)
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                if c.execute("SELECT 1 FROM jobs WHERE status IN ('running','pending','cancelling')").fetchone():raise RuntimeError('Uma tarefa já está em execução.')
                c.execute('INSERT INTO jobs VALUES(?,?,?,?)',(jid,project_id,'running',json.dumps(job)))
            try:
                kwargs={'cwd':str(self.workspace),'stdout':(folder/'stdout.log').open('wb'),'stderr':subprocess.STDOUT}
                if os.name=='nt':kwargs['creationflags']=subprocess.CREATE_NO_WINDOW
                try:process=self.spawn([sys.executable,'-X','utf8','-m','engine.api.job_worker',str(folder)],**kwargs)
                finally:kwargs['stdout'].close()
                self.processes[jid]=process;job['pid']=process.pid
                try:job['worker_created']=psutil.Process(process.pid).create_time() if process.pid>0 else 0
                except psutil.Error:job['worker_created']=0
                self.store.save_job(job);return job
            except BaseException:
                job['status']='failed';job['error']={'code':'WORKER_START','message':'Não foi possível iniciar a tarefa local.'};self.store.save_job(job);raise

    def cancel(self,job_id):
        job=self.status(job_id)
        if job['status'] not in ACTIVE:return job
        (self.root/job_id/'cancel').touch();job['status']='cancelling';self.store.save_job(job)
        # Import and hashing may not poll cooperatively. Kill only the verified owned tree after grace.
        def enforce():
            time.sleep(5)
            if self.owned_alive(job):
                try:
                    process=psutil.Process(job['pid'])
                    for child in process.children(recursive=True):child.kill()
                    process.kill()
                except psutil.Error:pass
                atomic_json(self.root/job_id/'result.json',{'status':'cancelled','finished_at':now()})
        threading.Thread(target=enforce,daemon=True).start()
        return job

    def resume(self,job_id):
        job=self.status(job_id)
        if job['status'] not in ('failed','cancelled','interrupted'):raise ValueError('Tarefa não pode ser retomada neste estado.')
        if job['operation']=='analyze':raise ValueError('Análise exige novo orçamento explícito; inicie novamente pelo formulário de análise.')
        request=read_json(self.root/job_id/'request.json',{})
        return self.start(job['project_id'],job['operation'],{'source_input':request.get('source_input')})
