import json,time,sys,tempfile
from uuid import uuid5,NAMESPACE_URL
import httpx
from types import SimpleNamespace
from email.utils import parsedate_to_datetime
from datetime import datetime,timezone
from pathlib import Path
from typing import Protocol,Literal
from pydantic import BaseModel,ConfigDict,Field
from engine.contracts import TranscriptArtifact,AnalysisConfig,AnalysisArtifact,Topic,Candidate,PipelineError
from engine.pipeline.artifacts import object_hash,atomic_json,file_hash
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
    summary:str=Field(max_length=600)
    evidence_word_ids:list[str]=Field(max_length=8)

class ResponseCandidate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    topic_id:str
    start_word_id:str
    end_word_id:str
    evidence_word_ids:list[str]=Field(max_length=8)
    rationale:str=Field(max_length=800)
    editorial:ResponseFlags
    context_before_word_ids:list[str]=Field(default_factory=list,max_length=8)
    context_after_word_ids:list[str]=Field(default_factory=list,max_length=8)
    title_suggestion:str=Field(min_length=1,max_length=80)
    opening_suggestion:str=Field(default='',max_length=72)
    description_suggestion:str=Field(default='',max_length=400)

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
        self.code=data.get('code');self.transport=data.get('transport',False);self.timeout=data.get('type') in ('TimeoutError','ReadTimeout','ConnectTimeout','ProcessTimeout')
        self.response=SimpleNamespace(headers={'Retry-After':data['retry_after']} if data.get('retry_after') else {})
        super().__init__('Isolated Gemini request failed; no secret details exposed.')

def isolated_request(root,cancelled,timeout,**kwargs):
    root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gemini-',dir=root) as folder:
        folder=Path(folder);request=folder/'request.json';response=folder/'response.json'
        atomic_json(request,{'model':kwargs['model'],'contents':kwargs['contents'],'timeout_s':timeout,'events_path':str(kwargs['events_path']) if kwargs.get('events_path') else None,'context':kwargs.get('context',{}),'show_thought_summaries':kwargs.get('show_thought_summaries',True)})
        try:r=run_process([sys.executable,'-X','utf8','-m','engine.adapters.gemini.request_worker',str(request),str(response)],cancelled=cancelled,timeout_s=timeout+10,capture_output=True,text=True,encoding='utf-8')
        except PipelineError as exc:
            if exc.code=='PROCESS_TIMEOUT':raise WorkerRequestError({'transport':True,'type':'ProcessTimeout'}) from None
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
        self.checkpoint_root=Path(work_root)/'analysis-checkpoints' if work_root is not None else None

    def publish_cached(self,analysis):
        if self.events_path:atomic_json(self.events_path.parent/'analysis-preview.json',{'analysis':analysis.model_dump(mode='json'),'completed_windows':len(analysis.responses),'total_windows':len(analysis.responses)})
        EventWriter(self.events_path).emit('analysis_cache_reused','Análise existente reaproveitada. Não houve nova chamada nem novos resumos Gemini.',model=analysis.model,topics=[t.model_dump(mode='json') for t in analysis.topics],candidates=[c.model_dump(mode='json') for c in analysis.candidates])

    def analyze(self,transcript:TranscriptArtifact,config:AnalysisConfig,cancelled=lambda:False) -> AnalysisArtifact:
        from .checkpoints import load_checkpoint,save_checkpoint
        if config.offline:raise PipelineError('OFFLINE_PROVIDER','analyze','Gemini requires internet; local stages and review remain available.')
        if not transcript.words:raise PipelineError('NO_SPEECH','analyze','No transcript; never upload silent video.')
        request=self.request;secret=''
        if request is None:
            secret=get_gemini_key()
            request=lambda **kw:isolated_request(self.work_root,cancelled,config.timeout_s,events_path=self.events_path,show_thought_summaries=config.show_thought_summaries,context=self.context,**kw)
        writer=EventWriter(self.events_path,secret)
        def check_cancelled():
            if cancelled():raise PipelineError('CANCELLED','analyze','Cancelled; no further Gemini requests.')
        def validate(parsed,window):
            valid_ids={w.id for w in window['words']};order={w.id:i for i,w in enumerate(window['words'])}
            for topic in parsed.topics:
                if not set(topic.evidence_word_ids).issubset(valid_ids):raise ValueError('unknown topic word IDs')
            for candidate in parsed.candidates:
                refs=[candidate.start_word_id,candidate.end_word_id,*candidate.evidence_word_ids,*candidate.context_before_word_ids,*candidate.context_after_word_ids]
                if not set(refs).issubset(valid_ids):raise ValueError('unknown candidate word IDs')
                if candidate.topic_id not in {t.id for t in parsed.topics}:raise ValueError('unknown topic ID')
                if order[candidate.start_word_id]>order[candidate.end_word_id]:raise ValueError('reversed boundaries')
            return parsed
        prompt=(Path(__file__).resolve().parents[2]/'prompts/analysis_v1.txt').read_text(encoding='utf-8')
        prompt=prompt.replace('{MIN_SECONDS}',str(config.clip_min_seconds)).replace('{MAX_SECONDS}',str(config.clip_max_seconds)).replace('{PREFERRED_SECONDS}',str(config.clip_preferred_seconds))
        prompt+='\nNão encerre um argumento no meio. Se a conclusão exigir mais que o máximo, não proponha esse corte. Resumos de análise, quando disponíveis, devem estar em português brasileiro.'
        global_text=' '.join(w.text for w in transcript.words)
        prompt+='\n<CONTEXTO_GLOBAL>\n'+global_text+'\n</CONTEXTO_GLOBAL>'
        topics=[];candidates=[];covered=set();hashes=[];responses=[];calls=0
        windows=build_windows(transcript,max(config.window_seconds,config.clip_max_seconds*2) if config.clip_min_seconds>=60 else config.window_seconds,config.max_text_chars,overlap_seconds=config.clip_max_seconds if config.clip_min_seconds>=60 else 30)
        runtime={'analyzer':file_hash(Path(__file__)),'worker':file_hash(Path(__file__).with_name('request_worker.py')),'checkpoints':file_hash(Path(__file__).with_name('checkpoints.py')),'schema':GeminiResponse.model_json_schema(),'policy':2}
        identity={'transcript':object_hash(transcript),'model':config.model,'prompt':object_hash(prompt),'compatibility':{'schema':GeminiResponse.model_json_schema(),'policy':2}}
        from engine.api.projects import read_json
        previous=read_json(self.work_root/'analysis-preview.json',{}) or {}
        previous_analysis=previous.get('analysis',{})
        compatible_previous=(previous_analysis.get('transcript_id')==str(transcript.transcript_id) and previous_analysis.get('model')==config.model and previous_analysis.get('prompt_hash')==object_hash(prompt))
        planned=[]
        for window in windows:
            text=prompt+'\n<TRANSCRICAO>\n'+window['text']+'\n</TRANSCRICAO>'
            key=object_hash({**identity,'window_id':window['id'],'word_ids':[w.id for w in window['words']],'text':text})
            cached=load_checkpoint(self.checkpoint_root,key)
            if cached is None:
                legacy_key=object_hash({**{k:v for k,v in identity.items() if k!='compatibility'},'runtime':runtime,'window_id':window['id'],'word_ids':[w.id for w in window['words']],'text':text})
                cached=load_checkpoint(self.checkpoint_root,legacy_key)
            if cached is None and compatible_previous and self.checkpoint_root:
                for path in self.checkpoint_root.glob('*.json'):
                    old=load_checkpoint(self.checkpoint_root,path.stem)
                    if old and old['provenance'].get('window_id')==window['id'] and old['payload_hashes'] and set(old['payload_hashes'])<=set(previous_analysis.get('payload_hashes',[])):
                        cached=old;break
            if cached:
                try:
                    validate(GeminiResponse.model_validate(cached['response']),window)
                    if cached['provenance']['window_id']!=window['id'] or 'usage' not in cached['provenance'] or not isinstance(cached['payload_hashes'],list) or not all(isinstance(h,str) and len(h)==64 for h in cached['payload_hashes']):raise ValueError('invalid checkpoint provenance')
                except (ValueError,TypeError,KeyError):cached=None
            planned.append((window,text,key,cached))
        missing=sum(cached is None for _,_,_,cached in planned)
        writer.emit('analysis_started','Analisando com contexto do vídeo inteiro e retomada de janelas validadas.',model=config.model,windows=len(windows),completed_windows=len(windows)-missing,remaining_windows=missing,request_limit=config.max_calls)
        if missing>min(config.max_calls,self.budget.remaining if self.budget else config.max_calls):
            raise PipelineError('PROVIDER_BUDGET','analyze','Request budget cannot cover remaining windows; no request made.')
        for index,(window,text,key,cached) in enumerate(planned,1):
            check_cancelled();window_hashes=[]
            context={'window_id':window['id'],'window_index':index,'windows':len(windows)}
            writer.emit('window_started',f'Janela {index} de {len(windows)}.',**context,source_start_us=window['words'][0].start_us,source_end_us=max(w.end_us for w in window['words']))
            if cached:
                parsed=validate(GeminiResponse.model_validate(cached['response']),window)
                provenance=cached['provenance'];hashes.extend(cached['payload_hashes'])
                self.context={**context,'attempt':0,'model':config.model}
                writer.emit('window_reused','Janela já validada reaproveitada. Nenhuma nova chamada ao Gemini.',**self.context,checkpoint_key=key)
            else:
                repair=False
                while True:
                    response=None
                    for attempt in range(2):
                        check_cancelled()
                        if calls>=config.max_calls:raise PipelineError('PROVIDER_BUDGET','analyze','Gemini request budget exhausted; analysis not complete.')
                        payload_hash=object_hash({'model':config.model,'contents':text,'prompt_version':config.prompt_version,'runtime':runtime,'show_thought_summaries':config.show_thought_summaries})
                        if self.budget:self.budget.reserve(payload_hash)
                        calls+=1;hashes.append(payload_hash);window_hashes.append(payload_hash)
                        self.context={**context,'attempt':calls,'model':config.model}
                        writer.emit('request_started','Solicitação enviada; aguardando resposta estruturada do Gemini.',**self.context)
                        try:
                            response=request(model=config.model,contents=text,config={'temperature':0,'response_mime_type':'application/json','response_json_schema':GeminiResponse.model_json_schema()})
                            break
                        except PipelineError:raise
                        except Exception as exc:
                            timeout=isinstance(exc,(TimeoutError,httpx.TimeoutException)) or getattr(exc,'timeout',False)
                            writer.emit('request_failed','Tempo de resposta excedido.' if timeout else 'Solicitação não concluída.',**self.context,error_code='PROVIDER_TIMEOUT' if timeout else 'PROVIDER_UNAVAILABLE')
                            code=getattr(exc,'code',None) or getattr(exc,'status_code',None)
                            if code==429:
                                writer.emit('provider_rate_limited','O Gemini atingiu a cota ou o limite de solicitações. Aguarde a renovação do limite antes de continuar.',**self.context,error_code='PROVIDER_RATE_LIMIT')
                                raise PipelineError('PROVIDER_RATE_LIMIT','analyze','Gemini quota/rate limit reached; no immediate retry. Validated windows remain available.') from None
                            if code in (401,403):raise PipelineError('PROVIDER_AUTH','analyze','Gemini authentication/permission failed.') from None
                            if code=='PROVIDER_OUTPUT_TRUNCATED':raise PipelineError(code,'analyze','Gemini output token limit reached; no complete JSON received.') from None
                            transport_types=(TimeoutError,ConnectionError,httpx.TimeoutException,httpx.NetworkError)
                            try:
                                import httpx2
                                transport_types+=(httpx2.TimeoutException,httpx2.NetworkError)
                            except ImportError:pass
                            retryable=code in (429,500,502,503,504) or isinstance(exc,transport_types) or getattr(exc,'transport',False)
                            if not retryable or attempt==1:raise PipelineError('PROVIDER_TIMEOUT' if timeout else 'PROVIDER_UNAVAILABLE','analyze','Gemini request failed; validated windows remain available to resume.',retryable) from None
                            writer.emit('request_retry','Repetindo após falha recuperável, preservando janelas concluídas.',**self.context)
                            delay=retry_delay(exc)
                            while delay>0:
                                check_cancelled();step=min(.2,delay);self.sleep(step);delay-=step
                    try:parsed=validate(GeminiResponse.model_validate_json(getattr(response,'text','') or ''),window)
                    except (ValueError,TypeError):
                        writer.emit('response_rejected','Resposta descartada: JSON ou referências inválidas.',**self.context)
                        if repair:raise PipelineError('PROVIDER_INVALID_OUTPUT','analyze','Invalid structured JSON after one repair; analysis incomplete.') from None
                        repair=True;text+='\nA resposta anterior não respeitou o schema ou IDs. Retorne JSON válido usando somente os IDs da transcrição.'
                        continue
                    usage=getattr(response,'usage_metadata',None)
                    provenance={'window_id':window['id'],'model_version':getattr(response,'model_version',None),'usage':usage.model_dump(mode='json') if hasattr(usage,'model_dump') else None}
                    save_checkpoint(self.checkpoint_root,key,parsed,provenance,window_hashes)
                    break
            prefix=window['id']+':'
            domain_topics=[Topic.model_validate(t.model_dump()) for t in parsed.topics]
            domain_candidates=[Candidate.model_validate(c.model_dump()) for c in parsed.candidates]
            for topic in domain_topics:topic.id=prefix+topic.id
            for ordinal,candidate in enumerate(domain_candidates):
                candidate.topic_id=prefix+candidate.topic_id
                candidate.id=uuid5(NAMESPACE_URL,'autoclip:'+key+':'+str(ordinal))
            topics.extend(domain_topics);candidates.extend(domain_candidates);covered.update(w.id for w in window['words']);responses.append(provenance)
            if self.events_path:
                preview=AnalysisArtifact(transcript_id=transcript.transcript_id,topics=topics,candidates=candidates,clip_min_seconds=config.clip_min_seconds,complete=False,covered_word_ids=sorted(covered),model=config.model,prompt_hash=object_hash(prompt),payload_hashes=hashes,responses=responses)
                snapshot={'analysis':preview.model_dump(mode='json'),'completed_windows':index,'total_windows':len(windows)}
                atomic_json(self.events_path.parent/'analysis-preview.json',snapshot)
                if self.checkpoint_root is not None:atomic_json(self.work_root/'analysis-preview.json',snapshot)
            writer.emit('window_validated','Janela validada e salva para retomada; propostas aguardam revisão.',**self.context,topics=[t.model_dump(mode='json') for t in domain_topics],candidates=[{**c.model_dump(mode='json'),'start_us':next(w.start_us for w in window['words'] if w.id==c.start_word_id),'end_us':max(w.end_us for w in window['words'][next(i for i,w in enumerate(window['words']) if w.id==c.start_word_id):next(i for i,w in enumerate(window['words']) if w.id==c.end_word_id)+1])} for c in domain_candidates],usage=provenance['usage'])
        if covered!={w.id for w in transcript.words}:raise PipelineError('INCOMPLETE_ANALYSIS','analyze','Some transcript words were not covered.')
        # Consolidate after every window, preserving coverage independently of proposals.
        from engine.editorial.select import select_candidates
        from engine.contracts import SelectionConfig
        topic_labels={t.id:' '.join(t.label.casefold().split()) for t in topics}
        distinct=[];seen_topics=set()
        full=AnalysisArtifact(transcript_id=transcript.transcript_id,topics=topics,candidates=candidates,clip_min_seconds=config.clip_min_seconds,complete=True,covered_word_ids=sorted(covered),model=config.model,prompt_hash=object_hash(prompt),payload_hashes=hashes,responses=responses)
        valid=select_candidates(full,transcript,SelectionConfig(min_us=config.clip_min_seconds*1_000_000,max_us=config.clip_max_seconds*1_000_000,max_clips=10)).candidates
        for candidate in valid:
            label=topic_labels.get(candidate.topic_id,candidate.topic_id)
            if label in seen_topics:continue
            seen_topics.add(label);distinct.append(candidate)
        candidates=distinct
        writer.emit('analysis_completed','Todas as janelas foram analisadas e validadas.',requests_used=calls,reused_windows=len(windows)-missing,topics_count=len(topics),candidates_count=len(candidates))
        return AnalysisArtifact(transcript_id=transcript.transcript_id,topics=topics,candidates=candidates,clip_min_seconds=config.clip_min_seconds,complete=True,covered_word_ids=sorted(covered),model=config.model,prompt_hash=object_hash(prompt),payload_hashes=hashes,responses=responses)
