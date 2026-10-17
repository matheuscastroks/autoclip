import pytest
from engine.contracts import TranscriptArtifact, Word, Segment, PipelineError
from engine.contracts.api import SegmentUpdate
from engine.editorial.transcript_editor import apply_transcript_updates

def make_sample_transcript():
    words = [
        Word(id='w0', text='Olá', start_us=0, end_us=500_000),
        Word(id='w1', text='mundo', start_us=500_000, end_us=1_000_000),
        Word(id='w2', text='como', start_us=1_200_000, end_us=1_500_000),
        Word(id='w3', text='vai', start_us=1_500_000, end_us=2_000_000),
    ]
    segments = [
        Segment(id='s0', text='Olá mundo', start_us=0, end_us=1_000_000, word_ids=['w0', 'w1']),
        Segment(id='s1', text='como vai', start_us=1_200_000, end_us=2_000_000, word_ids=['w2', 'w3']),
    ]
    return TranscriptArtifact(
        source_id='00000000-0000-0000-0000-000000000001',
        source_sha256='a' * 64,
        words=words,
        segments=segments,
    )

def test_edit_word_preserves_exact_timestamps():
    t = make_sample_transcript()
    updated = apply_transcript_updates(t, [SegmentUpdate(id='s0', text='Oi mundo')])
    assert updated.segments[0].text == 'Oi mundo'
    assert updated.words[0].text == 'Oi'
    assert updated.words[0].start_us == 0
    assert updated.words[0].end_us == 500_000
    assert updated.words[1].text == 'mundo'
    assert updated.words[1].start_us == 500_000
    assert updated.words[1].end_us == 1_000_000

def test_edit_segment_with_more_words_preserves_boundaries():
    t = make_sample_transcript()
    updated = apply_transcript_updates(t, [SegmentUpdate(id='s0', text='Olá meu caro mundo')])
    assert updated.segments[0].text == 'Olá meu caro mundo'
    assert updated.segments[0].start_us == 0
    assert updated.segments[0].end_us == 1_000_000
    s0_words = [w for w in updated.words if w.id in updated.segments[0].word_ids]
    assert len(s0_words) == 4
    assert [w.text for w in s0_words] == ['Olá', 'meu', 'caro', 'mundo']
    assert s0_words[0].start_us == 0
    assert s0_words[-1].end_us == 1_000_000
    assert all(b.start_us >= a.end_us for a, b in zip(s0_words, s0_words[1:]))
    assert all(w.end_us > w.start_us for w in s0_words)

def test_edit_segment_with_fewer_words_preserves_boundaries():
    t = make_sample_transcript()
    updated = apply_transcript_updates(t, [SegmentUpdate(id='s0', text='Mundo')])
    assert updated.segments[0].text == 'Mundo'
    assert updated.segments[0].start_us == 0
    assert updated.segments[0].end_us == 1_000_000
    s0_words = [w for w in updated.words if w.id in updated.segments[0].word_ids]
    assert len(s0_words) == 1
    assert s0_words[0].text == 'Mundo'
    assert s0_words[0].start_us == 0
    assert s0_words[0].end_us == 1_000_000

def test_edit_nonexistent_segment_raises_error():
    t = make_sample_transcript()
    with pytest.raises(PipelineError) as exc:
        apply_transcript_updates(t, [SegmentUpdate(id='s999', text='Inexistente')])
    assert exc.value.code == 'SEGMENT_NOT_FOUND'
