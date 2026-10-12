"""Real local subprocess and FFmpeg; adopted fixture ASR, never Gemini."""
import time,subprocess
from pathlib import Path
from engine.contracts import Source,TranscriptArtifact,Word
from engine.pipeline.artifacts import atomic_json,file_hash

def test_local_worker_completes_without_retranscribing_or_calling_provider(tmp_path):
    from engine.api.jobs import JobManager
    from engine.api.store import ProjectStore
    from engine.media.probe import locate_tools
    ffmpeg,_=locate_tools();root=tmp_path/'vídeo de teste';root.mkdir()
    video=root/'fonte.mp4'
    subprocess.run([str(ffmpeg),'-v','error','-f','lavfi','-i','color=c=blue:s=64x64:r=10:d=2','-f','lavfi','-i','sine=frequency=440:duration=2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(video)],check=True,capture_output=True)
    source=Source(local_path=video,sha256=file_hash(video),duration_us=2_000_000)
    transcript=TranscriptArtifact(source_id=source.id,source_sha256=source.sha256,model={'kind':'TEST FIXTURE ONLY'},words=[Word(id='w1',text='Teste',start_us=0,end_us=1_000_000)])
    atomic_json(root/'source.json',source);atomic_json(root/'transcript.json',transcript)
    store=ProjectStore(tmp_path/'.autoclip/library.sqlite');pid=store.register(root)['id']
    manager=JobManager(store,tmp_path);job=manager.start(pid,'transcribe',{})
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        result=manager.status(job['id'])
        if result['status'] not in ('running','pending','cancelling'):break
        time.sleep(.2)
    assert result['status']=='completed',result
    assert not (tmp_path/'.autoclip/jobs'/job['id']/'budget.sqlite').exists() or result.get('requests_used',0)==0
    assert TranscriptArtifact.model_validate_json((root/'transcript.json').read_bytes()).words==transcript.words
    assert not (root/'analysis.json').exists()
