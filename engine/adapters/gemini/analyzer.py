import json,time,sys,tempfile
import httpx
from types import SimpleNamespace
from email.utils import parsedate_to_datetime
from datetime import datetime,timezone
from pathlib import Path
from typing import Protocol,Literal
from pydantic import BaseModel,ConfigDict,Field
from engine.contracts import TranscriptArtifact,AnalysisConfig,AnalysisArtifact,Topic,Candidate,PipelineError
from engine.pipeline.artifacts import object_hash,atomic_json
from engine.pipeline.cancellation import run_process
from engine.adapters.openshorts.windows import build_windows
from engine.pipeline.analysis_events import EventWriter
from .credentials import get_gemini_key


class ResponseFlags(BaseModel):
    model_config=ConfigDict(extra='forbid')
    completeness:Literal['yes','no','uncertain']
    standalone_context:Literal['yes','no','uncertain']
    qualification_preserved:Literal['yes','no','uncertain']

class ResponseTopic(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id:str
    label:str
    summary:str
    evidence_word_ids:list[str]

class ResponseCandidate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    topic_id:str
    start_word_id:str
    end_word_id:str
    evidence_word_ids:list[str]
    rationale:str
    editorial:ResponseFlags
    context_before_word_ids:list[str]=Field(default_factory=list)
    context_after_word_ids:list[str]=Field(default_factory=list)
    title_suggestion:str=''
    description_suggestion:str=''

class GeminiResponse(BaseModel):
    model_config=ConfigDict(extra='forbid')
    topics:list[ResponseTopic]
    candidates:list[ResponseCandidate]

def retry_delay(error):
    raw=getattr(getattr(error,'response',None),'headers',{}).get('Retry-After')
    if raw is None:return 2
    try:return max(0,min(30,float(raw)))
    except (ValueError,TypeError):
        try:return max(0,min(30,(parsedate_to_datetime(raw)-datetime.now(timezone.utc)).total_seconds()))
        except (ValueError,TypeError):return 2

class WorkerRequestError(Exception):
    def __init__(self,data):
        self.code=data.get('code');self.transport=data.get('transport',False)
        self.response=SimpleNamespace(headers={'Retry-After':data['retry_after']} if data.get('retry_after') else {})
        super().__init__('Isolated Gemini request failed; no secret details exposed.')

def isolated_request(root,cancelled,timeout,**kwargs):
    root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gemini-',dir=root) as folder:
        folder=Path(folder);request=folder/'request.json';response=folder/'response.json'
        atomic_json(request,{'model':kwargs['model'],'contents':kwargs['contents'],'timeout_s':timeout,'events_path':str(kwargs['events_path']) if kwargs.get('events_path') else None,'context':kwargs.get('context',{}),'show_thought_summaries':kwargs.get('show_thought_summaries',True)})
        try:r=run_process([sys.executable,'-X','utf8','-m','engine.adapters.gemini.request_worker',str(request),str(response)],cancelled=cancelled,timeout_s=timeout+10,capture_output=True,text=True,encoding='utf-8')
        except PipelineError as exc:
            if exc.code=='PROCESS_TIMEOUT':raise WorkerRequestError({'transport':True}) from None
            raise
        if not response.exists():raise WorkerRequestError({'transport':True})
        data=json.loads(response.read_text(encoding='utf-8'))
        if 'error' in data:
            atomic_json(root/'last-request-error.json',data['error'])
            raise WorkerRequestError(data['error'])
        usage=data.get('usage')
        return SimpleNamespace(text=data['text'],model_version=data.get('model_version'),usage_metadata=SimpleNamespace(model_dump=lambda **kw:usage) if usage else None)

class Analyzer(Protocol):
    def analyze(self,transcript:TranscriptArtifact,config:AnalysisConfig,cancelled=lambda:False) -> AnalysisArtifact: ...

class GeminiAnalyzer:
    def __init__(self,request=None,sleep=time.sleep,work_root=None,budget=None,events_path=None):
        self.request=request;self.sleep=sleep;self.work_root=Path(work_root) if work_root else Path.cwd()/'.runtime-tmp'
        self.budget=budget
        self.events_path=Path(events_path) if events_path else None

    def publish_cached(self,analysis):
        EventWriter(self.events_path).emit('analysis_cache_reused','Análise existente reaproveitada. Não houve nova chamada nem novos resumos Gemini.',model=analysis.model,topics=[t.model_dump(mode='json') for t in analysis.topics],candidates=[c.model_dump(mode='json') for c in analysis.candidates])

    def analyze(self,transcript:TranscriptArtifact,config:AnalysisConfig,cancelled=lambda:False) -> AnalysisArtifact:
        if config.offline: raise PipelineError('OFFLINE_PROVIDER','analyze','Gemini requires internet; local stages and review remain available.')
        if not transcript.words: raise PipelineError('NO_SPEECH','analyze','No transcript; never upload silent video.')
        request=self.request
        secret=''
        if request is None:
            secret=get_gemini_key()
            request=lambda **kw:isolated_request(self.work_root,cancelled,config.timeout_s,events_path=self.events_path,show_thought_summaries=config.show_thought_summaries,context=self.context,**kw)
        writer=EventWriter(self.events_path,secret)
        def check_cancelled():
            if cancelled():raise PipelineError('CANCELLED','analyze','Cancelled; no further Gemini requests.')
        prompt=(Path(__file__).resolve().parents[2]/'prompts/analysis_v1.txt').read_text(encoding='utf-8')
        prompt=prompt.replace('20–60 segundos aproximadamente',f'20–{config.clip_max_seconds} segundos; prefira cerca de {config.clip_preferred_seconds} segundos, mas priorize concluir o raciocínio')
        prompt+='\nNão encerre um argumento no meio. Se a conclusão exigir mais que o máximo, não proponha esse corte. Resumos de análise, quando disponíveis, devem estar em português brasileiro.'
        topics=[];candidates=[];covered=set();hashes=[];responses=[];calls=0
        windows=build_windows(transcript,config.window_seconds,config.max_text_chars)
        writer.emit('analysis_started','Preparando a análise da transcrição.',model=config.model,windows=len(windows),request_limit=config.max_calls)
        if len(windows)>min(config.max_calls,self.budget.remaining if self.budget else config.max_calls):
            raise PipelineError('PROVIDER_BUDGET','analyze','Request budget cannot cover all windows; no request made.')
        try:
            for index,window in enumerate(windows,1):
                check_cancelled()
                writer.emit('window_started',f'Analisando janela {index} de {len(windows)}.',window_id=window['id'],window_index=index,windows=len(windows),source_start_us=window['words'][0].start_us,source_end_us=max(w.end_us for w in window['words']))
                text=prompt+'\n<TRANSCRICAO>\n'+window['text']+'\n</TRANSCRICAO>'
                valid_ids={w.id for w in window['words']};repair=False
                while True:
                    response=None
                    for attempt in range(2):
                        check_cancelled()
                        if calls>=config.max_calls:
                            raise PipelineError('PROVIDER_BUDGET','analyze','Gemini request budget exhausted; analysis not complete.')
                        payload_hash=object_hash({'model':config.model,'contents':text,'prompt_version':config.prompt_version,'show_thought_summaries':config.show_thought_summaries})
                        if self.budget:self.budget.reserve(payload_hash)
                        calls+=1;hashes.append(payload_hash)
                        self.context={'window_id':window['id'],'window_index':index,'attempt':calls,'model':config.model}
                        writer.emit('request_started','Solicitação enviada; aguardando o Gemini.',**self.context)
                        try:
                            response=request(model=config.model,contents=text,config={'temperature':0,'response_mime_type':'application/json','response_json_schema':GeminiResponse.model_json_schema()})
                            break
                        except PipelineError:raise
                        except Exception as exc:
                            writer.emit('request_failed','A solicitação não foi concluída; nenhuma seleção desta tentativa foi validada.',**self.context)
                            code=getattr(exc,'code',None) or getattr(exc,'status_code',None)
                            if code in (401,403): raise PipelineError('PROVIDER_AUTH','analyze','Gemini authentication/permission failed.') from None
                            transport_types=(TimeoutError,ConnectionError,httpx.TimeoutException,httpx.NetworkError)
                            try:
                                import httpx2
                                transport_types+=(httpx2.TimeoutException,httpx2.NetworkError)
                            except ImportError:pass
                            retryable=code in (429,500,502,503,504) or isinstance(exc,transport_types) or getattr(exc,'transport',False)
                            if not retryable or attempt==1:
                                raise PipelineError('PROVIDER_UNAVAILABLE','analyze','Gemini request failed; no provider fallback.',retryable) from None
                            writer.emit('request_retry','Nova tentativa dentro do limite confirmado.',**self.context)
                            delay=retry_delay(exc)
                            while delay>0:
                                check_cancelled();step=min(.2,delay);self.sleep(step);delay-=step
                    try:
                        parsed=GeminiResponse.model_validate_json(getattr(response,'text','') or '')
                        for topic in parsed.topics:
                            if not set(topic.evidence_word_ids).issubset(valid_ids): raise ValueError('unknown topic word IDs')
                        for candidate in parsed.candidates:
                            refs=[candidate.start_word_id,candidate.end_word_id,*candidate.evidence_word_ids,*candidate.context_before_word_ids,*candidate.context_after_word_ids]
                            if not set(refs).issubset(valid_ids): raise ValueError('unknown candidate word IDs')
                            if candidate.topic_id not in {t.id for t in parsed.topics}: raise ValueError('unknown topic ID')
                            order={w.id:i for i,w in enumerate(window['words'])}
                            if order[candidate.start_word_id]>order[candidate.end_word_id]:raise ValueError('reversed boundaries')
                    except (ValueError,TypeError):
                        writer.emit('response_rejected','Resposta descartada: JSON ou referências inválidas.',**self.context)
                        if repair: raise PipelineError('PROVIDER_INVALID_OUTPUT','analyze','Invalid structured JSON after one repair; analysis incomplete.') from None
                        repair=True;text+='\nA resposta anterior não respeitou o schema ou IDs. Retorne JSON válido usando somente os IDs da transcrição.'
                        continue
                    prefix=window['id']+':'
                    domain_topics=[Topic.model_validate(t.model_dump()) for t in parsed.topics]
                    domain_candidates=[Candidate.model_validate(c.model_dump()) for c in parsed.candidates]
                    for topic in domain_topics:topic.id=prefix+topic.id
                    for candidate in domain_candidates:candidate.topic_id=prefix+candidate.topic_id
                    topics.extend(domain_topics);candidates.extend(domain_candidates);covered.update(valid_ids)
                    usage=getattr(response,'usage_metadata',None)
                    responses.append({'window_id':window['id'],'model_version':getattr(response,'model_version',None),'usage':usage.model_dump(mode='json') if hasattr(usage,'model_dump') else None})
                    writer.emit('window_validated','Resposta estruturada validada; propostas ainda exigem seleção e revisão editorial.',**self.context,topics=[t.model_dump(mode='json') for t in domain_topics],candidates=[{**c.model_dump(mode='json'),'start_us':next(w.start_us for w in window['words'] if w.id==c.start_word_id),'end_us':max(w.end_us for w in window['words'][next(i for i,w in enumerate(window['words']) if w.id==c.start_word_id):next(i for i,w in enumerate(window['words']) if w.id==c.end_word_id)+1])} for c in domain_candidates],usage=responses[-1]['usage'])
                    break
            if covered!={w.id for w in transcript.words}:
                raise PipelineError('INCOMPLETE_ANALYSIS','analyze','Some transcript words were not covered.')
            writer.emit('analysis_completed','Todas as janelas foram analisadas e validadas.',requests_used=calls,topics_count=len(topics),candidates_count=len(candidates))
            return AnalysisArtifact(transcript_id=transcript.transcript_id,topics=topics,candidates=candidates,complete=True,covered_word_ids=sorted(covered),model=config.model,prompt_hash=object_hash(prompt),payload_hashes=hashes,responses=responses)
        finally:
            pass
