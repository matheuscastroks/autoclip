"""Canonical PCM WAV progress when FFmpeg -copyts reports zero output time."""
import struct
from engine.pipeline.progress import RenderProgress


class WavProgress(RenderProgress):
    def __init__(self, path, total_us, callback):
        super().__init__(total_us, callback)
        self.path = path
        self.data_offset = None

    def line(self, line):
        key, _, value = line.strip().partition('=')
        if key != 'total_size':
            return super().line(line)
        try:
            size = int(value)
            if self.data_offset is None:
                with self.path.open('rb') as stream:
                    header = stream.read(12)
                    if header[:4] not in (b'RIFF', b'RF64') or header[8:] != b'WAVE':
                        return
                    while stream.tell() < 65536:
                        chunk = stream.read(8)
                        if len(chunk) != 8:
                            return
                        name, length = struct.unpack('<4sI', chunk)
                        if name == b'data':
                            self.data_offset = stream.tell()
                            break
                        stream.seek(length + length % 2, 1)
            if self.data_offset is not None:
                # extract_audio always writes mono, PCM16 at exactly 16 kHz.
                measured = max(0, size - self.data_offset) * 1_000_000 // 32000
                self.processed_us = max(self.processed_us, min(self.total_us, measured))
                self.callback(self.processed_us, self.total_us)
        except (OSError, ValueError, struct.error):
            pass
