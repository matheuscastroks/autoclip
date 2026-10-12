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
        from engine.pipeline.analysis_events import read_events
        job['events']+=read_events(folder/'analysis-events.jsonl',limit=100)
        job['progress']=read_json(folder/'progress.json')
        policy=read_json(folder/'request-policy.json')
        if policy:job.update(policy)
        request_log=folder/'stdout.log'
        if request_log.exists():
            # Never return raw process output or provider content to the UI.
            try:
                lines=request_log.read_text(encoding='utf-8',errors='replace').splitlines()
                if job.get('error',{}).get('code')=='SOURCE_UNAVAILABLE' and job.get('operation') in ('import','prepare'):
                    from engine.media.source_errors import source_error
                    job['error']=source_error('\n'.join(lines[-100:])).as_dict()
                stages=[line[7:] for line in lines if line.startswith('Stage: ')]
                if stages:job['stage']=stages[-1]
            except OSError:pass
        budget=folder/'budget.sqlite'
        if budget.exists():
            import sqlite3
            with sqlite3.connect(budget) as c:job['requests_used']=c.execute('SELECT count(*) FROM attempts').fetchone()[0]
        self.store.save_job(job);return job

    def start(self,project_id,operation,options,*,persist_selection=True):
        if operation not in ('prepare','import','transcribe','analyze','render','export'):raise ValueError('Operação não suportada.')
        if any(r['id']==project_id for r in self.store.trash()):raise ValueError('Restaure o projeto antes de iniciar uma tarefa.')
        row=self.store.get(project_id)
        if (Path(row['path'])/'manual-check.json').exists():raise ValueError('Projeto manual disponível apenas para consulta nesta fase.')
        with self.lock:
            for prior in self.store.jobs():
                if self.status(prior['id'])['status'] in ACTIVE:raise RuntimeError('Uma tarefa já está em execução. Aguarde ou cancele antes de iniciar outra.')
            settings=Settings(self.workspace).get()
            if operation=='render' and options.get('candidate_ids') is not None:
                from .analysis_view import save_selection,validate_selection
                (save_selection if persist_selection else validate_selection)(Path(row['path']),options.get('analysis_hash'),options['candidate_ids'],settings.get('clip_max_seconds',180))
                if not options['candidate_ids']:raise ValueError('Selecione pelo menos um trecho.')
            values={k:v for k,v in settings.items() if k not in ('gemini_key_configured','schema_version','tools_available','asr_available')}
            # Only typed request options are accepted by the API; no arbitrary command.
            values.update({k:options[k] for k in ('max_calls','window_seconds','max_text_chars') if k in options})
            # New UI jobs plan calls from the actual transcript. Explicit legacy API limits remain supported.
            automatic=operation in ('prepare','analyze') and 'max_calls' not in options
            values['automatic_calls']=automatic
            jid=str(uuid.uuid4());folder=self.root/jid;folder.mkdir()
            job={'id':jid,'project_id':project_id,'operation':operation,'status':'running','created_at':now(),'requests_used':0,'request_mode':'automatic' if automatic else 'manual','request_limit':None if automatic else values['max_calls'],'events':[]}
            request={'job_id':jid,'project_id':project_id,'project_root':row['path'],'workspace':str(self.workspace),'operation':operation,'settings':values,'source_input':options.get('source_input')}
            request['selection']={k:options[k] for k in ('analysis_hash','candidate_ids') if options.get(k) is not None}
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

    def resume(self,job_id,source_input=None):
        job=self.status(job_id)
        if job['status'] not in ('failed','cancelled','interrupted'):raise ValueError('Tarefa não pode ser retomada neste estado.')
        if source_input is not None:
            root=Path(self.store.get(job['project_id'])['path'])
            if job['operation'] not in ('import','prepare') or (root/'source.json').exists():raise ValueError('A fonte de um projeto já importado não pode ser substituída. Crie outro projeto.')
        if job['operation'] in ('prepare','analyze'):return self.start(job['project_id'],job['operation'],{'source_input':source_input or read_json(self.root/job_id/'request.json',{}).get('source_input')})
        request=read_json(self.root/job_id/'request.json',{})
        selection=request.get('selection',{})
        if job['operation']=='render' and selection.get('candidate_ids'):
            ready={i['candidate_id'] for i in (job.get('progress') or {}).get('items',[]) if i['state']=='ready'}
            selection={**selection,'candidate_ids':[cid for cid in selection['candidate_ids'] if cid not in ready]}
            if not selection['candidate_ids']:raise ValueError('Todas as prévias já estão prontas.')
        return self.start(job['project_id'],job['operation'],{'source_input':source_input or request.get('source_input'),**selection},persist_selection=False)
