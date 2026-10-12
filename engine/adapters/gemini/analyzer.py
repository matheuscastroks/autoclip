import json,time
from pathlib import Path
from typing import Protocol
from pydantic import BaseModel,ConfigDict,Field
from engine.contracts import TranscriptArtifact,AnalysisConfig,AnalysisArtifact,Topic,Candidate,PipelineError
from engine.pipeline.artifacts import object_hash
from engine.adapters.openshorts.windows import build_windows
from .credentials import get_gemini_key


class GeminiResponse(BaseModel):
    model_config=ConfigDict(extra='forbid')
    topics:list[Topic]=Field(default_factory=list)
    candidates:list[Candidate]=Field(default_factory=list)

class Analyzer(Protocol):
    def analyze(self,transcript:TranscriptArtifact,config:AnalysisConfig) -> AnalysisArtifact: ...

class GeminiAnalyzer:
    def __init__(self,request=None,sleep=time.sleep):
        self.request=request;self.sleep=sleep

    def analyze(self,transcript:TranscriptArtifact,config:AnalysisConfig) -> AnalysisArtifact:
        if config.offline: raise PipelineError('OFFLINE_PROVIDER','analyze','Gemini requires internet; local stages and review remain available.')
        if not transcript.words: raise PipelineError('NO_SPEECH','analyze','No transcript; never upload silent video.')
        request=self.request;client=None
        if request is None:
            from google import genai
            from google.genai import types
            # Disable SDK's own retry layer: this engine owns the request budget.
            options=types.HttpOptions(timeout=config.timeout_s*1000,retry_options=types.HttpRetryOptions(attempts=1))
            client=genai.Client(api_key=get_gemini_key(),http_options=options)
            request=client.models.generate_content
        prompt=(Path(__file__).resolve().parents[2]/'prompts/analysis_v1.txt').read_text(encoding='utf-8')
        topics=[];candidates=[];covered=set();hashes=[];responses=[];calls=0
        try:
            for window in build_windows(transcript):
                text=prompt+'\n<TRANSCRICAO>\n'+window['text']+'\n</TRANSCRICAO>'
                valid_ids={w.id for w in window['words']};repair=False
                while True:
                    response=None
                    for attempt in range(2):
                        if calls>=config.max_calls:
                            raise PipelineError('PROVIDER_BUDGET','analyze','Gemini request budget exhausted; analysis not complete.')
                        calls+=1;hashes.append(object_hash({'model':config.model,'contents':text,'prompt_version':config.prompt_version}))
                        try:
                            response=request(model=config.model,contents=text,config={'temperature':0,'response_mime_type':'application/json','response_schema':GeminiResponse})
                            break
                        except Exception as exc:
                            code=getattr(exc,'code',None) or getattr(exc,'status_code',None)
                            if code in (401,403): raise PipelineError('PROVIDER_AUTH','analyze','Gemini authentication/permission failed.') from None
                            retryable=code in (429,500,502,503,504) or isinstance(exc,(TimeoutError,ConnectionError))
                            if not retryable or attempt==1:
                                raise PipelineError('PROVIDER_UNAVAILABLE','analyze','Gemini request failed; no provider fallback.',retryable) from None
                            self.sleep(2)
                    try:
                        parsed=GeminiResponse.model_validate_json(getattr(response,'text','') or '')
                        for topic in parsed.topics:
                            if not set(topic.evidence_word_ids).issubset(valid_ids): raise ValueError('unknown topic word IDs')
                        for candidate in parsed.candidates:
                            refs=[candidate.start_word_id,candidate.end_word_id,*candidate.evidence_word_ids,*candidate.context_before_word_ids,*candidate.context_after_word_ids]
                            if not set(refs).issubset(valid_ids): raise ValueError('unknown candidate word IDs')
                            if candidate.topic_id not in {t.id for t in parsed.topics}: raise ValueError('unknown topic ID')
                    except (ValueError,TypeError):
                        if repair: raise PipelineError('PROVIDER_INVALID_OUTPUT','analyze','Invalid structured JSON after one repair; analysis incomplete.') from None
                        repair=True;text+='\nA resposta anterior não respeitou o schema ou IDs. Retorne JSON válido usando somente os IDs da transcrição.'
                        continue
                    prefix=window['id']+':'
                    for topic in parsed.topics: topic.id=prefix+topic.id
                    for candidate in parsed.candidates: candidate.topic_id=prefix+candidate.topic_id
                    topics.extend(parsed.topics);candidates.extend(parsed.candidates);covered.update(valid_ids)
                    usage=getattr(response,'usage_metadata',None)
                    responses.append({'window_id':window['id'],'model_version':getattr(response,'model_version',None),'usage':usage.model_dump(mode='json') if hasattr(usage,'model_dump') else None})
                    break
            if covered!={w.id for w in transcript.words}:
                raise PipelineError('INCOMPLETE_ANALYSIS','analyze','Some transcript words were not covered.')
            return AnalysisArtifact(transcript_id=transcript.transcript_id,topics=topics,candidates=candidates,complete=True,covered_word_ids=sorted(covered),model=config.model,prompt_hash=object_hash(prompt),payload_hashes=hashes,responses=responses)
        finally:
            if client: client.close()
