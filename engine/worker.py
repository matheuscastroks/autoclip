"""Heavy ASR subprocess boundary, no UI or network providers."""
import argparse
from pathlib import Path
from engine.contracts import AudioArtifact,ASRConfig
from engine.adapters.openshorts.transcriber import OpenShortsTranscriber
from engine.pipeline.artifacts import atomic_json

def run_worker(audio: Path, config: Path, output: Path):
    audio_art=AudioArtifact.model_validate_json(Path(audio).read_bytes())
    config_art=ASRConfig.model_validate_json(Path(config).read_bytes())
    atomic_json(Path(output),OpenShortsTranscriber().transcribe(audio_art,config_art))

def main():
    p=argparse.ArgumentParser();p.add_argument('audio');p.add_argument('config');p.add_argument('output');a=p.parse_args()
    run_worker(Path(a.audio),Path(a.config),Path(a.output))

if __name__=='__main__': main()
