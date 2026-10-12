"""Validate the local real-speech caption demo without provider calls."""
import sys,json,subprocess
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.contracts import *
from engine.media.probe import locate_tools,probe_source
from engine.pipeline.artifacts import file_hash,atomic_json
from engine.media.face_tracking import track_faces
from engine.render.ffmpeg import FFmpegRenderer
from engine.render.verify import verify_render

root=Path('poc-results/media/bold-caption-demo')
proof=json.loads(Path('poc-results/frontend/bold-caption-style-validation.json').read_text())
ffmpeg,ffprobe=locate_tools()
source=probe_source(Source(sha256=file_hash(root/'clean-source.mp4'),local_path=(root/'clean-source.mp4').resolve(),duration_us=proof['duration_us']),ffprobe)
edl=EDLArtifact(source_id=source.id,transcript_id=uuid4(),duration_us=proof['duration_us'],spans=[Span(source_start_us=0,source_end_us=proof['duration_us'],output_start_us=0,output_end_us=proof['duration_us'])],protected_word_ids=[])
base=next((root/'captions').rglob('*.ass'))
caps=CaptionArtifact(transcript_id=edl.transcript_id,edl_revision_id=edl.revision_id,revision_id=uuid4(),words=[],ass_path=base.resolve(),srt_path=base.with_suffix('.srt').resolve(),font=str(Path('engine/assets/fonts/Montserrat-ExtraBold.ttf').resolve()))
crop=track_faces(source,edl,ReframeConfig(),ffmpeg)
assert crop.mode=='face-track',crop.fallback_reason
render=FFmpegRenderer(ffmpeg).render(source,edl,crop,caps,ExportConfig(output_root=root/'face-tracked'))
qa=verify_render(render,source,edl,ffprobe,ffmpeg);assert qa.technical_pass
frame=Path('poc-results/frontend/face-tracking-frame.jpg').resolve()
subprocess.run([str(ffmpeg),'-v','error','-y','-ss','0.25','-i',str(render.path),'-frames:v','1',str(frame)],check=True)
atomic_json(Path('poc-results/frontend/face-tracking-validation.json'),{'crop':crop,'render':render,'qa':qa,'gemini_calls':0,'purpose':'Short real speech sample; not a complete editorial cut'})
print({'mode':crop.mode,'detected':crop.detected_samples,'samples':crop.total_samples,'x_range':[min(p.center_x for p in crop.points),max(p.center_x for p in crop.points)],'technical_pass':qa.technical_pass})
