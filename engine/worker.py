"""Heavy ASR subprocess boundary, no UI or network providers."""
import argparse
from pathlib import Path
from engine.contracts import AudioArtifact,ASRConfig
from engine.adapters.openshorts.transcriber import OpenShortsTranscriber
from engine.pipeline.artifacts import atomic_json

def main():
    p=argparse.ArgumentParser();p.add_argument('audio');p.add_argument('config');p.add_argument('output');a=p.parse_args()
    audio=AudioArtifact.model_validate_json(Path(a.audio).read_bytes())
    config=ASRConfig.model_validate_json(Path(a.config).read_bytes())
    atomic_json(Path(a.output),OpenShortsTranscriber().transcribe(audio,config))

if __name__=='__main__': main()
