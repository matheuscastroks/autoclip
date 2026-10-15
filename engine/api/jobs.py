import json,os,subprocess,sys,threading,uuid,time
from pathlib import Path
import psutil
from datetime import datetime
from engine.pipeline.artifacts import atomic_json
from .store import now
from .projects import read_json
from .settings import Settings
from engine.pipeline.artifacts import object_hash,file_hash
from .job_logs import IncrementalJobLogs

ACTIVE=('running','pending','cancelling')

def render_recipe(settings):
    from engine.pipeline.fingerprints import stage_dependencies,ROOT,safe_file_hash
    keys=('clip_max_seconds','pause_mode','ffmpeg','ffprobe')
    return object_hash({'settings':{k:settings.get(k) for k in keys},'stages':{stage:stage_dependencies(stage) for stage in ('edit_plan','captions','reframe','render','verify')},'contracts':safe_file_hash(ROOT/'engine/contracts/models.py')})

def legacy_render_compatible(request,job,settings):
    """Adopt old recipes only when their settings and implementation still match."""
    from engine.pipeline.fingerprints import FILES,ROOT
    keys=('clip_max_seconds','pause_mode','ffmpeg','ffprobe')
    if any(request.get('settings',{}).get(k)!=settings.get(k) for k in keys):return False
    files={name for stage in ('edit_plan','captions','reframe','render','verify') for name in FILES[stage]}|{'engine/contracts/models.py'}
    try:return datetime.fromisoformat(job['created_at']).timestamp()>=max((ROOT/name).stat().st_mtime for name in files)
    except (OSError,ValueError,KeyError):return False

class JobManager:
    def __init__(self,store,workspace,spawn=subprocess.Popen):
        self.store=store;self.workspace=Path(workspace).resolve();self.spawn=spawn;self.processes={};self.lock=threading.RLock();self.draining=False;self.max_workers=2;self._stop=threading.Event()
        self.root=self.workspace/'.autoclip/jobs';self.root.mkdir(parents=True,exist_ok=True)
        self.logs=IncrementalJobLogs()
        for job in self.store.jobs():self.status(job['id'])
        self._scheduler=threading.Thread(target=self._monitor,daemon=True);self._scheduler.start()

    def owned_alive(self,job):
        process=self.processes.get(job['id'])
        if process:return process.poll() is None
        try:
            p=psutil.Process(job.get('pid',0));cmd=p.cmdline();cmd_str=' '.join(cmd)
            matches='engine.api.job_worker' in cmd_str or 'job-worker' in cmd
            return abs(p.create_time()-job.get('worker_created',0))<.1 and matches and str(self.root/job['id']) in cmd_str
        except (psutil.Error,ValueError):return False

    def status(self,job_id):
        with self.lock:return self._status(job_id)

    def _status(self,job_id):
        job=self.store.job(job_id)
        if job.get('finished_at') or (job.get('status') in ('completed','cancelled','rejected') and 'events' in job and job.get('error') is not None):
            return job
        folder=self.root/job_id
        original_data=dict(job)
        result=read_json(folder/'result.json')
        if result:job.update(result)
        elif job['status'] in ('running','cancelling') and not self.owned_alive(job):
            job['status']='interrupted';job['error']={'code':'INTERRUPTED','message':'Tarefa interrompida. Retome explicitamente pela interface.'}
        job['events']=read_json(folder/'events.json',[]) or []
        from engine.pipeline.analysis_events import read_events
        job['events']+=read_events(folder/'analysis-events.jsonl',limit=100)
        job['progress']=read_json(folder/'progress.json')
        policy=read_json(folder/'request-policy.json')
        if policy:job.update(policy)
        request_log=folder/'stdout.log'
        stage,lines=self.logs.read(request_log)
        # Never return raw process output or provider content to the UI.
        if (job.get('error') or {}).get('code')=='SOURCE_UNAVAILABLE' and job.get('operation') in ('import','prepare'):
            from engine.media.source_errors import source_error
            job['error']=source_error('\n'.join(lines)).as_dict()
        if stage:job['stage']=stage
        budget=folder/'budget.sqlite'
        if budget.exists():
            import sqlite3
            with sqlite3.connect(budget) as c:job['requests_used']=c.execute('SELECT count(*) FROM attempts').fetchone()[0]
        if job!=original_data:
            self.store.save_job(job)
        return job

    def request_shutdown(self,callback):
        with self.lock:
            if any(self.status(j['id'])['status'] in ACTIVE for j in self.store.jobs()):return False
            self.draining=True
            if callback:callback()
            return True

    def clear_history(self):
        from .job_history import clear_job_history
        with self.lock:
            return clear_job_history(self.store,self.root,self.owned_alive)

    def start(self,project_id,operation,options,*,persist_selection=True):
        if operation not in ('prepare','import','transcribe','analyze','render','preview','render_final','export'):raise ValueError('Operação não suportada.')
        if any(r['id']==project_id for r in self.store.trash()):raise ValueError('Restaure o projeto antes de iniciar uma tarefa.')
        row=self.store.get(project_id)
        if (Path(row['path'])/'manual-check.json').exists():raise ValueError('Projeto manual disponível apenas para consulta nesta fase.')
        with self.lock:
            if self.draining:raise RuntimeError('O motor está encerrando. Reabra o aplicativo.')
            settings=Settings(self.workspace).get()
            if operation in ('render','preview') and options.get('candidate_ids') is not None:
                from .analysis_view import save_selection,validate_selection
                (save_selection if persist_selection else validate_selection)(Path(row['path']),options.get('analysis_hash'),options['candidate_ids'],settings.get('clip_max_seconds',300))
                if not options['candidate_ids']:raise ValueError('Selecione pelo menos um trecho.')
            if operation=='render_final':
                from engine.pipeline.outputs import load_preparation
                ids=options.get('revision_ids')
                if not ids:raise ValueError('Selecione uma revisão preparada.')
                known={r['revision_id'] for r in read_json(Path(row['path'])/'project.json',{}).get('revisions',[])}
                if not set(ids)<=known:raise ValueError('Revisão não encontrada neste projeto.')
                for rid in ids:load_preparation(Path(row['path']),rid)
            values={k:v for k,v in settings.items() if k not in ('gemini_key_configured','schema_version','tools_available','asr_available')}
            # Only typed request options are accepted by the API; no arbitrary command.
            values.update({k:options[k] for k in ('max_calls','window_seconds','max_text_chars') if k in options})
            # New UI jobs plan calls from the actual transcript. Explicit legacy API limits remain supported.
            automatic=operation in ('prepare','analyze') and 'max_calls' not in options
            values['automatic_calls']=automatic
            active_rows=[self.status(j['id']) for j in self.store.jobs() if j['project_id']==project_id]
            ignored_ready=ignored_queued=0;ready_items=[];recipe=None
            if operation in ('render','preview') and options.get('candidate_ids') is not None:
                recipe=render_recipe(values);queued=set();ready={}
                for prior in active_rows:
                    if prior['operation']!=operation:continue
                    old=read_json(self.root/prior['id']/'request.json',{}) or {}
                    if old.get('selection',{}).get('analysis_hash')!=options.get('analysis_hash'):continue
                    if old.get('render_recipe')!=recipe and not (old.get('render_recipe') is None and legacy_render_compatible(old,prior,values)):continue
                    if prior['status'] in ACTIVE:queued.update(old.get('selection',{}).get('candidate_ids',[]))
                    for item in (prior.get('progress') or {}).get('items',[]):
                        if item['state']=='ready':ready[item['candidate_id']]=item
                # Only technically valid, existing revisions may be skipped as ready.
                from .reviews import list_revisions
                valid={r.get('candidate_id'):r for r in list_revisions(Path(row['path'])) if (r.get('preview',{}).get('state')=='available' if operation=='preview' else r['technical_pass'])}
                checked_ready={}
                for cid,item in ready.items():
                    if cid not in valid or cid not in options['candidate_ids']:continue
                    rendered=read_json(Path(row['path'])/'revisions'/item.get('revision_id','missing')/('preview.json' if operation=='preview' else 'render.json'),{}) or {}
                    if operation=='preview':rendered=rendered.get('render',{})
                    path=Path(rendered.get('path','')).resolve()
                    if path.is_relative_to(Path(row['path']).resolve()) and path.is_file() and file_hash(path)==rendered.get('sha256'):checked_ready[cid]=item
                ready=checked_ready
                wanted=options['candidate_ids'];ignored_ready=sum(cid in ready for cid in wanted);ignored_queued=sum(cid in queued and cid not in ready for cid in wanted)
                ready_items=[ready[cid] for cid in wanted if cid in ready]
                options={**options,'candidate_ids':[cid for cid in wanted if cid not in queued and cid not in ready]}
                if not options['candidate_ids'] and ignored_queued:
                    prior=next(j for j in active_rows if j['status'] in ACTIVE and j['operation']==operation and set(read_json(self.root/j['id']/'request.json',{}).get('selection',{}).get('candidate_ids',[]))&set(wanted))
                    return {**prior,'ignored_ready':ignored_ready,'ignored_queued':ignored_queued,'enqueued_items':0}
            else:
                for prior in active_rows:
                    old=read_json(self.root/prior['id']/'request.json',{}) or {}
                    if prior['status'] in ACTIVE and prior['operation']==operation and old.get('selection',{}).get('revision_ids')==options.get('revision_ids') and (operation=='render_final' or old.get('settings')==values and old.get('source_input')==options.get('source_input')):return prior
            jid=str(uuid.uuid4());folder=self.root/jid;folder.mkdir()
            job={'id':jid,'project_id':project_id,'operation':operation,'status':'pending','created_at':now(),'requests_used':0,'request_mode':'automatic' if automatic else 'manual','request_limit':None if automatic else values['max_calls'],'events':[]}
            request={'job_id':jid,'project_id':project_id,'project_root':row['path'],'workspace':str(self.workspace),'operation':operation,'settings':values,'source_input':options.get('source_input')}
            request['selection']={k:options[k] for k in ('analysis_hash','candidate_ids','revision_ids') if options.get(k) is not None}
            if recipe:request['render_recipe']=recipe
            job.update(ignored_ready=ignored_ready,ignored_queued=ignored_queued,enqueued_items=len(options.get('candidate_ids',[])))
            atomic_json(folder/'request.json',request)
            if operation=='render_final':
                final_items=[]
                for rid in options['revision_ids']:
                    revision_dir,prepared,*_=load_preparation(Path(row['path']),rid)
                    candidate=read_json(revision_dir/'candidate.json',{})
                    final_items.append({'candidate_id':str(prepared.candidate_id),'revision_id':rid,'title':candidate.get('title_suggestion','Corte'),'state':'pending','phase':'waiting','processed_us':0,'total_us':None})
                atomic_json(folder/'progress.json',{'stage':'render_final','steps':{'render_final':'pending'},'phase':'waiting','items':final_items})
            if operation in ('render','preview') and options.get('candidate_ids'):
                analysis=read_json(Path(row['path'])/'analysis.json',{}) or {}
                titles={c['id']:c.get('title_suggestion','Trecho') for c in analysis.get('candidates',[])}
                atomic_json(folder/'progress.json',{'stage':'render','steps':{'render':'pending'},'phase':'waiting','items':[{'candidate_id':cid,'title':titles.get(cid,'Trecho'),'state':'pending','phase':'waiting','processed_us':0,'total_us':None} for cid in options['candidate_ids']]})
            if operation in ('render','preview') and options.get('candidate_ids')==[]:
                atomic_json(folder/'progress.json',{'stage':'render','steps':{'render':'completed'},'items':ready_items})
                atomic_json(folder/'result.json',{'status':'completed','finished_at':now()})
                job['status']='completed'
            self.store.save_job(job)
            self.dispatch()
            return self.status(jid)

    def close(self):
        self._stop.set()
        if threading.current_thread() is not self._scheduler:self._scheduler.join(timeout=2)

    def _monitor(self):
        while not self._stop.wait(.5):
            try:self.dispatch()
            except Exception:
                # A transient database/filesystem failure must not kill the scheduler.
                import logging
                logging.getLogger(__name__).exception('Queue dispatch failed')

    def dispatch(self):
        with self.lock:
            if self.draining:return
            rows=[self.status(j['id']) if j['status'] in ACTIVE else j for j in self.store.jobs()]
            executing=[j for j in rows if j['status'] in ('running','cancelling')]
            occupied={j['project_id'] for j in executing}
            provider_busy=any(j['operation']=='analyze' for j in executing)
            pending=sorted((j for j in rows if j['status']=='pending'),key=lambda j:(j['created_at'],j['id']))
            waiting_projects=set()
            for position,job in enumerate(pending,1):
                blocked=job['project_id'] in occupied or job['project_id'] in waiting_projects
                provider=job['operation']=='analyze'
                reason='Aguardando a tarefa anterior deste projeto.' if blocked else 'Aguardando a fila de análise por IA.' if provider and provider_busy else 'Aguardando capacidade do motor local.' if len(executing)>=self.max_workers else ''
                if reason:
                    job.update(queue_position=position,queue_reason=reason);self.store.save_job(job);waiting_projects.add(job['project_id']);continue
                folder=self.root/job['id'];job.update(status='running',queue_position=None,queue_reason=None,started_at=now())
                self.store.save_job(job)
                try:
                    kwargs={'cwd':str(self.workspace),'stdout':(folder/'stdout.log').open('wb'),'stderr':subprocess.STDOUT}
                    if os.name=='nt':kwargs['creationflags']=subprocess.CREATE_NO_WINDOW
                    from engine.system.subprocesses import engine_cmd
                    cmd = engine_cmd('job-worker', str(folder), module='engine.api.job_worker')
                    try:process=self.spawn(cmd,**kwargs)
                    finally:kwargs['stdout'].close()
                    self.processes[job['id']]=process;job['pid']=process.pid
                    try:job['worker_created']=psutil.Process(process.pid).create_time() if process.pid>0 else 0
                    except psutil.Error:job['worker_created']=0
                    self.store.save_job(job);executing.append(job);occupied.add(job['project_id']);provider_busy=provider_busy or provider
                except Exception:
                    job.update(status='failed',error={'code':'WORKER_START','message':'Não foi possível iniciar a tarefa local. As outras tarefas foram preservadas.'})
                    self.store.save_job(job)

    def cancel(self,job_id):
        with self.lock:return self._cancel(job_id)

    def _cancel(self,job_id):
        job=self.status(job_id)
        if job['status'] not in ACTIVE:return job
        if job['status']=='pending':
            progress=read_json(self.root/job_id/'progress.json')
            if progress:
                for item in progress.get('items',[]):item.update(state='cancelled',phase='cancelled')
                atomic_json(self.root/job_id/'progress.json',progress)
            atomic_json(self.root/job_id/'result.json',{'status':'cancelled','finished_at':now()});job['status']='cancelled';self.store.save_job(job);self.dispatch();return job
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

    def resume(self,job_id,source_input=None,*,candidate_id=None):
        job=self.status(job_id)
        if job['status'] not in ('failed','cancelled','interrupted'):raise ValueError('Tarefa não pode ser retomada neste estado.')
        if source_input is not None:
            root=Path(self.store.get(job['project_id'])['path'])
            if job['operation'] not in ('import','prepare') or (root/'source.json').exists():raise ValueError('A fonte de um projeto já importado não pode ser substituída. Crie outro projeto.')
        if job['operation'] in ('prepare','analyze'):return self.start(job['project_id'],job['operation'],{'source_input':source_input or read_json(self.root/job_id/'request.json',{}).get('source_input')})
        request=read_json(self.root/job_id/'request.json',{})
        selection=request.get('selection',{})
        if candidate_id is not None:
            failed={i['candidate_id'] for i in (job.get('progress') or {}).get('items',[]) if i['state']=='failed'}
            if job['operation'] not in ('render','preview','render_final') or candidate_id not in failed or candidate_id not in selection.get('candidate_ids',[]):raise ValueError('Este corte não está disponível para nova tentativa.')
            selection={**selection,'candidate_ids':[candidate_id]}
        if job['operation'] in ('render','preview') and selection.get('candidate_ids'):
            ready={i['candidate_id'] for i in (job.get('progress') or {}).get('items',[]) if i['state']=='ready'}
            selection={**selection,'candidate_ids':[cid for cid in selection['candidate_ids'] if cid not in ready]}
            if not selection['candidate_ids']:raise ValueError('Todas as prévias já estão prontas.')
        return self.start(job['project_id'],job['operation'],{'source_input':source_input or request.get('source_input'),**selection},persist_selection=False)
