"""Measured copies publish only after completion and preserve existing artifacts."""
from pathlib import Path
from uuid import uuid4
from engine.contracts import PipelineError
from engine.pipeline.telemetry import observe


def copy_observed(source, target, *, cancelled=lambda: False):
    source, target = Path(source), Path(target)
    temp = target.with_name(uuid4().hex + '.partial')
    total, done = source.stat().st_size, 0
    try:
        if cancelled():
            raise PipelineError('CANCELLED', 'export', 'Cancelled; previous packages preserved.')
        with source.open('rb') as reader, temp.open('xb') as writer:
            while chunk := reader.read(1024 * 1024):
                if cancelled():
                    raise PipelineError('CANCELLED', 'export', 'Cancelled; previous packages preserved.')
                writer.write(chunk)
                done += len(chunk)
                observe('copy', done, total, 'bytes')
        if cancelled():
            raise PipelineError('CANCELLED', 'export', 'Cancelled; previous packages preserved.')
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
