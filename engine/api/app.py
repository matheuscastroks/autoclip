import secrets
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request,Query
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,ConfigDict,Field,SecretStr,model_validator
from typing import Literal
from engine.contracts import PipelineError,EditorialChecks
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
    clip_preferred_seconds:int=Field(default=60,ge=20,le=180)
    clip_max_seconds:int=Field(default=180,ge=20,le=180)
    pause_mode:Literal['preserve','conservative']='conservative'
    show_thought_summaries:bool=True

    @model_validator(mode='after')
    def durations(self):
        if self.clip_preferred_seconds>self.clip_max_seconds:raise ValueError('Preferred exceeds maximum')
        return self

class JobOptions(Input):
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
class AnalysisSelection(Input):
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
class Decision(Input):
    decision:str
    checks:EditorialChecks
    notes:str=Field(default='',max_length=10000)
    content_hash:str=Field(pattern=r'^[a-f0-9]{64}$')

def create_app(workspace:Path,token:str)->FastAPI:
    workspace=Path(workspace).resolve();store=ProjectStore(workspace/'.autoclip/library.sqlite');settings=Settings(workspace)
    discover(store,workspace)
    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
    app.state.store=store;app.state.workspace=workspace;app.state.token=token;app.state.settings=settings
    from .gemini_connection import GeminiConnection
    gemini_connection=GeminiConnection();app.state.gemini_connection=gemini_connection
    from .jobs import JobManager
    jobs=JobManager(store,workspace);app.state.jobs=jobs
    def describe(row):
        rows=[j for j in store.jobs() if j['project_id']==row['id']]
        latest=max(rows,key=lambda j:(j.get('created_at',''),j['id'])) if rows else None
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
        if any(jobs.status(j['id'])['status'] in ('running','pending','cancelling') for j in store.jobs()):raise HTTPException(409,'Cancele ou aguarde a tarefa antes de encerrar o serviço.')
        callback=getattr(app.state,'shutdown',None)
        if callback:callback()
        return {'stopped':True}
    @app.get('/api/v1/config')
    def config():return settings.get()
    @app.put('/api/v1/config')
    def update_config(values:AppConfig):return settings.save(values.model_dump())
    @app.put('/api/v1/config/credential')
    def update_credential(value:Credential):
        return gemini_connection.validate(value.key.get_secret_value())
    @app.get('/api/v1/config/gemini')
    def gemini_status():return gemini_connection.status()
    @app.post('/api/v1/config/gemini/test')
    def gemini_test():return gemini_connection.validate()
    @app.get('/api/v1/projects')
    def projects():return [describe(row) for row in store.list_projects()]
    @app.post('/api/v1/projects')
    def new_project(value:NewProject):
        import uuid
        if value.automatic and not settings.get()['gemini_key_configured']:raise HTTPException(400,'Configure a chave Gemini antes de iniciar a sequência automática.')
        row=store.create(workspace/'.autoclip/projects'/str(uuid.uuid4()),value.name.strip() or 'Novo projeto')
        try:job=jobs.start(row['id'],'prepare' if value.automatic else 'import',{'source_input':value.source_input,'authorize_text':value.authorize_text,**({'max_calls':value.max_calls} if value.max_calls else {})})
        except RuntimeError as exc:raise HTTPException(409,str(exc))
        return {'project':project_detail(row),'job':job}
    def editable(pid):
        store.get(pid)
        if any(jobs.status(j['id'])['status'] in ('running','pending','cancelling') for j in store.jobs() if j['project_id']==pid):raise HTTPException(409,'Aguarde ou cancele a tarefa antes de excluir ou restaurar.')
    @app.delete('/api/v1/projects/{pid}')
    def delete_project(pid:str):
        with jobs.lock:
            editable(pid);store.set_deleted(pid,True)
        return {'deleted':True}
    @app.get('/api/v1/trash')
    def trash():return store.trash()
    @app.post('/api/v1/trash/{pid}/restore')
    def restore_project(pid:str):
        with jobs.lock:
            editable(pid);store.set_deleted(pid,False)
        return project_detail(store.get(pid))
    @app.post('/api/v1/projects/import')
    def register(value:ImportProject):return project_detail(store.register(Path(value.path),value.name))
    @app.get('/api/v1/projects/{pid}')
    def detail(pid:str):return describe(store.get(pid))
    @app.get('/api/v1/projects/{pid}/transcript')
    def transcript(pid:str):
        from engine.contracts import TranscriptArtifact
        path=Path(store.get(pid)['path'])/'transcript.json'
        if not path.is_file():raise HTTPException(404,'Transcrição ainda não disponível.')
        return TranscriptArtifact.model_validate_json(path.read_bytes()).model_dump(mode='json')
    @app.get('/api/v1/projects/{pid}/analysis')
    def analysis(pid:str):
        from .analysis_view import analysis_view
        root=Path(store.get(pid)['path']);rows=[j for j in store.jobs() if j['project_id']==pid and j['operation'] in ('analyze','prepare')]
        latest=None
        # Store ordering is chronological; completed artifacts are independent of event retention.
        if rows:latest=jobs.status(max(rows,key=lambda j:(j.get('created_at',''),j['id']))['id'])
        return analysis_view(root,latest,jobs.root/latest['id'] if latest else None,settings.get().get('clip_max_seconds',180))
    @app.get('/api/v1/projects/{pid}/analysis-selection')
    def selection(pid:str):
        from .projects import read_json
        return read_json(Path(store.get(pid)['path'])/'analysis-selection.json',{'schema_version':'1.0','analysis_hash':None,'candidate_ids':[]})
    @app.put('/api/v1/projects/{pid}/analysis-selection')
    def update_selection(pid:str,value:AnalysisSelection):
        from .analysis_view import save_selection
        with jobs.lock:
            editable(pid)
            return save_selection(Path(store.get(pid)['path']),value.analysis_hash,value.candidate_ids,settings.get().get('clip_max_seconds',180))
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
    def media(pid:str,asset:str):
        root=Path(store.get(pid)['path'])
        if asset=='thumbnail':
            from .thumbnails import thumbnail
            return FileResponse(thumbnail(root,settings.get()['ffmpeg']),media_type='image/jpeg')
        return FileResponse(asset_path(root,asset),media_type='video/mp4')

    @app.get('/api/v1/jobs')
    def list_jobs():return [jobs.status(j['id']) for j in store.jobs()]
    @app.get('/api/v1/jobs/{jid}')
    def job_status(jid:str):return jobs.status(jid)
    @app.post('/api/v1/projects/{pid}/jobs')
    def start_job(pid:str,value:StartJob):
        try:return jobs.start(pid,value.operation,value.options.model_dump(exclude_none=True))
        except RuntimeError as exc:raise HTTPException(409,str(exc))
    @app.post('/api/v1/jobs/{jid}/cancel')
    def cancel_job(jid:str):return jobs.cancel(jid)
    @app.post('/api/v1/jobs/{jid}/resume')
    def resume_job(jid:str,value:RetryJob|None=None):
        try:return jobs.resume(jid,value.source_input if value else None)
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
    @app.get('/api/v1/projects/{pid}/revisions')
    def revisions(pid:str):return reviews.list_revisions(Path(store.get(pid)['path']))
    @app.get('/api/v1/projects/{pid}/deleted-revisions')
    def deleted_revisions(pid:str):return reviews.list_deleted(Path(store.get(pid)['path']))
    @app.delete('/api/v1/projects/{pid}/revisions/{rid}')
    def delete_revision(pid:str,rid:str):
        with jobs.lock:
            editable(pid);return reviews.set_deleted(Path(store.get(pid)['path']),rid,True)
    @app.post('/api/v1/projects/{pid}/revisions/{rid}/restore')
    def restore_revision(pid:str,rid:str):
        with jobs.lock:
            editable(pid);return reviews.set_deleted(Path(store.get(pid)['path']),rid,False)
    @app.post('/api/v1/projects/{pid}/revisions/{rid}/decision')
    def decide(pid:str,rid:str,value:Decision):
        return reviews.decide(Path(store.get(pid)['path']),rid,value.decision,value.checks,value.notes,value.content_hash)
    @app.post('/api/v1/projects/{pid}/exports')
    def export(pid:str):return reviews.export(Path(store.get(pid)['path']))

    dist=workspace/'desktop/dist'
    if dist.is_dir():app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
    return app
