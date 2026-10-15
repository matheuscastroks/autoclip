"""Incrementally inspect worker logs without retaining or exposing full output."""
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LogSnapshot:
    identity: tuple
    offset: int = 0
    modified_ns: int = 0
    stage: str | None = None
    tail: deque = field(default_factory=lambda: deque(maxlen=100))
    pending: bytes = b''


class IncrementalJobLogs:
    def __init__(self, max_entries=128):
        self.entries = OrderedDict()
        self.max_entries = max_entries

    def read(self, path: Path):
        try:
            stat = path.stat()
            identity = (stat.st_dev, stat.st_ino)
            entry = self.entries.get(path)
            if entry is None or entry.identity != identity or stat.st_size < entry.offset or (stat.st_size == entry.offset and stat.st_mtime_ns != entry.modified_ns):
                entry = LogSnapshot(identity)
            if stat.st_size > entry.offset:
                with path.open('rb') as stream:
                    stream.seek(entry.offset)
                    while chunk := stream.read(64 * 1024):
                        entry.offset += len(chunk)
                        parts = (entry.pending + chunk).split(b'\n')
                        entry.pending = parts.pop()[-4096:]
                        for line in parts:
                            decoded = line[-4096:].decode('utf-8', errors='replace').rstrip('\r')
                            entry.tail.append(decoded)
                            if line.startswith(b'Stage: '):
                                entry.stage = decoded[7:]
            entry.modified_ns = stat.st_mtime_ns
            self.entries[path] = entry
            self.entries.move_to_end(path)
            while len(self.entries) > self.max_entries:
                self.entries.popitem(last=False)
            tail = list(entry.tail)
            if entry.pending:
                tail.append(entry.pending.decode('utf-8', errors='replace'))
            return entry.stage, tail[-100:]
        except OSError:
            return None, []
