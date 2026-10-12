"""Run the approved local ASR stage on the complete common test video."""
import sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from engine.media.importer import import_source
from engine.media.probe import probe_source,locate_tools
from engine.media.audio import extract_audio
from engine.adapters.openshorts.transcriber import OpenShortsTranscriber
from engine.contracts import ASRConfig
from engine.pipeline.artifacts import atomic_json,write_artifact

project=root/'poc-projects/jones-manoel'
ffmpeg,ffprobe=locate_tools()
started=time.perf_counter()
print('Importing the complete source and extracting CPU ASR audio.',flush=True)
source=probe_source(import_source(str(root/'research/media/z0cf-eWBVCo.mp4'),project),ffprobe)
atomic_json(project/'source.json',source)
audio=extract_audio(source,ffmpeg,project)
atomic_json(project/'audio.json',audio)
print(f'Transcribing {source.duration_us/1e6:.3f}s with multilingual small, CPU/int8.',flush=True)
t=OpenShortsTranscriber().transcribe(audio,ASRConfig(model_path=root/'research/models/whisper-small'))
ref=write_artifact(t,'transcript',project)
atomic_json(project/'transcript.json',t)
atomic_json(project/'asr-result.json',{'status':'completed','source_sha256':source.sha256,'words':len(t.words),'artifact':ref.model_dump(mode='json'),'wall_seconds':round(time.perf_counter()-started,3),'coverage':'complete source','semantic_analysis':'not run'})
print(f'Completed: {len(t.words)} words; {time.perf_counter()-started:.1f}s.',flush=True)
