import json,sys
from pathlib import Path
from engine.contracts import *
from engine.pipeline.artifacts import atomic_json,file_hash,object_hash
from engine.pipeline.runner import run_project,export_approved
from engine.pipeline.request_budget import RequestBudget
from engine.adapters.gemini.analyzer import GeminiAnalyzer
from engine.media.importer import import_source
from engine.media.probe import probe_source
from .store import now

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

def main(folder:Path):
    request=json.loads((folder/'request.json').read_text(encoding='utf-8'));root=Path(request['project_root']);settings=request['settings'];operation=request['operation']
    cancelled=lambda:(folder/'cancel').exists()
    progress={'stage':operation,'steps':{s:'pending' for s in ('import','transcribe','analyze','render','export')}}
    def stage(name,status):
        progress['stage']=name;progress['steps'][name]=status
        atomic_json(folder/'progress.json',progress)
        if status=='running' and cancelled():raise PipelineError('CANCELLED',name,'Cancelled')
    try:
        if cancelled():raise PipelineError('CANCELLED','job','Cancelled')
        if operation=='prepare':
            if not (root/'source.json').is_file():
                stage('import','running')
                source=import_source(request['source_input'],root)
                source=probe_source(source,Path(settings['ffprobe']));atomic_json(root/'source.json',source)
            stage('import','completed')
            source=Source.model_validate_json((root/'source.json').read_bytes())
            config=PipelineConfig(asr=ASRConfig(model_path=Path(settings['asr_model_path'])),analysis=AnalysisConfig(model=settings['gemini_model'],max_calls=settings['max_calls'],window_seconds=settings['window_seconds'],max_text_chars=settings['max_text_chars']),export=ExportConfig(output_root=root/'previews'),ffmpeg=Path(settings['ffmpeg']),ffprobe=Path(settings['ffprobe']))
            stage('transcribe','running')
            transcriber=PreparedTranscript(source,root) if (root/'transcript.json').is_file() else None
            run_project(source,config,root,cancelled,transcriber=transcriber,stop_after='transcribe')
            stage('transcribe','completed');stage('analyze','running')
            transcriber=PreparedTranscript(source,root)
            analyzer=GeminiAnalyzer(work_root=root/'work',budget=RequestBudget(folder/'budget.sqlite',config.analysis.max_calls))
            run_project(source,config,root,cancelled,transcriber=transcriber,analyzer=analyzer,stop_after='analyze')
            stage('analyze','completed')
            atomic_json(folder/'result.json',{'status':'completed','finished_at':now()});return 0
        stage(operation,'running')
        if operation=='import':
            source=import_source(request['source_input'],root)
            source=probe_source(source,Path(settings['ffprobe']));atomic_json(root/'source.json',source)
        elif operation=='export':
            packages=export_approved(root)
            if not packages:raise PipelineError('NO_APPROVED_CLIPS','export','No approved clips available.')
            stage(operation,'completed');atomic_json(folder/'result.json',{'status':'completed','finished_at':now(),'exports':packages});return 0
        else:
            source=Source.model_validate_json((root/'source.json').read_bytes())
            if file_hash(source.local_path)!=source.sha256:raise PipelineError('SOURCE_CHANGED','job','Source changed.')
            config=PipelineConfig(asr=ASRConfig(model_path=Path(settings['asr_model_path'])),analysis=AnalysisConfig(model=settings['gemini_model'],max_calls=settings['max_calls'],window_seconds=settings['window_seconds'],max_text_chars=settings['max_text_chars']),
                export=ExportConfig(output_root=root/'previews'),ffmpeg=Path(settings['ffmpeg']),ffprobe=Path(settings['ffprobe']))
            transcriber=PreparedTranscript(source,root) if (root/'transcript.json').is_file() else None
            if operation in ('analyze','render') and transcriber is None:raise PipelineError('TRANSCRIPT_REQUIRED','job','Transcribe first.')
            precomputed=PreparedAnalysis(root,transcriber.transcript).analysis if operation=='render' else None
            analyzer=GeminiAnalyzer(work_root=root/'work',budget=RequestBudget(folder/'budget.sqlite',config.analysis.max_calls)) if operation=='analyze' else None
            state=run_project(source,config,root,cancelled,transcriber=transcriber,analyzer=analyzer,stop_after=operation,precomputed_analysis=precomputed)
            if state.status=='failed':raise PipelineError('RENDER_FAILED','job','One or more previews failed technical QA.')
        stage(operation,'completed');atomic_json(folder/'result.json',{'status':'completed','finished_at':now()})
    except BaseException as exc:
        code=getattr(exc,'code','JOB_FAILED')
        stage(progress['stage'],'cancelled' if cancelled() or code=='CANCELLED' else 'failed')
        atomic_json(folder/'result.json',{'status':'cancelled' if cancelled() or code=='CANCELLED' else 'failed','finished_at':now(),'error':{'code':code,'message':'A tarefa não foi concluída. Verifique a fonte, o modelo e as configurações.'}})
        return 1
    return 0

if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1])))
