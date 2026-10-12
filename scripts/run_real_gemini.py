"""Evaluate Gemini on a provenance-checked complete local ASR artifact.

Uses the already completed full-source ASR stage rather than repeating CPU
inference. Its identity enters cache keys; this is not a default-ASR cache seed.
"""
import sys,json,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from engine.contracts import *
from engine.pipeline.artifacts import file_hash,atomic_json
from engine.pipeline.runner import run_project
from engine.media.probe import locate_tools
from engine.editorial.report import create_report

parser=argparse.ArgumentParser();parser.add_argument('--model',required=True);parser.add_argument('--max-calls',type=int,required=True);args=parser.parse_args()
prepared=root/'poc-projects/jones-manoel'
transcript_path=prepared/'transcript.json'
if not transcript_path.is_file():raise SystemExit('Full-source local ASR is still running; no remote request made.')
source=Source.model_validate_json((prepared/'source.json').read_bytes())
t=TranscriptArtifact.model_validate_json(transcript_path.read_bytes())
asr_result=json.loads((prepared/'asr-result.json').read_text(encoding='utf-8'))
if asr_result['status']!='completed' or asr_result['coverage']!='complete source' or t.source_sha256!=source.sha256 or file_hash(source.local_path)!=source.sha256:
    raise SystemExit('Invalid source/transcript provenance; no remote request made.')

class ValidatedTranscript:
    cache_identity='validated-full-source-artifact:'+file_hash(transcript_path)
    def transcribe(self,audio,config):
        if audio.source_id!=t.source_id or audio.source_sha256!=t.source_sha256:raise ValueError('Source mismatch')
        if any(w.end_us>audio.duration_us+100_000 for w in t.words):raise ValueError('Word outside complete source')
        result=t.model_copy(deep=True)
        result.model['restoration']={'kind':'validated complete-source artifact','transcript_sha256':file_hash(transcript_path),'actual_asr_result':asr_result}
        return result

ffmpeg,ffprobe=locate_tools();project=root/'poc-projects/gemini-test'
config=PipelineConfig(asr=ASRConfig(model_path=root/'research/models/whisper-small'),analysis=AnalysisConfig(model=args.model,max_calls=args.max_calls,window_seconds=1800,max_text_chars=300000),export=ExportConfig(output_root=project/'previews'),ffmpeg=ffmpeg,ffprobe=ffprobe)
state=run_project(source,config,project,transcriber=ValidatedTranscript())
report=create_report(project) if state.revisions else None
analysis=json.loads((project/'analysis.json').read_text(encoding='utf-8'))
summary={'schema_version':'1.0','model':args.model,'request_budget':args.max_calls,'requests_used':len(analysis['payload_hashes']),'source_sha256':source.sha256,'status':state.status,'proposed_clips':len(analysis['candidates']),'rendered_clips':len(state.revisions),'editorial_status':'requires human review','report':str(report) if report else None,'complete_source_asr_seconds':asr_result['wall_seconds']}
atomic_json(project/'gemini-result.json',summary)
atomic_json(root/'poc-results/real-gemini.json',summary)
print(json.dumps(summary,ensure_ascii=False),flush=True)
