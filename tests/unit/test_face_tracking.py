import pytest
from engine.contracts import CropArtifact

def test_path_smoothing_dropout_and_bounds():
    from engine.media.face_tracking import smooth_track
    points=smooth_track([(0,.2),(500_000,.21),(1_000_000,.8),(1_500_000,None),(3_000_000,None)],hold_us=1_000_000)
    assert points[0].center_x==pytest.approx(.2)
    assert points[1].center_x==pytest.approx(.2) # dead zone
    assert .2<points[2].center_x<.8
    assert points[3].center_x==points[2].center_x
    assert points[2].center_x<points[4].center_x<=.5

def test_nearest_face_stays_selected():
    from engine.media.face_tracking import choose_face
    faces=[(.2,.1,.9),(.8,.3,.99)]
    assert choose_face(faces,None)==.8
    assert choose_face(faces,.2)==.2

def test_dynamic_crop_expression_and_invalid_timeline():
    from engine.media.face_tracking import crop_expression
    from engine.contracts import CropPoint
    points=[CropPoint(output_us=0,center_x=.2),CropPoint(output_us=1_000_000,center_x=.8)]
    expr=crop_expression(points)
    assert 't' in expr and 'iw' in expr and '1080' in expr
    from uuid import uuid4
    with pytest.raises(ValueError):CropArtifact(source_id=uuid4(),edl_revision_id=uuid4(),mode='face-track',points=list(reversed(points)))

def test_missing_model_falls_back_without_decoding(tmp_path):
    from engine.media.face_tracking import track_faces
    from engine.contracts import ReframeConfig
    from types import SimpleNamespace
    from uuid import uuid4
    source=SimpleNamespace(id=uuid4());edl=SimpleNamespace(revision_id=uuid4())
    result=track_faces(source,edl,ReframeConfig(model_path=tmp_path/'missing.tflite'),tmp_path/'ffmpeg')
    assert result.mode=='center-crop' and 'unavailable' in result.fallback_reason

def test_far_face_is_not_immediately_switched():
    from engine.media.face_tracking import choose_face
    assert choose_face([(.9,.2,.9)],.2) is None

def test_short_empty_span_and_origin_offset_preserve_output_timeline(tmp_path,monkeypatch):
    import sys
    from types import SimpleNamespace as NS
    from uuid import uuid4
    from engine.contracts import Source,EDLArtifact,Span,ReframeConfig
    from engine.media import face_tracking as tracking
    class Options:
        Delegate=NS(CPU='CPU')
        def __init__(self,**kwargs):pass
    fake_mp=NS(tasks=NS(BaseOptions=Options,vision=NS(FaceDetectorOptions=Options,RunningMode=NS(VIDEO='VIDEO'))),Image=NS(create_from_file=lambda _:NS(width=640,height=360)))
    monkeypatch.setitem(sys.modules,'mediapipe',fake_mp)
    model=tmp_path/'model';model.write_bytes(b'model')
    calls=[]
    def decode(args,**kwargs):
        from pathlib import Path
        calls.append(args)
        if len(calls)>1:Path(args[-1].replace('%06d','000001')).write_bytes(b'frame')
        return NS(returncode=0)
    monkeypatch.setattr(tracking,'run_process',decode)
    class Detector:
        def __enter__(self):return self
        def __exit__(self,*_):pass
        def detect_for_video(self,image,t):return NS(detections=[NS(bounding_box=NS(origin_x=300,width=80,height=90),categories=[NS(score=.9)])])
    source=Source(local_path=tmp_path/'source.mp4',sha256='a'*64,duration_us=2_000_000,probe={'video_origin_us':3_000_000,'raw':{'format':{'start_time':'2'}}})
    edl=EDLArtifact(source_id=source.id,transcript_id=uuid4(),duration_us=1_100_000,protected_word_ids=[],spans=[Span(source_start_us=300_000,source_end_us=400_000,output_start_us=0,output_end_us=100_000),Span(source_start_us=900_000,source_end_us=1_900_000,output_start_us=100_000,output_end_us=1_100_000)])
    crop=tracking.track_faces(source,edl,ReframeConfig(model_path=model),tmp_path/'ffmpeg',detector_factory=lambda _:Detector())
    assert crop.mode=='face-track'
    assert [p.output_us for p in crop.points]==[0,100_000]
    assert calls[0][calls[0].index('-ss')+1]=='1.300000'
    assert calls[1][calls[1].index('-ss')+1]=='1.900000'
    from engine.contracts import PipelineError
    with pytest.raises(PipelineError,match='cancelled'):
        tracking.track_faces(source,edl,ReframeConfig(model_path=model),tmp_path/'ffmpeg',cancelled=lambda:True,detector_factory=lambda _:Detector())

def test_crop_expression_simplifies_large_point_lists():
    from engine.media.face_tracking import crop_expression
    from engine.contracts import CropPoint
    # 500 samples micro-jittering across a timeline
    points=[CropPoint(output_us=i*500_000,center_x=0.5+0.05*(i%5)) for i in range(500)]
    expr=crop_expression(points)
    assert expr.count('clip(')<=60
    assert 'max(0,min(iw-1080' in expr

def test_native_detector_load_error_falls_back_to_center_crop(tmp_path,monkeypatch):
    import sys
    from types import SimpleNamespace as NS
    from uuid import uuid4
    from engine.contracts import Source,EDLArtifact,Span,ReframeConfig
    from engine.media import face_tracking as tracking
    class Options:
        Delegate=NS(CPU='CPU')
        def __init__(self,**kwargs):pass
    fake_mp=NS(tasks=NS(BaseOptions=Options,vision=NS(FaceDetectorOptions=Options,RunningMode=NS(VIDEO='VIDEO'))))
    monkeypatch.setitem(sys.modules,'mediapipe',fake_mp)
    model=tmp_path/'model.tflite';model.write_bytes(b'model')
    source=Source(local_path=tmp_path/'source.mp4',sha256='a'*64,duration_us=1_000_000,probe={})
    edl=EDLArtifact(source_id=source.id,transcript_id=uuid4(),duration_us=1_000_000,protected_word_ids=[],spans=[Span(source_start_us=0,source_end_us=1_000_000,output_start_us=0,output_end_us=1_000_000)])
    def broken_detector(_):
        raise OSError("Could not find module 'libmediapipe.dll'")
    crop=tracking.track_faces(source,edl,ReframeConfig(model_path=model),tmp_path/'ffmpeg',detector_factory=broken_detector)
    assert crop.mode=='center-crop' and 'unavailable' in crop.fallback_reason.lower()


