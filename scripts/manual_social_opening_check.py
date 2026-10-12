"""Short local technical render. Does not analyze, transcribe or approve a cut."""
import sys,json,subprocess
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.contracts import *
from engine.pipeline.artifacts import file_hash,atomic_json
from engine.media.probe import locate_tools,probe_source
from engine.render.ffmpeg import FFmpegRenderer
from engine.render.verify import verify_render
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
from engine.pipeline.fingerprints import resolve_font
proof=json.loads(Path('poc-results/frontend/real-center-crop-validation.json').read_text());project=Path(proof['render']['path']).parents[2]
source=Source.model_validate_json((project/'source.json').read_bytes());original=TranscriptArtifact.model_validate_json((project/'transcript.json').read_bytes())
edl0=EDLArtifact.model_validate_json((project/'revisions'/proof['render']['revision_id']/'edl.json').read_bytes())
start=edl0.spans[0].source_start_us;duration=8_000_000
root=Path('poc-results/media/social-opening-demo');root.mkdir(parents=True,exist_ok=True);ffmpeg,ffprobe=locate_tools();media=root/'source.mp4'
subprocess.run([str(ffmpeg),'-v','error','-y','-ss',f'{start/1e6:.6f}','-i',str(source.local_path),'-t','8','-c:v','libx264','-threads','2','-c:a','aac',str(media)],check=True)
local=probe_source(Source(local_path=media.resolve(),sha256=file_hash(media),duration_us=duration),ffprobe)
words=[w.model_copy(update={'start_us':w.start_us-start,'end_us':w.end_us-start}) for w in original.words if start<=w.start_us and w.end_us<=start+duration]
t=TranscriptArtifact(source_id=local.id,source_sha256=local.sha256,words=words)
edl=EDLArtifact(source_id=local.id,transcript_id=t.transcript_id,spans=[Span(source_start_us=0,source_end_us=duration,output_start_us=0,output_end_us=duration)],duration_us=duration,protected_word_ids=[w.id for w in words])
config=CaptionConfig(opening_text='Toda corrupção é igual?',font_path=resolve_font(None,'Montserrat ExtraBold'))
caps=OpenShortsCaptionBuilder(root/'captions').build(t,edl,CaptionRevision(),config)
render=FFmpegRenderer(ffmpeg).render(local,edl,CropArtifact(source_id=local.id,edl_revision_id=edl.revision_id),caps,ExportConfig(output_root=root/'renders'))
qa=verify_render(render,local,edl,ffprobe,ffmpeg);assert qa.technical_pass
for seconds,name in [(1,'social-opening-visible.jpg'),(7.5,'social-opening-finished.jpg')]:
 subprocess.run([str(ffmpeg),'-v','error','-y','-ss',str(seconds),'-i',str(render.path),'-frames:v','1',str(Path('poc-results/frontend')/name)],check=True)
atomic_json(Path('poc-results/frontend/social-opening-validation.json'),{'purpose':'8-second technical presentation sample; headline chosen manually for style validation, no full-cut editorial approval','render':render,'qa':qa,'opening_text':caps.opening_text,'opening_duration_us':caps.opening_duration_us,'gemini_calls':0})
print({'technical_pass':qa.technical_pass,'opening_duration_us':caps.opening_duration_us,'duration_us':duration})
