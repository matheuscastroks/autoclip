import subprocess,re
from pathlib import Path
from fractions import Fraction
from engine.contracts import RenderArtifact,Source,EDLArtifact,ExportValidation,PipelineError
from engine.media.probe import probe_json
from engine.pipeline.artifacts import file_hash
from engine.pipeline.cancellation import run_process

def verify_render(render:RenderArtifact,source:Source,edl:EDLArtifact,ffprobe:Path,ffmpeg:Path,cancelled=lambda:False) -> ExportValidation:
    probe=probe_json(render.path,ffprobe,cancelled)
    v=next((s for s in probe['streams'] if s['codec_type']=='video'),{})
    a=next((s for s in probe['streams'] if s['codec_type']=='audio'),{})
    decoded=run_process([str(ffmpeg),'-nostdin','-v','error','-i',str(render.path),'-f','null','-'],cancelled=cancelled,capture_output=True,text=True,encoding='utf-8')
    levels=run_process([str(ffmpeg),'-nostdin','-v','info','-i',str(render.path),'-vn','-af','volumedetect','-f','null','-'],cancelled=cancelled,capture_output=True,text=True,encoding='utf-8')
    match=re.search(r'max_volume:\s*([-+\d.]+|[-+]?inf)\s*dB',levels.stderr or '')
    peak=float(match.group(1)) if match else float('-inf')
    duration=round(float(probe['format']['duration'])*1e6)
    checks={'hash':file_hash(render.path)==render.sha256,'size':render.path.stat().st_size==render.size_bytes,'decoded':decoded.returncode==0,'dimensions':v.get('width')==1080 and v.get('height')==1920,'video_codec':v.get('codec_name')=='h264','pixel_format':v.get('pix_fmt')=='yuv420p','audio':a.get('codec_name')=='aac' and a.get('sample_rate')=='48000','fps':Fraction(v.get('avg_frame_rate','0/1'))==30,'duration':abs(duration-edl.duration_us)<=33_355,'non_silent':levels.returncode==0 and peak>-80,'orientation':not any(s.get('rotation',0) for s in v.get('side_data_list',[])),'source_match':source.id==edl.source_id,'revision_match':render.revision_id==edl.revision_id}
    return ExportValidation(revision_id=edl.revision_id,technical_pass=all(checks.values()),checks=checks,warnings=['Editorial integrity requires human review; technical checks do not prove meaning.'])
