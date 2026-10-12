import pytest


def test_contracts_reject_invalid_temporal_bounds_and_major():
    from engine.contracts import Word, TranscriptArtifact
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Word(id='w1', text='Não', start_us=10, end_us=10)
    with pytest.raises(ValidationError):
        Word(id='w1', text='Não', start_us=-1, end_us=10)
    with pytest.raises(ValidationError):
        TranscriptArtifact(schema_version='2.0', source_sha256='a' * 64, words=[])
    with pytest.raises(ValidationError):
        TranscriptArtifact(source_sha256='broken', words=[])
    assert Word(id='w1', text='Não', start_us=0, end_us=10).probability is None


def test_overlap_is_warned_without_changing_timestamps():
    from engine.contracts import TranscriptArtifact, Word
    t = TranscriptArtifact(source_sha256='a'*64, words=[
        Word(id='w1', text='a', start_us=0, end_us=100),
        Word(id='w2', text='b', start_us=50, end_us=120)])
    assert 'overlapping_words' in t.warnings
    assert t.words[1].start_us == 50


def test_engine_imports_without_cloud_or_heavy_platform():
    import subprocess, sys
    r = subprocess.run([sys.executable, '-c',
        "import engine; import engine.contracts; import sys; assert not {'cloud','main','app','torch','ultralytics','remotion'} & set(sys.modules)"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
