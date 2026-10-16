"""CPU face detector and a deterministic output-time crop path. No network IO."""
import math,tempfile
from pathlib import Path
from engine.contracts import CropArtifact,CropPoint,PipelineError
from engine.pipeline.artifacts import file_hash
from engine.pipeline.cancellation import run_process

def model_path(config):
    return config.model_path or Path(__file__).resolve().parents[1]/'assets/models/blaze_face_short_range.tflite'

def choose_face(faces,previous):
    # Largest confident face initially; spatial continuity afterwards (not identity recognition).
    if not faces:return None
    if previous is None:return max(faces,key=lambda f:f[1]*f[2])[0]
    nearest=min(faces,key=lambda f:abs(f[0]-previous))
    return nearest[0] if abs(nearest[0]-previous)<=.25 else None

def smooth_track(samples,hold_us=1_000_000):
    position=.5;last_seen=None;last_t=None;points=[]
    for t,target in samples:
        if target is not None:last_seen=t
        elif last_seen is not None and t-last_seen<=hold_us:target=position
        else:target=.5
        target=max(0.,min(1.,target))
        if last_t is None:position=target
        elif abs(target-position)>.02:
            dt=(t-last_t)/1e6
            delta=(target-position)*(1-math.exp(-dt/.65))
            position+=max(-.18*dt,min(.18*dt,delta))
        points.append(CropPoint(output_us=t,center_x=position));last_t=t
    return points

def simplify_crop_points(points,max_segments=60,epsilon=0.005):
    if len(points)<=2:return points
    t0=points[0].output_us;t_total=points[-1].output_us-t0 or 1
    def rdp(pts,eps):
        if len(pts)<=2:return pts
        p1,p2=pts[0],pts[-1]
        x1,y1=(p1.output_us-t0)/t_total,p1.center_x
        x2,y2=(p2.output_us-t0)/t_total,p2.center_x
        dx,dy=x2-x1,y2-y1;mag=math.hypot(dx,dy)
        max_dist,index=-1.0,-1
        for i in range(1,len(pts)-1):
            p=pts[i];px,py=(p.output_us-t0)/t_total,p.center_x
            dist=abs(py-y1) if mag==0 else abs(dy*px-dx*py+x2*y1-y2*x1)/mag
            if dist>max_dist:max_dist,index=dist,i
        if max_dist>eps:return rdp(pts[:index+1],eps)[:-1]+rdp(pts[index:],eps)
        return [p1,p2]
    curr_eps=epsilon;res=rdp(points,curr_eps)
    while len(res)-1>max_segments:
        curr_eps*=1.5;res=rdp(points,curr_eps)
    return res

def crop_expression(points, width=1080):
    # Piecewise linear interpolation, clamped to frame edges. Capped to safe FFmpeg evaluator limit (~60 terms).
    if not points:return f'max(0,min(iw-{width},(iw-{width})/2))'
    if len(points)>60:points=simplify_crop_points(points,max_segments=60)
    value=f'{points[0].center_x:.8f}'
    for a,b in zip(points,points[1:]):
        dt=(b.output_us-a.output_us)/1e6
        slope=(b.center_x-a.center_x)/dt
        if abs(slope)>1e-8:value+=f'+({slope:.8f})*clip(t-{a.output_us/1e6:.6f},0,{dt:.6f})'
    return f'max(0,min(iw-{width},iw*({value})-{width // 2}))'

def track_faces(source,edl,config,ffmpeg,*,cancelled=lambda:False,progress=None,detector_factory=None):
    path=model_path(config)
    def fallback(reason):return CropArtifact(source_id=source.id,edl_revision_id=edl.revision_id,fallback_reason=reason)
    if not config.enabled:return fallback('Face tracking disabled in configuration.')
    if not path.is_file():return fallback('Face detector model unavailable; using central crop.')
    try:
        import mediapipe as mp
        options=mp.tasks.vision.FaceDetectorOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(path),delegate=mp.tasks.BaseOptions.Delegate.CPU),running_mode=mp.tasks.vision.RunningMode.VIDEO,min_detection_confidence=config.min_confidence)
        context=(detector_factory or mp.tasks.vision.FaceDetector.create_from_options)(options)
    except (ImportError,OSError,RuntimeError):return fallback('MediaPipe unavailable; using central crop.')
    samples=[];previous=None;last_seen=None;detected=0;detector_ms=-1
    container_origin=float(source.probe.get('raw',{}).get('format',{}).get('start_time',0))
    seek_offset=source.probe.get('video_origin_us',0)/1e6-container_origin
    with context as detector:
        with tempfile.TemporaryDirectory(prefix='autoclip-faces-') as folder:
            root=Path(folder)
            for index,span in enumerate(edl.spans):
                if cancelled():raise PipelineError('CANCELLED','reframe','Face tracking cancelled.')
                duration=(span.output_end_us-span.output_start_us)/1e6
                pattern=root/f'{index}-%06d.jpg'
                result=run_process([str(ffmpeg),'-nostdin','-v','error','-y','-threads','2','-ss',f'{seek_offset+span.source_start_us/1e6:.6f}','-i',str(source.local_path),'-map',f'0:{source.probe.get("video_stream_index",0)}','-t',f'{duration:.6f}','-vf',f'fps={config.sample_fps}:start_time=0:round=up,scale=640:-2','-threads','2',str(pattern)],cancelled=cancelled,capture_output=True,text=True,encoding='utf-8')
                if result.returncode:raise PipelineError('REFRAME_FAILED','reframe','Could not decode face tracking frames.')
                frames=sorted(root.glob(f'{index}-*.jpg'))
                if not frames:
                    samples.append((span.output_start_us,None))
                    continue # Short source spans can contain no decoded frame; interpolate safely.
                for frame_index,frame in enumerate(frames):
                    if cancelled():raise PipelineError('CANCELLED','reframe','Face tracking cancelled.')
                    t=span.output_start_us+round(frame_index/config.sample_fps*1e6)
                    if t>=span.output_end_us:break
                    image=mp.Image.create_from_file(str(frame))
                    detector_ms=max(detector_ms+1,t//1000)
                    result=detector.detect_for_video(image,detector_ms)
                    faces=[((d.bounding_box.origin_x+d.bounding_box.width/2)/image.width,d.bounding_box.width*d.bounding_box.height/(image.width*image.height),max((c.score for c in d.categories),default=0)) for d in result.detections]
                    if last_seen is not None and t-last_seen>1_000_000:previous=None
                    target=choose_face(faces,previous)
                    if target is not None:previous=target;last_seen=t;detected+=1
                    samples.append((t,target));frame.unlink()
                    if progress:progress(t,edl.duration_us)
    points=smooth_track(samples)
    if not detected:
        result=fallback('No confident face detected; using central crop.')
        return result.model_copy(update={'total_samples':len(samples),'model_sha256':file_hash(path)})
    return CropArtifact(source_id=source.id,edl_revision_id=edl.revision_id,mode='face-track',fallback_reason='Brief losses hold the crop; prolonged losses ease toward center.',points=points,model_sha256=file_hash(path),detected_samples=detected,total_samples=len(samples))
