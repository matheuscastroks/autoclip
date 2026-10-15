import secrets, sys
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request,Query
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,ConfigDict,Field,SecretStr,model_validator
from typing import Literal
from engine.contracts import PipelineError,EditorialChecks
from engine.contracts.api import Project as ProjectResponse,Job as JobResponse,Revision as RevisionResponse,AnalysisView,CreatedProject
from .store import ProjectStore
from .projects import discover,project_detail
from .settings import Settings
from .media import make_ticket,valid_ticket,asset_path

class Input(BaseModel):model_config=ConfigDict(extra='forbid')
class ImportProject(Input):path:str;name:str|None=None
class Credential(Input):key:SecretStr
class AppConfig(Input):
    asr_model_path:str
    gemini_model:str=Field(min_length=1,max_length=120)
    max_calls:int=Field(ge=1,le=100)
    window_seconds:int=Field(ge=60,le=1800)
    max_text_chars:int=Field(ge=1000,le=300000)
    ffmpeg:str
    ffprobe:str
    clip_policy_version:int=Field(default=2,ge=2,le=2)
    clip_preferred_seconds:int=Field(default=180,ge=60,le=300)
    clip_max_seconds:int=Field(default=300,ge=60,le=300)
    pause_mode:Literal['preserve','conservative']='conservative'
    show_thought_summaries:bool=True
    ai_provider:Literal['gemini','openrouter']='gemini'
    openrouter_model:str=Field(default='openrouter/free',min_length=1,max_length=120)
    openrouter_key_configured:bool|None=Field(default=None,exclude=True)
    gemini_key_configured:bool|None=Field(default=None,exclude=True)
    asr_available:bool|None=Field(default=None,exclude=True)
    tools_available:bool|None=Field(default=None,exclude=True)
    schema_version:str|None=Field(default=None,exclude=True)

    @model_validator(mode='after')
    def durations(self):
        if self.clip_preferred_seconds>self.clip_max_seconds:raise ValueError('Preferred exceeds maximum')
        return self

class JobOptions(Input):
    revision_ids:list[str]|None=Field(default=None,min_length=1,max_length=1000)
    analysis_hash:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    candidate_ids:list[str]|None=Field(default=None,max_length=1000)
    authorize_text:bool=False
    max_calls:int|None=Field(default=None,ge=1,le=100)
    window_seconds:int|None=Field(default=None,ge=60,le=1800)
    max_text_chars:int|None=Field(default=None,ge=1000,le=300000)
    source_input:str|None=None
class StartJob(Input):
    operation:str
    options:JobOptions=Field(default_factory=JobOptions)
class RetryJob(Input):
    source_input:str|None=Field(default=None,min_length=1,max_length=4000)
    candidate_id:str|None=Field(default=None,min_length=1,max_length=100)
class AnalysisSelection(Input):
    schema_version:str|None='1.0'
    analysis_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
    candidate_ids:list[str]=Field(max_length=1000)
class NewProject(Input):
    name:str=Field(min_length=1,max_length=100)
    source_input:str=Field(min_length=1)
    automatic:bool=False
    authorize_text:bool=False
    max_calls:int|None=Field(default=None,ge=1,le=100)
class Picker(Input):
    kind:str
class BulkCuts(Input):
    revision_ids:list[str]=Field(min_length=1,max_length=1000)
class Decision(Input):
    decision:Literal['approved','rejected']
    checks:EditorialChecks
    notes:str=Field(default='',max_length=10000)
    content_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
class SystemProvisionInput(Input):
    model_id:str='Systran/faster-whisper-small'
    install_ffmpeg:bool=True

def get_frontend_dist(workspace: Path) -> Path | None:
    p = workspace / 'desktop/dist'
    if (p / 'index.html').is_file():
        return p
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            p = Path(sys._MEIPASS) / 'desktop/dist'
            if (p / 'index.html').is_file():
                return p
            p = Path(sys._MEIPASS) / 'dist'
            if (p / 'index.html').is_file():
                return p
        exe_dir = Path(sys.executable).parent
        for candidate in [exe_dir / 'desktop/dist', exe_dir / 'dist', exe_dir / 'resources/dist']:
            if (candidate / 'index.html').is_file():
                return candidate
    return None

def create_app(workspace:Path,token:str)->FastAPI:
    workspace=Path(workspace).resolve();store=ProjectStore(workspace/'.autoclip/library.sqlite');settings=Settings(workspace)
    discover(store,workspace)
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def lifespan(app):
        try:yield
        finally:app.state.jobs.close()
    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
    app.state.store=store;app.state.workspace=workspace;app.state.token=token;app.state.settings=settings
    from .gemini_connection import GeminiConnection
    gemini_connection=GeminiConnection();app.state.gemini_connection=gemini_connection
    from .jobs import JobManager
    jobs=JobManager(store,workspace);app.state.jobs=jobs
    from engine.system.profiler import profile_hardware
    from engine.system.provisioner import DependencyProvisioner
    provisioner=DependencyProvisioner();app.state.provisioner=provisioner
    def describe(row):
        rows=[j for j in store.jobs() if j['project_id']==row['id']]
        executing=[j for j in rows if j['status'] in ('running','cancelling')]
        pending=[j for j in rows if j['status']=='pending']
        latest=max(executing or pending or rows,key=lambda j:(j.get('created_at',''),j['id'])) if rows else None
        return project_detail(row,jobs.status(latest['id']) if latest else None)

    @app.middleware('http')
    async def access(request:Request,call_next):
        host=request.url.hostname
        if host not in ('127.0.0.1','localhost'):return JSONResponse({'detail':'Acesso somente local.'},403)
        origin=request.headers.get('origin')
        if origin and origin!=str(request.base_url).rstrip('/'):return JSONResponse({'detail':'Origem não autorizada.'},403)
        if request.url.path.startswith('/api/'):
            authorized=secrets.compare_digest(request.headers.get('authorization',''),'Bearer '+token)
            parts=request.url.path.strip('/').split('/')
            if len(parts)==7 and parts[:3]==['api','v1','projects'] and parts[4]=='media':
                # ticket routes still require bearer authentication.
                pass
            if len(parts)==6 and parts[:3]==['api','v1','projects'] and parts[4]=='media':
                authorized=authorized or valid_ticket(token,parts[3],parts[5],request.query_params.get('expires'),request.query_params.get('ticket',''))
            if not authorized:return JSONResponse({'detail':'Sessão inválida. Abra novamente pelo atalho.'},401)
        response=await call_next(request)
        response.headers['Referrer-Policy']='no-referrer';response.headers['X-Content-Type-Options']='nosniff'
        if request.url.path.startswith('/api/'):response.headers['Cache-Control']='no-store'
        return response

    @app.exception_handler(PipelineError)
    async def pipeline_error(request,exc):return JSONResponse({'detail':{'code':exc.code,'message':'A operação não foi concluída. Verifique o modelo, a fonte e as configurações.'}},400)

    @app.exception_handler(KeyError)
    async def missing(request,exc):return JSONResponse({'detail':'Projeto ou tarefa não encontrado.'},404)

    @app.exception_handler(ValueError)
    async def invalid(request,exc):return JSONResponse({'detail':'Dados inválidos ou pasta incompatível. Verifique sua seleção.'},400)

    # Pydantic error inputs may contain an API key. Do not return them.
    from fastapi.exceptions import RequestValidationError
    @app.exception_handler(RequestValidationError)
    async def validation(request,exc):return JSONResponse({'detail':'Preencha os campos com valores válidos.'},422)

    @app.get('/api/v1/health')
    def health():return {'schema_version':'1.0','status':'ok','application':'autoclip-editor'}
    @app.post('/api/v1/shutdown')
    def shutdown():
        if not jobs.request_shutdown(getattr(app.state,'shutdown',None)):raise HTTPException(409,'Cancele ou aguarde a tarefa antes de encerrar o serviço.')
        return {'stopped':True}
    @app.get('/api/v1/config')
    def config():return settings.get()
    @app.put('/api/v1/config')
    def update_config(values:AppConfig):return settings.save(values.model_dump())
    @app.put('/api/v1/config/credential')
    def update_credential(value:Credential):
        return gemini_connection.validate(value.key.get_secret_value())
    @app.put('/api/v1/config/openrouter-credential')
    def update_openrouter_credential(value:Credential):
        from engine.adapters.openrouter.credentials import set_openrouter_key
        set_openrouter_key(value.key.get_secret_value().strip())
        return {'configured':True}
    @app.get('/api/v1/config/gemini')
    def gemini_status():return gemini_connection.status()
    @app.post('/api/v1/config/gemini/test')
    def gemini_test():return gemini_connection.validate()
    @app.get('/api/v1/system/profile')
    def system_profile():return {'schema_version':'1.0','profile':profile_hardware().to_dict()}
    from engine.contracts.api import ProvisionStatus
    @app.post('/api/v1/system/provision',response_model=ProvisionStatus)
    def system_provision(value:SystemProvisionInput):
        try:return provisioner.start(value.model_id,value.install_ffmpeg)
        except RuntimeError as exc:raise HTTPException(409,str(exc))
    @app.get('/api/v1/system/provision/status',response_model=ProvisionStatus)
    def system_provision_status():
        st=provisioner.status()
        if st.get('status')=='ready' and st.get('model_path'):
            cfg=settings.get();updates={}
            if st.get('model_path') and cfg.get('asr_model_path')!=st['model_path']:updates['asr_model_path']=st['model_path']
            if st.get('ffmpeg_path') and cfg.get('ffmpeg')!=st['ffmpeg_path']:updates['ffmpeg']=st['ffmpeg_path']
            if st.get('ffprobe_path') and cfg.get('ffprobe')!=st['ffprobe_path']:updates['ffprobe']=st['ffprobe_path']
            if updates:settings.save({**cfg,**updates})
        return st
    @app.post('/api/v1/system/provision/cancel')
    def system_provision_cancel():
        provisioner.cancel();return {'cancelled':True}
    @app.get('/api/v1/projects',response_model=list[ProjectResponse])
    def projects():return [describe(row) for row in store.list_projects()]
    @app.post('/api/v1/projects',response_model=CreatedProject)
    def new_project(value:NewProject):
        import uuid
        cfg=settings.get()
        if value.automatic:
            provider=cfg.get('ai_provider','gemini')
            if provider=='gemini' and not cfg.get('gemini_key_configured'):
                raise HTTPException(400,'Configure a chave Gemini antes de iniciar a sequência automática.')
            elif provider=='openrouter' and not cfg.get('openrouter_key_configured'):
                raise HTTPException(400,'Configure a chave OpenRouter antes de iniciar a sequência automática.')
        row=store.create(workspace/'.autoclip/projects'/str(uuid.uuid4()),value.name.strip() or 'Novo projeto')
        try:job=jobs.start(row['id'],'prepare' if value.automatic else 'import',{'source_input':value.source_input,'authorize_text':value.authorize_text,**({'max_calls':value.max_calls} if value.max_calls else {})})
        except RuntimeError as exc:raise HTTPException(409,str(exc))
        return {'project':project_detail(row),'job':job}
    def editable(pid,*,cut_delete=False):
        store.get(pid)
        if any(jobs.status(j['id'])['status'] in ('running','pending','cancelling') for j in store.jobs() if j['project_id']==pid and (not cut_delete or j['operation'] not in ('transcribe','analyze'))):raise HTTPException(409,'Aguarde ou cancele a geração, exportação ou importação antes de excluir este corte.' if cut_delete else 'Aguarde ou cancele a tarefa antes de excluir ou restaurar.')
    @app.delete('/api/v1/projects/{pid}')
    def delete_project(pid:str,permanent:bool=False):
        import shutil
        with jobs.lock:
            editable(pid)
            row=store.get(pid)
            if permanent:
                path=Path(row['path'])
                if path.is_dir() and (workspace/'.autoclip/projects') in path.parents:
                    try:
                        shutil.rmtree(path)
                    except OSError as exc:
                        raise HTTPException(500,'Não foi possível remover os arquivos do projeto. O projeto permanece na biblioteca.') from exc
                    if path.exists():
                        raise HTTPException(500,'Os arquivos do projeto não foram removidos. O projeto permanece na biblioteca.')
                store.hard_delete(pid)
            else:
                store.set_deleted(pid,True)
        return {'deleted':True}
    @app.post('/api/v1/jobs/clear-history')
    def clear_job_history():
        return jobs.clear_history()

    @app.get('/api/v1/trash')
    def trash():return store.trash()
    @app.post('/api/v1/trash/{pid}/restore',response_model=ProjectResponse)
    def restore_project(pid:str):
        with jobs.lock:
            editable(pid);store.set_deleted(pid,False)
        return project_detail(store.get(pid))
    @app.post('/api/v1/projects/import',response_model=ProjectResponse)
    def register(value:ImportProject):return project_detail(store.register(Path(value.path),value.name))
    @app.get('/api/v1/projects/{pid}',response_model=ProjectResponse)
    def detail(pid:str):return describe(store.get(pid))
    @app.get('/api/v1/projects/{pid}/transcript')
    def transcript(pid:str):
        from engine.contracts import TranscriptArtifact
        path=Path(store.get(pid)['path'])/'transcript.json'
        if not path.is_file():raise HTTPException(404,'Transcrição ainda não disponível.')
        return TranscriptArtifact.model_validate_json(path.read_bytes()).model_dump(mode='json')
    @app.get('/api/v1/projects/{pid}/analysis',response_model=AnalysisView)
    def analysis(pid:str):
        from .analysis_view import analysis_view
        root=Path(store.get(pid)['path']);rows=[j for j in store.jobs() if j['project_id']==pid and j['operation'] in ('analyze','prepare')]
        latest=None
        # Store ordering is chronological; completed artifacts are independent of event retention.
        if rows:latest=jobs.status(max(rows,key=lambda j:(j.get('created_at',''),j['id']))['id'])
        # Migrate the most recent validated partial snapshot from earlier job folders.
        if not (root/'work'/'analysis-preview.json').exists():
            from .projects import read_json
            from engine.pipeline.artifacts import atomic_json
            for row in sorted(rows,key=lambda j:(j.get('created_at',''),j['id']),reverse=True):
                snapshot=read_json(jobs.root/row['id']/'analysis-preview.json')
                if snapshot:
                    atomic_json(root/'work'/'analysis-preview.json',snapshot);break
        return analysis_view(root,latest,jobs.root/latest['id'] if latest else None,settings.get().get('clip_max_seconds',300))
    @app.get('/api/v1/projects/{pid}/analysis-selection')
    def selection(pid:str):
        from .projects import read_json
        return read_json(Path(store.get(pid)['path'])/'analysis-selection.json',{'schema_version':'1.0','analysis_hash':None,'candidate_ids':[]})
    @app.put('/api/v1/projects/{pid}/analysis-selection')
    def update_selection(pid:str,value:AnalysisSelection):
        from .analysis_view import save_selection
        with jobs.lock:
            editable(pid)
            return save_selection(Path(store.get(pid)['path']),value.analysis_hash,value.candidate_ids,settings.get().get('clip_max_seconds',300))
    @app.get('/api/v1/projects/{pid}/analysis-events')
    def analysis_events(pid:str,job_id:str,offset:int=Query(default=0,ge=0,le=1_000_000),limit:int=Query(default=100,ge=1,le=200)):
        store.get(pid);job=store.job(job_id)
        if job['project_id']!=pid:raise HTTPException(404,'Histórico não encontrado neste projeto.')
        from engine.pipeline.analysis_events import read_events
        from engine.pipeline.artifacts import confined
        rows=read_events(confined(jobs.root,job_id+'/analysis-events.jsonl'),limit+1,offset)
        return {'schema_version':'1.0','events':rows[:limit],'next_offset':offset+min(limit,len(rows)),'has_more':len(rows)>limit}
    @app.get('/api/v1/projects/{pid}/media/{asset}/ticket')
    def ticket(pid:str,asset:str):
        root=Path(store.get(pid)['path'])
        if asset!='thumbnail':asset_path(root,asset)
        return {'url':make_ticket(token,pid,asset)}
    @app.get('/api/v1/projects/{pid}/media/{asset}')
    def media(pid:str,asset:str,download:bool=False):
        root=Path(store.get(pid)['path'])
        if asset=='thumbnail':
            from .thumbnails import thumbnail
            return FileResponse(thumbnail(root,settings.get()['ffmpeg']),media_type='image/jpeg')
        if download:
            from engine.contracts import RenderArtifact,ExportValidation
            from engine.pipeline.artifacts import file_hash
            folder=reviews.revision_folder(root,asset)
            try:
                qa=ExportValidation.model_validate_json((folder/'qa.json').read_bytes())
                rendered=RenderArtifact.model_validate_json((folder/'render.json').read_bytes())
                path=asset_path(root,asset)
                if not qa.technical_pass or rendered.revision_id.__str__()!=asset or path!=rendered.path.resolve() or file_hash(path)!=rendered.sha256:raise ValueError('invalid render')
            except (OSError,ValueError):raise HTTPException(409,'O corte não passou pela validação técnica. Gere a prévia novamente.')
            return FileResponse(path,media_type='video/mp4',filename='corte-'+asset+'.mp4')
        return FileResponse(asset_path(root,asset),media_type='video/mp4')

    @app.get('/api/v1/jobs',response_model=list[JobResponse])
    def list_jobs():return [jobs.status(j['id']) for j in store.jobs()]
    @app.get('/api/v1/jobs/{jid}',response_model=JobResponse)
    def job_status(jid:str):return jobs.status(jid)
    @app.post('/api/v1/projects/{pid}/jobs',response_model=JobResponse)
    def start_job(pid:str,value:StartJob):
        try:return jobs.start(pid,value.operation,value.options.model_dump(exclude_none=True))
        except RuntimeError as exc:raise HTTPException(409,str(exc))
    @app.post('/api/v1/jobs/{jid}/cancel',response_model=JobResponse)
    def cancel_job(jid:str):return jobs.cancel(jid)
    @app.post('/api/v1/jobs/{jid}/resume',response_model=JobResponse)
    def resume_job(jid:str,value:RetryJob|None=None):
        try:return jobs.resume(jid,value.source_input if value else None,candidate_id=value.candidate_id if value else None)
        except RuntimeError as exc:raise HTTPException(409,str(exc))
    @app.post('/api/v1/picker')
    def picker(value:Picker):
        from .native import pick
        return {'path':pick(value.kind)}
    @app.post('/api/v1/projects/{pid}/open-folder')
    def open_folder(pid:str):
        from .native import open_directory
        open_directory(Path(store.get(pid)['path']));return {'opened':True}
    from . import reviews
    @app.post('/api/v1/projects/{pid}/revisions/bulk-delete')
    def bulk_delete(pid:str,value:BulkCuts):
        with jobs.lock:
            editable(pid,cut_delete=True)
            root=Path(store.get(pid)['path'])
            ids=set(value.revision_ids)
            available={r['revision_id'] for r in reviews.list_revisions(root)}
            if not ids<=available:raise HTTPException(409,'A lista de cortes mudou. Atualize antes de excluir.')
            for rid in ids:reviews.set_deleted(root,rid,True)
            return {'deleted':len(ids)}
    @app.post('/api/v1/projects/{pid}/revisions/bulk-export')
    def bulk_export(pid:str,value:BulkCuts):
        with jobs.lock:
            editable(pid)
            root=Path(store.get(pid)['path']);ids=set(value.revision_ids)
            approved={r['revision_id'] for r in reviews.list_revisions(root) if r['technical_pass'] and r['review_status']=='approved'}
            if not ids<=approved:raise HTTPException(409,'Todos os cortes selecionados precisam de aprovação editorial válida.')
            from engine.pipeline.runner import export_approved
            return {'paths':export_approved(root,ids)}
    @app.get('/api/v1/projects/{pid}/revisions',response_model=list[RevisionResponse])
    def revisions(pid:str):return reviews.list_revisions(Path(store.get(pid)['path']))
    @app.get('/api/v1/projects/{pid}/deleted-revisions')
    def deleted_revisions(pid:str):return reviews.list_deleted(Path(store.get(pid)['path']))
    @app.delete('/api/v1/projects/{pid}/revisions/{rid}')
    def delete_revision(pid:str,rid:str):
        with jobs.lock:
            editable(pid,cut_delete=True);return reviews.set_deleted(Path(store.get(pid)['path']),rid,True)
    @app.post('/api/v1/projects/{pid}/revisions/{rid}/restore')
    def restore_revision(pid:str,rid:str):
        with jobs.lock:
            editable(pid);return reviews.set_deleted(Path(store.get(pid)['path']),rid,False)
    @app.post('/api/v1/projects/{pid}/revisions/{rid}/decision')
    def decide(pid:str,rid:str,value:Decision):
        return reviews.decide(Path(store.get(pid)['path']),rid,value.decision,value.checks,value.notes,value.content_hash)
    @app.post('/api/v1/projects/{pid}/exports')
    def export(pid:str):return reviews.export(Path(store.get(pid)['path']))

    dist=get_frontend_dist(workspace)
    if dist and dist.is_dir():app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
    return app
