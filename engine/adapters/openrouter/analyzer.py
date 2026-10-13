import json, time, sys, tempfile
from uuid import uuid5, NAMESPACE_URL
import httpx
from types import SimpleNamespace
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from engine.contracts import TranscriptArtifact, AnalysisConfig, AnalysisArtifact, Topic, Candidate, PipelineError
from engine.pipeline.artifacts import object_hash, atomic_json, file_hash
from engine.pipeline.cancellation import run_process
from engine.adapters.openshorts.windows import build_windows
from engine.pipeline.analysis_events import EventWriter
from engine.adapters.gemini.analyzer import GeminiResponse
from .credentials import get_openrouter_key

def retry_delay(error):
    raw = getattr(getattr(error, 'response', None), 'headers', {}).get('Retry-After')
    if raw is None:
        raw = getattr(error, 'retry_after', None)
    if raw is None:
        return 2
    try:
        return max(0, min(30, float(raw)))
    except (ValueError, TypeError):
        try:
            return max(0, min(30, (parsedate_to_datetime(raw) - datetime.now(timezone.utc)).total_seconds()))
        except (ValueError, TypeError):
            return 2

class WorkerRequestError(Exception):
    def __init__(self, data):
        self.code = data.get('code')
        self.transport = data.get('transport', False)
        self.timeout = data.get('type') in ('TimeoutError', 'ReadTimeout', 'ConnectTimeout', 'ProcessTimeout')
        self.retry_after = data.get('retry_after')
        self.response = SimpleNamespace(headers={'Retry-After': data['retry_after']} if data.get('retry_after') else {})
        super().__init__(data.get('message', 'Isolated OpenRouter request failed.'))

def isolated_request(root, cancelled, timeout, **kwargs):
    from engine.pipeline.provider_lock import provider_slot
    writer = EventWriter(kwargs.get('events_path'))
    context = kwargs.get('context', {})
    with provider_slot(Path.cwd(), cancelled, on_wait=lambda: writer.emit('provider_waiting', 'Aguardando a vez na fila de chamadas à IA.', **context)):
        writer.emit('request_dispatched', 'Vez liberada; iniciando a solicitação ao OpenRouter.', **context)
        return _isolated_request(root, cancelled, timeout, **kwargs)

def _isolated_request(root, cancelled, timeout, **kwargs):
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='openrouter-', dir=root) as folder:
        folder = Path(folder)
        request = folder / 'request.json'
        response = folder / 'response.json'
        atomic_json(request, {
            'model': kwargs['model'],
            'contents': kwargs['contents'],
            'timeout_s': timeout,
            'events_path': str(kwargs['events_path']) if kwargs.get('events_path') else None,
            'context': kwargs.get('context', {})
        })
        from engine.system.subprocesses import engine_cmd
        cmd = engine_cmd('openrouter-worker', str(request), str(response), module='engine.adapters.openrouter.request_worker')
        try:
            run_process(cmd, cancelled=cancelled, timeout_s=timeout+10, capture_output=True, text=True, encoding='utf-8')
        except PipelineError as exc:
            if exc.code == 'PROCESS_TIMEOUT':
                raise WorkerRequestError({'transport': True, 'type': 'ProcessTimeout'}) from None
            raise
        if not response.exists():
            raise WorkerRequestError({'transport': True})
        data = json.loads(response.read_text(encoding='utf-8'))
        if 'error' in data:
            atomic_json(root / 'last-openrouter-error.json', data['error'])
            raise WorkerRequestError(data['error'])
        usage = data.get('usage')
        return SimpleNamespace(text=data['text'], model_version=data.get('model_version'), usage_metadata=SimpleNamespace(model_dump=lambda **kw: usage) if usage else None)

class OpenRouterAnalyzer:
    def __init__(self, request=None, sleep=time.sleep, work_root=None, budget=None, events_path=None):
        self.request = request
        self.sleep = sleep
        self.work_root = Path(work_root) if work_root else Path.cwd() / '.runtime-tmp'
        self.budget = budget
        self.events_path = Path(events_path) if events_path else None
        self.checkpoint_root = Path(work_root) / 'analysis-checkpoints' if work_root is not None else None
        self.context = {}

    def publish_cached(self, analysis):
        if self.events_path:
            atomic_json(self.events_path.parent / 'analysis-preview.json', {
                'analysis': analysis.model_dump(mode='json'),
                'completed_windows': len(analysis.responses),
                'total_windows': len(analysis.responses)
            })
        EventWriter(self.events_path).emit('analysis_cache_reused', 'Análise existente reaproveitada. Não houve nova chamada ao OpenRouter.', model=analysis.model, topics=[t.model_dump(mode='json') for t in analysis.topics], candidates=[c.model_dump(mode='json') for c in analysis.candidates])

    def analyze(self, transcript: TranscriptArtifact, config: AnalysisConfig, cancelled=lambda: False) -> AnalysisArtifact:
        from engine.adapters.gemini.checkpoints import load_checkpoint, save_checkpoint
        if config.offline:
            raise PipelineError('OFFLINE_PROVIDER', 'analyze', 'OpenRouter requires internet; local stages and review remain available.')
        if not transcript.words:
            raise PipelineError('NO_SPEECH', 'analyze', 'No transcript; never upload silent video.')
            
        request = self.request
        secret = ''
        if request is None:
            secret = get_openrouter_key()
            request = lambda **kw: isolated_request(self.work_root, cancelled, config.timeout_s, events_path=self.events_path, context=self.context, **kw)
        writer = EventWriter(self.events_path, secret)
        
        def check_cancelled():
            if cancelled():
                raise PipelineError('CANCELLED', 'analyze', 'Cancelled; no further OpenRouter requests.')
                
        def validate(parsed, window):
            valid_ids = {w.id for w in window['words']}
            order = {w.id: i for i, w in enumerate(window['words'])}
            for topic in parsed.topics:
                if not set(topic.evidence_word_ids).issubset(valid_ids):
                    raise ValueError('unknown topic word IDs')
            for candidate in parsed.candidates:
                refs = [candidate.start_word_id, candidate.end_word_id, *candidate.evidence_word_ids, *candidate.context_before_word_ids, *candidate.context_after_word_ids]
                if not set(refs).issubset(valid_ids):
                    raise ValueError('unknown candidate word IDs')
                if candidate.topic_id not in {t.id for t in parsed.topics}:
                    raise ValueError('unknown topic ID')
                if order[candidate.start_word_id] > order[candidate.end_word_id]:
                    raise ValueError('reversed boundaries')
            return parsed
            
        prompt = (Path(__file__).resolve().parents[2] / 'prompts/analysis_v1.txt').read_text(encoding='utf-8')
        prompt = prompt.replace('{MIN_SECONDS}', str(config.clip_min_seconds)).replace('{MAX_SECONDS}', str(config.clip_max_seconds)).replace('{PREFERRED_SECONDS}', str(config.clip_preferred_seconds))
        prompt += '\nNão encerre um argumento no meio. Se a conclusão exigir mais que o máximo, não proponha esse corte. Resumos de análise devem estar em português brasileiro.'
        global_text = ' '.join(w.text for w in transcript.words)
        prompt += '\n<CONTEXTO_GLOBAL>\n' + global_text + '\n</CONTEXTO_GLOBAL>'
        
        topics = []; candidates = []; covered = set(); hashes = []; responses = []; calls = 0
        windows = build_windows(transcript, max(config.window_seconds, config.clip_max_seconds * 2) if config.clip_min_seconds >= 60 else config.window_seconds, config.max_text_chars, overlap_seconds=config.clip_max_seconds if config.clip_min_seconds >= 60 else 30)
        
        runtime = {'analyzer': file_hash(Path(__file__)), 'worker': file_hash(Path(__file__).with_name('request_worker.py')), 'schema': GeminiResponse.model_json_schema(), 'policy': 2}
        identity = {'transcript': object_hash(transcript), 'model': config.model, 'prompt': object_hash(prompt), 'provider': 'openrouter'}
        
        planned = []
        for window in windows:
            text = prompt + '\n<TRANSCRICAO>\n' + window['text'] + '\n</TRANSCRICAO>'
            key = object_hash({**identity, 'window_id': window['id'], 'word_ids': [w.id for w in window['words']], 'text': text})
            cached = load_checkpoint(self.checkpoint_root, key)
            if cached:
                try:
                    validate(GeminiResponse.model_validate(cached['response']), window)
                    if cached['provenance']['window_id'] != window['id']:
                        raise ValueError('invalid window_id')
                except (ValueError, TypeError, KeyError):
                    cached = None
            planned.append((window, text, key, cached))
            
        missing = sum(cached is None for _, _, _, cached in planned)
        writer.emit('analysis_started', 'Analisando com OpenRouter e retomada de janelas validadas.', model=config.model, windows=len(windows), completed_windows=len(windows) - missing, remaining_windows=missing, request_limit=config.max_calls)
        
        if missing > min(config.max_calls, self.budget.remaining if self.budget else config.max_calls):
            raise PipelineError('PROVIDER_BUDGET', 'analyze', 'Request budget cannot cover remaining windows; no request made.')
            
        for index, (window, text, key, cached) in enumerate(planned, 1):
            check_cancelled(); window_hashes = []
            context = {'window_id': window['id'], 'window_index': index, 'windows': len(windows)}
            writer.emit('window_started', f'Janela {index} de {len(windows)}.', **context, source_start_us=window['words'][0].start_us, source_end_us=max(w.end_us for w in window['words']))
            
            if cached:
                parsed = validate(GeminiResponse.model_validate(cached['response']), window)
                provenance = cached['provenance']
                hashes.extend(cached['payload_hashes'])
                self.context = {**context, 'attempt': 0, 'model': config.model}
                writer.emit('window_reused', 'Janela já validada reaproveitada. Nenhuma nova chamada ao OpenRouter.', **self.context, checkpoint_key=key)
            else:
                repair = False
                while True:
                    response = None
                    for attempt in range(2):
                        check_cancelled()
                        if calls >= config.max_calls:
                            raise PipelineError('PROVIDER_BUDGET', 'analyze', 'OpenRouter request budget exhausted; analysis not complete.')
                        payload_hash = object_hash({'model': config.model, 'contents': text, 'prompt_version': config.prompt_version, 'runtime': runtime})
                        if self.budget:
                            self.budget.reserve(payload_hash)
                        calls += 1; hashes.append(payload_hash); window_hashes.append(payload_hash)
                        self.context = {**context, 'attempt': calls, 'model': config.model}
                        writer.emit('request_started', 'Solicitação enviada; aguardando resposta do OpenRouter.', **self.context)
                        try:
                            response = request(model=config.model, contents=text)
                            break
                        except Exception as exc:
                            timeout = isinstance(exc, (TimeoutError, httpx.TimeoutException)) or getattr(exc, 'timeout', False)
                            writer.emit('request_failed', 'Tempo de resposta excedido.' if timeout else 'Solicitação não concluída.', **self.context, error_code='PROVIDER_TIMEOUT' if timeout else 'PROVIDER_UNAVAILABLE')
                            code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
                            if code == 'PROVIDER_RATE_LIMIT' or code == 429:
                                writer.emit('provider_rate_limited', 'O OpenRouter atingiu o limite de taxa. Aguarde antes de continuar.', **self.context, error_code='PROVIDER_RATE_LIMIT')
                                raise PipelineError('PROVIDER_RATE_LIMIT', 'analyze', 'OpenRouter rate limit reached; validated windows remain available.') from None
                            if code == 'PROVIDER_AUTH' or code in (401, 403):
                                raise PipelineError('PROVIDER_AUTH', 'analyze', 'OpenRouter authentication failed.') from None
                            transport_types = (TimeoutError, ConnectionError, httpx.TimeoutException, httpx.NetworkError)
                            retryable = code in (429, 500, 502, 503, 504) or isinstance(exc, transport_types) or getattr(exc, 'transport', False)
                            if not retryable or attempt == 1:
                                raise PipelineError('PROVIDER_TIMEOUT' if timeout else 'PROVIDER_UNAVAILABLE', 'analyze', 'OpenRouter request failed; validated windows remain available.', retryable) from None
                            writer.emit('request_retry', 'Repetindo após falha recuperável.', **self.context)
                            delay = retry_delay(exc)
                            while delay > 0:
                                check_cancelled(); step = min(.2, delay); self.sleep(step); delay -= step
                                
                    try:
                        raw_json_str = getattr(response, 'text', '') or ''
                        parsed = validate(GeminiResponse.model_validate_json(raw_json_str), window)
                    except (ValueError, TypeError):
                        writer.emit('response_rejected', 'Resposta descartada: JSON ou referências inválidas.', **self.context)
                        if repair:
                            raise PipelineError('PROVIDER_INVALID_OUTPUT', 'analyze', 'Invalid structured JSON from OpenRouter after repair.') from None
                        repair = True
                        text += '\nA resposta anterior não respeitou o schema ou IDs. Retorne apenas JSON válido usando os IDs da transcrição.'
                        continue
                        
                    usage = getattr(response, 'usage_metadata', None)
                    provenance = {
                        'window_id': window['id'],
                        'model_version': getattr(response, 'model_version', None),
                        'usage': usage.model_dump(mode='json') if hasattr(usage, 'model_dump') else None
                    }
                    save_checkpoint(self.checkpoint_root, key, parsed, provenance, window_hashes)
                    break
                    
            prefix = window['id'] + ':'
            domain_topics = [Topic.model_validate(t.model_dump()) for t in parsed.topics]
            domain_candidates = [Candidate.model_validate(c.model_dump()) for c in parsed.candidates]
            for topic in domain_topics:
                topic.id = prefix + topic.id
            for ordinal, candidate in enumerate(domain_candidates):
                candidate.topic_id = prefix + candidate.topic_id
                candidate.id = uuid5(NAMESPACE_URL, 'autoclip:' + key + ':' + str(ordinal))
                
            topics.extend(domain_topics)
            candidates.extend(domain_candidates)
            covered.update(w.id for w in window['words'])
            responses.append(provenance)
            
            if self.events_path:
                preview = AnalysisArtifact(
                    transcript_id=transcript.transcript_id,
                    topics=topics,
                    candidates=candidates,
                    clip_min_seconds=config.clip_min_seconds,
                    complete=False,
                    covered_word_ids=sorted(covered),
                    model=config.model,
                    prompt_hash=object_hash(prompt),
                    payload_hashes=hashes,
                    responses=responses
                )
                snapshot = {'analysis': preview.model_dump(mode='json'), 'completed_windows': index, 'total_windows': len(windows)}
                atomic_json(self.events_path.parent / 'analysis-preview.json', snapshot)
                if self.checkpoint_root is not None:
                    atomic_json(self.work_root / 'analysis-preview.json', snapshot)
            writer.emit('window_validated', 'Janela validada com OpenRouter.', **self.context)
            
        if covered != {w.id for w in transcript.words}:
            raise PipelineError('INCOMPLETE_ANALYSIS', 'analyze', 'Some transcript words were not covered.')
            
        from engine.editorial.select import select_candidates
        from engine.contracts import SelectionConfig
        topic_labels = {t.id: ' '.join(t.label.casefold().split()) for t in topics}
        distinct = []; seen_topics = set()
        full = AnalysisArtifact(transcript_id=transcript.transcript_id, topics=topics, candidates=candidates, clip_min_seconds=config.clip_min_seconds, complete=True, covered_word_ids=sorted(covered), model=config.model, prompt_hash=object_hash(prompt), payload_hashes=hashes, responses=responses)
        valid = select_candidates(full, transcript, SelectionConfig(min_us=config.clip_min_seconds * 1_000_000, max_us=config.clip_max_seconds * 1_000_000, max_clips=10)).candidates
        for candidate in valid:
            label = topic_labels.get(candidate.topic_id, candidate.topic_id)
            if label in seen_topics:
                continue
            seen_topics.add(label)
            distinct.append(candidate)
        candidates = distinct
        
        writer.emit('analysis_completed', 'Todas as janelas foram analisadas e validadas via OpenRouter.', requests_used=calls, reused_windows=len(windows) - missing, topics_count=len(topics), candidates_count=len(candidates))
        return AnalysisArtifact(transcript_id=transcript.transcript_id, topics=topics, candidates=candidates, clip_min_seconds=config.clip_min_seconds, complete=True, covered_word_ids=sorted(covered), model=config.model, prompt_hash=object_hash(prompt), payload_hashes=hashes, responses=responses)
