import json,sys
from pathlib import Path
from engine.contracts import *
from engine.pipeline.artifacts import atomic_json,file_hash,object_hash
from engine.pipeline.runner import run_project,export_approved,render_final
from engine.pipeline.request_budget import RequestBudget
from engine.adapters.gemini.analyzer import GeminiAnalyzer
from engine.adapters.openrouter.analyzer import OpenRouterAnalyzer
from engine.media.importer import import_source
from engine.media.probe import probe_source
from .store import now
from engine.pipeline.analysis_events import EventWriter
from engine.adapters.openshorts.windows import build_windows

def configure_analysis_requests(config,transcript,settings,folder):
    if not settings.get('automatic_calls',False):return
    if not transcript.words:raise PipelineError('NO_SPEECH','analyze','Não há fala transcrita para analisar.')
    windows=len(build_windows(transcript,max(config.analysis.window_seconds,config.analysis.clip_max_seconds*2) if config.analysis.clip_min_seconds>=60 else config.analysis.window_seconds,config.analysis.max_text_chars,overlap_seconds=config.analysis.clip_max_seconds if config.analysis.clip_min_seconds>=60 else 30))
    # Each window allows two transport attempts, plus one JSON repair with two attempts.
    # This covers every existing execution path without unlimited retries on permanent failures.
    config.analysis.max_calls=max(1,windows*4)
    atomic_json(folder/'request-policy.json',{'request_mode':'automatic','request_limit':config.analysis.max_calls,'windows':windows})
    EventWriter(folder/'analysis-events.jsonl').emit('requests_planned','Chamadas dimensionadas automaticamente pela transcrição; novas tentativas apenas em falhas recuperáveis.',windows=windows,request_limit=config.analysis.max_calls)

def pipeline_config(settings,root):
    ai_provider = settings.get('ai_provider', 'gemini')
    model = settings.get('openrouter_model', 'openrouter/free') if ai_provider == 'openrouter' else settings['gemini_model']
    return PipelineConfig(asr=ASRConfig(model_path=Path(settings['asr_model_path'])),
        analysis=AnalysisConfig(clip_min_seconds=60,model=model,max_calls=settings['max_calls'],window_seconds=settings['window_seconds'],max_text_chars=settings['max_text_chars'],clip_preferred_seconds=settings.get('clip_preferred_seconds',180),clip_max_seconds=settings.get('clip_max_seconds',300),show_thought_summaries=settings.get('show_thought_summaries',True)),
        selection=SelectionConfig(max_us=settings.get('clip_max_seconds',300)*1_000_000),pauses=PauseConfig(enabled=settings.get('pause_mode','conservative')=='conservative'),
        export=ExportConfig(output_root=root/'previews'),ffmpeg=Path(settings['ffmpeg']),ffprobe=Path(settings['ffprobe']))

def make_analyzer(settings,root,folder,config):
    budget=RequestBudget(folder/'budget.sqlite',config.analysis.max_calls)
    events_path=folder/'analysis-events.jsonl'
    if settings.get('ai_provider','gemini')=='openrouter':
        return OpenRouterAnalyzer(work_root=root/'work',budget=budget,events_path=events_path)
    return GeminiAnalyzer(work_root=root/'work',budget=budget,events_path=events_path)

class PreparedTranscript:
    def __init__(self,source,root):
        self.path=root/'transcript.json';self.transcript=TranscriptArtifact.model_validate_json(self.path.read_bytes())
        if self.transcript.source_id!=source.id or self.transcript.source_sha256!=source.sha256:raise PipelineError('SOURCE_CHANGED','transcribe','Existing transcript belongs to a different source.')
        self.cache_identity='adopted-existing-transcript:'+file_hash(self.path)
    def transcribe(self,audio,config):
        if any(w.end_us>audio.duration_us+100_000 for w in self.transcript.words):raise PipelineError('INVALID_TRANSCRIPT','transcribe','Transcript extends beyond source.')
        return self.transcript

class PreparedAnalysis:
    def __init__(self,root,transcript):
        self.analysis=AnalysisArtifact.model_validate_json((root/'analysis.json').read_bytes())
        if not self.analysis.complete or self.analysis.transcript_id!=transcript.transcript_id or set(self.analysis.covered_word_ids)!={w.id for w in transcript.words}:
            raise PipelineError('INCOMPLETE_ANALYSIS','analyze','Complete validated analysis required before rendering.')
    def analyze(self,*args,**kwargs):return self.analysis

def import_probed(input_value,root,ffprobe,cancelled=lambda:False):
    source=import_source(input_value,root,persist=False,cancelled=cancelled)
    try:source=probe_source(source,ffprobe)
    except PipelineError as exc:
        from engine.media.source_errors import MESSAGES
        raise PipelineError('SOURCE_INVALID','import',MESSAGES['SOURCE_INVALID']) from exc
    atomic_json(root/'source.json',source)
    return source

def _main(folder:Path):
    request=json.loads((folder/'request.json').read_text(encoding='utf-8'));root=Path(request['project_root']);settings=request['settings'];operation=request['operation']
    cancelled=lambda:(folder/'cancel').exists()
    progress={'stage':operation,'steps':{s:'pending' for s in ('import','transcribe','analyze','render','export')}}
    def stage(name,status):
        from engine.pipeline.telemetry import observe
        # Pipeline stages own their timing. Operation status must not start or
        # complete the same timed phase a second time.
        if name in ('import','export') and status in ('running','completed'):
            observe(name,finished=status=='completed')
        progress['stage']=name;progress['steps'][name]=status
        atomic_json(folder/'progress.json',progress)
        if status=='running' and cancelled():raise PipelineError('CANCELLED',name,'Cancelled')
    try:
        if cancelled():raise PipelineError('CANCELLED','job','Cancelled')
        if operation=='prepare':
            if not (root/'source.json').is_file():
                stage('import','running')
                source=import_probed(request['source_input'],root,Path(settings['ffprobe']),cancelled=cancelled)
            stage('import','completed')
            source=Source.model_validate_json((root/'source.json').read_bytes())
            config=pipeline_config(settings,root)
            stage('transcribe','running')
            transcriber=PreparedTranscript(source,root) if (root/'transcript.json').is_file() else None
            run_project(source,config,root,cancelled,transcriber=transcriber,stop_after='transcribe')
            stage('transcribe','completed');stage('analyze','running')
            transcriber=PreparedTranscript(source,root)
            configure_analysis_requests(config,transcriber.transcript,settings,folder)
            analyzer=make_analyzer(settings,root,folder,config)
            run_project(source,config,root,cancelled,transcriber=transcriber,analyzer=analyzer,stop_after='analyze')
            stage('analyze','completed')
            atomic_json(folder/'result.json',{'status':'completed','finished_at':now()});return 0
        stage(operation,'running')
        if operation=='import':
            source=import_probed(request['source_input'],root,Path(settings['ffprobe']),cancelled=cancelled)
        elif operation=='export':
            packages=export_approved(root,cancelled=cancelled)
            if not packages:raise PipelineError('NO_APPROVED_CLIPS','export','No technically valid and editorially approved clips available.')
            stage(operation,'completed');atomic_json(folder/'result.json',{'status':'completed','finished_at':now(),'exports':packages});return 0
        elif operation=='render_final':
            def final_progress(value):
                progress.update(value);atomic_json(folder/'progress.json',progress)
            render_final(root,request.get('selection',{}).get('revision_ids'),Path(settings['ffmpeg']),Path(settings['ffprobe']),cancelled=cancelled,progress=final_progress)
        else:
            source=Source.model_validate_json((root/'source.json').read_bytes())
            if file_hash(source.local_path)!=source.sha256:raise PipelineError('SOURCE_CHANGED','job','Source changed.')
            config=pipeline_config(settings,root)
            transcriber=PreparedTranscript(source,root) if (root/'transcript.json').is_file() else None
            if operation in ('analyze','render','preview') and transcriber is None:raise PipelineError('TRANSCRIPT_REQUIRED','job','Transcribe first.')
            precomputed=PreparedAnalysis(root,transcriber.transcript).analysis if operation in ('render','preview') else None
            if operation=='analyze':configure_analysis_requests(config,transcriber.transcript,settings,folder)
            analyzer=make_analyzer(settings,root,folder,config) if operation=='analyze' else None
            def pipeline_progress(value):
                progress.update(value);atomic_json(folder/'progress.json',progress)
            selection=request.get('selection',{})
            state=run_project(source,config,root,cancelled,transcriber=transcriber,analyzer=analyzer,stop_after=operation,precomputed_analysis=precomputed,candidate_ids=selection.get('candidate_ids'),analysis_hash=selection.get('analysis_hash'),progress=pipeline_progress if operation in ('render','preview') else None)
            if state.status=='failed':raise PipelineError('RENDER_FAILED','job','One or more previews failed technical QA.')
        stage(operation,'completed');atomic_json(folder/'result.json',{'status':'completed','finished_at':now()})
    except BaseException as exc:
        code=getattr(exc,'code','JOB_FAILED')
        if operation=='analyze' or operation=='prepare' and progress['steps'].get('analyze')=='running':EventWriter(folder/'analysis-events.jsonl').emit('analysis_stopped','Análise interrompida; os resumos já recebidos são parciais e não aprovam cortes.',error_code=code)
        stage(progress['stage'],'cancelled' if cancelled() or code=='CANCELLED' else 'failed')
        provider_name = 'OpenRouter' if settings.get('ai_provider') == 'openrouter' else 'Gemini'
        messages={'RENDER_FAILED':'Uma ou mais prévias falharam. As prontas foram preservadas; retome somente as pendentes.',
            'PROVIDER_TIMEOUT':f'O {provider_name} excedeu o tempo de resposta. Continue a análise; janelas validadas serão reaproveitadas.',
            'PROVIDER_UNAVAILABLE':f'Falha de comunicação com o {provider_name}. Continue a análise para tentar as janelas restantes.',
            'PROVIDER_RATE_LIMIT':f'O {provider_name} atingiu a cota ou o limite de solicitações deste modelo. Aguarde a renovação antes de continuar. As janelas já validadas foram preservadas.',
            'PROVIDER_INVALID_OUTPUT':f'O {provider_name} não entregou uma resposta estruturada válida. As janelas já validadas foram preservadas.',
            'PROVIDER_OUTPUT_TRUNCATED':f'A resposta do {provider_name} foi truncada antes de concluir o JSON. As janelas validadas foram preservadas.',
            'PROVIDER_AUTH':f'O {provider_name} recusou a autenticação. Verifique a chave e o acesso ao modelo.'}
        from engine.media.source_errors import MESSAGES
        messages.update(MESSAGES)
        atomic_json(folder/'result.json',{'status':'cancelled' if cancelled() or code=='CANCELLED' else 'failed','finished_at':now(),'error':{'code':code,'message':messages.get(code,'A tarefa não foi concluída. Verifique a fonte, o modelo e as configurações.')}})
        return 1
    return 0

def main(folder:Path):
    from engine.system.job_startup import start_startup_monitor
    from engine.pipeline.job_telemetry import run_observed
    running=start_startup_monitor(folder)
    if running:running()
    return run_observed(folder,_main)

if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1])))
