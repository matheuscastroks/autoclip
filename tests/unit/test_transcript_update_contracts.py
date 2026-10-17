import pytest
from pydantic import ValidationError
from engine.contracts.api import SegmentUpdate, UpdateTranscriptInput

def test_segment_update_valid():
    up = SegmentUpdate(id='s1', text='Texto corrigido')
    assert up.id == 's1'
    assert up.text == 'Texto corrigido'

def test_segment_update_invalid():
    with pytest.raises(ValidationError):
        SegmentUpdate(id='', text='Texto')

def test_update_transcript_input():
    payload = UpdateTranscriptInput(segments=[SegmentUpdate(id='s1', text='Texto')])
    assert len(payload.segments) == 1
    assert payload.segments[0].id == 's1'
