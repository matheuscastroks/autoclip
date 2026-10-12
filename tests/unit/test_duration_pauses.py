import pytest
from pathlib import Path
from test_gemini import transcript,payload

def test_three_minute_limit_preserves_complete_two_minute_argument(tmp_path):
    from engine.contracts import Source,Candidate,SelectionConfig
    from engine.editorial.edl import plan_continuous_edit
    t=transcript();t.segments=[]
    for i,w in enumerate(t.words):w.end_us=i*4_000_000+3_000_000;w.start_us=i*4_000_000
    s=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'video.mp4',duration_us=180_000_000)
    edl=plan_continuous_edit(Candidate.model_validate(payload(t)['candidates'][0]),t,s,selection=SelectionConfig(max_us=180_000_000))
    assert 119_000_000<=edl.duration_us<=120_000_000 and len(edl.protected_word_ids)==30

def test_only_verified_long_silence_is_shortened_and_captions_remap(tmp_path):
    from engine.contracts import Source,Candidate,PauseConfig,PauseVerification,Interval,CaptionConfig,CaptionRevision
    from engine.editorial.edl import plan_continuous_edit,output_at
    from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
    t=transcript();t.segments=[]
    for w in t.words[10:]:w.end_us+=4_000_000;w.start_us+=4_000_000
    s=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'video.mp4',duration_us=40_000_000)
    verified=PauseVerification(source_id=s.id,source_sha256=s.sha256,audio_sha256='b'*64,silences=[Interval(start_us=10_000_000,end_us=14_000_000)])
    edl=plan_continuous_edit(Candidate.model_validate(payload(t)['candidates'][0]),t,s,pauses=PauseConfig(enabled=True),verified_silences=verified)
    assert len(edl.spans)==2 and edl.removed
    assert edl.protected_word_ids==[w.id for w in t.words]
    assert output_at(edl,12_000_000) is None
    caps=OpenShortsCaptionBuilder(tmp_path/'captions').build(t,edl,CaptionRevision(),CaptionConfig())
    assert len(caps.words)==30 and caps.words[10].start_us==output_at(edl,t.words[10].start_us)
    assert caps.words[10].start_us<t.words[10].start_us

def test_timestamp_gap_without_audio_confirmation_preserves_pause(tmp_path):
    from engine.contracts import Source,Candidate,PauseConfig
    from engine.editorial.edl import plan_continuous_edit
    t=transcript();s=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'v',duration_us=40_000_000)
    edl=plan_continuous_edit(Candidate.model_validate(payload(t)['candidates'][0]),t,s,pauses=PauseConfig(enabled=True))
    assert not edl.removed and len(edl.spans)==1

def test_vad_speech_and_breath_energy_protect_untranscribed_audio(tmp_path):
    from engine.media.pauses import detect_verified_silences
    from engine.contracts import AudioArtifact,PauseConfig
    import numpy as np,wave
    path=tmp_path/'audio.wav';samples=np.zeros(16000*5,dtype=np.int16);samples[16000*2:16000*3]=8000
    with wave.open(str(path),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000);f.writeframes(samples.tobytes())
    from engine.pipeline.artifacts import file_hash
    audio=AudioArtifact(source_id=__import__('uuid').uuid4(),source_sha256='a'*64,path=path,sha256=file_hash(path),duration_us=5_000_000)
    result=detect_verified_silences(audio,PauseConfig(enabled=True),speech_detector=lambda a:[{'start':16000,'end':32000}])
    assert result.silences
    assert all(not (s.start_us<3_000_000 and s.end_us>1_000_000) for s in result.silences)
