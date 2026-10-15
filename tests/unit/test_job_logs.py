from pathlib import Path

from engine.api.job_logs import IncrementalJobLogs


def test_unchanged_poll_does_not_reopen_log_and_append_keeps_stage(tmp_path, monkeypatch):
    path = tmp_path / 'stdout.log'
    path.write_bytes(b'Stage: transcribe\n' + b'fixture output\n' * 100_000)
    reader = IncrementalJobLogs()
    stage, lines = reader.read(path)
    assert stage == 'transcribe'
    assert len(lines) == 100
    original = Path.open

    def no_reread(*args, **kwargs):
        raise AssertionError('Unchanged log must not be opened again')

    monkeypatch.setattr(Path, 'open', no_reread)
    assert reader.read(path) == (stage, lines)
    monkeypatch.setattr(Path, 'open', original)
    with path.open('ab') as stream:
        stream.write(b'Stage: render\n')
    assert reader.read(path)[0] == 'render'
    assert reader.entries[path].offset == path.stat().st_size


def test_truncation_and_partial_utf8_lines_are_handled(tmp_path):
    path = tmp_path / 'stdout.log'
    path.write_bytes(b'Stage: transcribe\nlong old line\n')
    reader = IncrementalJobLogs()
    reader.read(path)
    path.write_bytes(b'Stage: render\n')
    assert reader.read(path) == ('render', ['Stage: render'])
    with path.open('ab') as stream:
        stream.write('Conclu'.encode())
    reader.read(path)
    with path.open('ab') as stream:
        stream.write('ído\n'.encode())
    assert reader.read(path)[1][-1] == 'Concluído'


def test_log_cache_and_line_memory_are_bounded(tmp_path):
    reader = IncrementalJobLogs(max_entries=2)
    for index in range(3):
        path = tmp_path / str(index)
        path.write_bytes(b'x' * 1_000_000)
        reader.read(path)
    assert len(reader.entries) == 2
    assert all(len(entry.pending) <= 4096 for entry in reader.entries.values())
