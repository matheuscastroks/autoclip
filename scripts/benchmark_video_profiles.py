"""Reproducible local synthetic benchmark. No Whisper, AI or private media.

Run: python scripts/benchmark_video_profiles.py --output .runtime-tmp/video-benchmark
The output directory must not already contain files.
"""
import argparse
import json
import subprocess
import time
from pathlib import Path

from engine.contracts import (
    PREVIEW_PROFILE, FINAL_PROFILE, Candidate, CaptionConfig, CaptionRevision,
    EDLArtifact, EditorialFlags, ProjectRun, ReframeConfig, Span, TranscriptArtifact, Word,
)
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
from engine.media.face_tracking import track_faces
from engine.media.importer import import_source
from engine.media.probe import locate_tools, probe_source
from engine.pipeline import outputs
from engine.pipeline.artifacts import atomic_json, object_hash
from engine.pipeline.fingerprints import resolve_font


def benchmark(root: Path):
    root = root.resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError('Use a new empty benchmark directory; existing data is never overwritten.')
    root.mkdir(parents=True, exist_ok=True)
    ffmpeg, ffprobe = locate_tools()
    started = time.perf_counter()
    media = root / 'synthetic.mp4'
    subprocess.run([str(ffmpeg), '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=1280x720:rate=30:duration=30', '-f', 'lavfi', '-i',
        'sine=frequency=440:duration=30', '-c:v', 'libx264', '-preset', 'veryfast',
        '-c:a', 'aac', '-threads', '2', str(media)], check=True)
    source = probe_source(import_source(str(media), root/'project'), ffprobe)
    project = root/'project'
    ranges = [(0,8), (10,18), (20,28)]
    words = [Word(id=f'w{i}', text='Legenda', start_us=t*1_000_000, end_us=t*1_000_000+700_000)
             for i,t in enumerate(t for start,end in ranges for t in range(start,end))]
    transcript = TranscriptArtifact(source_id=source.id, source_sha256=source.sha256, words=words)
    candidate = Candidate(topic_id='synthetic', start_word_id=words[0].id, end_word_id=words[-1].id,
        evidence_word_ids=[w.id for w in words], rationale='Synthetic benchmark only; not an editorial selection.',
        title_suggestion='Benchmark sintético — prévia e final',
        editorial=EditorialFlags(completeness='uncertain', standalone_context='uncertain', qualification_preserved='uncertain'))
    edl = EDLArtifact(source_id=source.id, transcript_id=transcript.transcript_id, duration_us=24_000_000,
        protected_word_ids=[w.id for w in words], spans=[Span(source_start_us=a*1_000_000, source_end_us=b*1_000_000,
        output_start_us=i*8_000_000, output_end_us=(i+1)*8_000_000) for i,(a,b) in enumerate(ranges)])
    folder = project/'revisions'/str(edl.revision_id)
    folder.mkdir(parents=True)
    atomic_json(folder/'edl.json', edl)
    atomic_json(folder/'candidate.json', candidate)
    atomic_json(project/'transcript.json', transcript)
    prep_without_media = time.perf_counter()
    caps = OpenShortsCaptionBuilder(project/'captions').build(transcript, edl, CaptionRevision(),
        CaptionConfig(font_path=resolve_font(None, 'Montserrat ExtraBold'), opening_text='Prévia e final'))
    caption_seconds = time.perf_counter()-prep_without_media
    face_start = time.perf_counter()
    crop = track_faces(source, edl, ReframeConfig(), ffmpeg)
    face_seconds = time.perf_counter()-face_start
    atomic_json(folder/'captions.json', caps)
    atomic_json(folder/'crop.json', crop)
    outputs.save_preparation(project, folder, analysis_hash=object_hash(candidate), plan_hash=object_hash(edl))
    atomic_json(project/'project.json', ProjectRun(source=source, status='needs_review',
        revisions=[{'revision_id':str(edl.revision_id),'candidate_id':str(candidate.id)}]))
    preparation_seconds = time.perf_counter()-prep_without_media
    results = {'source_seconds':30,'source_dimensions':[1280,720],'cut_seconds':24,'edl_segments':3,
        'source_and_fixture_seconds':prep_without_media-started,'preparation_seconds':preparation_seconds,
        'caption_seconds':caption_seconds,'reframe_seconds':face_seconds,'crop_mode':crop.mode,'outputs':{}}
    for profile in (PREVIEW_PROFILE, FINAL_PROFILE):
        timing = {'verify_start':None}
        start = time.perf_counter()
        def progress(done, total, phase='render'):
            if phase=='verify':timing['verify_start']=time.perf_counter()
        result, reused = outputs.render_output(project, edl.revision_id, profile, ffmpeg, ffprobe, progress=progress)
        end = time.perf_counter()
        render = result.render if profile.name=='preview' else result
        state=ProjectRun.model_validate_json((project/'project.json').read_bytes())
        state.revisions[0]['preview_path' if profile.name=='preview' else 'render_path']=str(render.path)
        atomic_json(project/'project.json',state)
        warm_start = time.perf_counter()
        _, warm_reused = outputs.render_output(project, edl.revision_id, profile, ffmpeg, ffprobe)
        results['outputs'][profile.name] = dict(profile=profile.model_dump(mode='json'), total_seconds=end-start,
            render_and_lookup_seconds=(timing['verify_start'] or end)-start,
            validation_seconds=end-(timing['verify_start'] or end), bytes=render.size_bytes,
            cold_reused=reused, warm_reused=warm_reused, warm_seconds=time.perf_counter()-warm_start)
    atomic_json(root/'benchmark.json',results)
    print(json.dumps(results,indent=2,ensure_ascii=False))
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    benchmark(parser.parse_args().output)
