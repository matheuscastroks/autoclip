"""Transparent iterator observation; upstream transcription behavior is unchanged."""
from engine.pipeline.telemetry import observe


def progress_model(model, duration_us):
    class ObservedModel:
        def transcribe(self, *args, **kwargs):
            observe('transcribe', 0, duration_us, 'media_us')
            segments, info = model.transcribe(*args, **kwargs)

            def observed():
                for segment in segments:
                    observe('transcribe', round(segment.end * 1_000_000), duration_us, 'media_us')
                    yield segment

            return observed(), info

    return ObservedModel()
