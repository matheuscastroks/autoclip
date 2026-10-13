from uuid import uuid4
from types import SimpleNamespace
import json
import pytest
from engine.contracts import TranscriptArtifact, Word, Segment, AnalysisConfig, PipelineError

def make_transcript():
    ws = [Word(id=f'w{i}', text=('Não' if i == 0 else 'ressalva.' if i == 29 else 'palavra'), start_us=i * 1_000_000, end_us=i * 1_000_000 + 900_000) for i in range(30)]
    return TranscriptArtifact(source_sha256='a'*64, words=ws, segments=[Segment(id='s1', word_ids=[w.id for w in ws], text='Não ... ressalva.', start_us=0, end_us=29_900_000)])

def make_payload():
    return {
        'topics': [{'id': 'topic1', 'label': 'Tema de Teste', 'summary': 'Resumo do tema', 'evidence_word_ids': ['w0', 'w29']}],
        'candidates': [{
            'topic_id': 'topic1',
            'start_word_id': 'w0',
            'end_word_id': 'w29',
            'evidence_word_ids': ['w0', 'w29'],
            'rationale': 'Pensamento completo',
            'editorial': {'completeness': 'yes', 'standalone_context': 'yes', 'qualification_preserved': 'yes'},
            'title_suggestion': 'Título do Corte',
            'opening_suggestion': 'Abertura do Corte?',
            'description_suggestion': 'Descrição para redes sociais.'
        }]
    }

def test_openrouter_analyzer_success():
    from engine.adapters.openrouter.analyzer import OpenRouterAnalyzer
    
    captured = []
    def request(**kw):
        captured.append(kw)
        return SimpleNamespace(
            text=json.dumps(make_payload()),
            model_version='meta-llama/llama-3.3-70b-instruct:free',
            usage_metadata=None
        )
        
    t = make_transcript()
    analyzer = OpenRouterAnalyzer(request=request, sleep=lambda _: None)
    result = analyzer.analyze(t, AnalysisConfig(model='openrouter/free', max_calls=3))
    
    assert result.complete
    assert len(result.topics) == 1
    assert len(result.candidates) == 1
    assert result.candidates[0].title_suggestion == 'Título do Corte'
    assert 'contents' in captured[0]

def test_openrouter_analyzer_offline_mode():
    from engine.adapters.openrouter.analyzer import OpenRouterAnalyzer
    analyzer = OpenRouterAnalyzer(request=lambda **kw: pytest.fail('network called'))
    with pytest.raises(PipelineError) as exc:
        analyzer.analyze(make_transcript(), AnalysisConfig(model='openrouter/free', max_calls=1, offline=True))
    assert exc.value.code == 'OFFLINE_PROVIDER'

def test_openrouter_analyzer_invalid_word_ids_rejected():
    from engine.adapters.openrouter.analyzer import OpenRouterAnalyzer
    
    bad_payload = make_payload()
    bad_payload['candidates'][0]['start_word_id'] = 'w_nonexistent'
    
    def request(**kw):
        return SimpleNamespace(
            text=json.dumps(bad_payload),
            model_version='test-model',
            usage_metadata=None
        )
        
    analyzer = OpenRouterAnalyzer(request=request, sleep=lambda _: None)
    with pytest.raises(PipelineError) as exc:
        analyzer.analyze(make_transcript(), AnalysisConfig(model='openrouter/free', max_calls=2))
    assert exc.value.code == 'PROVIDER_INVALID_OUTPUT'
