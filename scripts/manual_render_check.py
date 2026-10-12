"""Real media render check using a MANUAL span, never a Gemini selection."""
import json,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from engine.contracts import *
from engine.media.importer import import_source
from engine.media.probe import probe_source,locate_tools
from engine.pipeline.artifacts import atomic_json,file_hash
from engine.editorial.edl import plan_continuous_edit
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
from engine.render.ffmpeg import FFmpegRenderer
from engine.render.verify import verify_render
from engine.editorial.report import create_report

project=root/'poc-projects/manual-render-check';project.mkdir(parents=True,exist_ok=True)
ffmpeg,ffprobe=locate_tools()
source=probe_source(import_source(str(root/'research/media/z0cf-eWBVCo.mp4'),project),ffprobe)
raw=json.loads((root/'research/results/openshorts-asr.json').read_text(encoding='utf-8'))['transcript']
words=[]
for segment in raw['segments']:
    for w in segment['words']:
        if w['end']>w['start']:
            words.append(Word(id=f'w{len(words):07d}',text=w['word'].strip(),start_us=60_000_000+round(w['start']*1e6),end_us=60_000_000+round(w['end']*1e6)))
t=TranscriptArtifact(source_id=source.id,source_sha256=source.sha256,words=words,model={'purpose':'partial 60–180s ASR smoke reused ONLY for manual rendering check','not_full_source':True})
end=next(w for w in words if w.end_us>=85_000_000)
c=Candidate(topic_id='manual-render-check',start_word_id=words[0].id,end_word_id=end.id,evidence_word_ids=[words[0].id,end.id],rationale='Trecho manual para verificar áudio, fit-blur e legendas. Não foi selecionado pelo Gemini nem aprovado editorialmente.',editorial=EditorialFlags(completeness='uncertain',standalone_context='uncertain',qualification_preserved='uncertain'),title_suggestion='Teste técnico de render — seleção manual')
edl=plan_continuous_edit(c,t,source)
folder=project/'revisions'/str(edl.revision_id);folder.mkdir(parents=True)
caps=OpenShortsCaptionBuilder(project/'captions').build(t,edl,CaptionRevision(),CaptionConfig())
started=time.perf_counter()
rendered=FFmpegRenderer(ffmpeg).render(source,edl,CropArtifact(source_id=source.id,edl_revision_id=edl.revision_id),caps,ExportConfig(output_root=project/'previews'))
qa=verify_render(rendered,source,edl,ffprobe,ffmpeg)
for name,value in [('edl',edl),('candidate',c),('captions',caps),('render',rendered),('qa',qa)]:atomic_json(folder/(name+'.json'),value)
atomic_json(project/'transcript.json',t)
state=ProjectRun(source=source,status='needs_review',transcript_path=project/'transcript.json',revisions=[{'revision_id':str(edl.revision_id),'candidate_id':str(c.id),'render_path':str(rendered.path),'review_status':'needs_review'}])
atomic_json(project/'project.json',state)
report=create_report(project)
summary={'schema_version':'1.0','source_sha256':source.sha256,'selection':'MANUAL TECHNICAL CHECK — Gemini was not called','editorial_status':'not approved','duration_us':edl.duration_us,'render':rendered,'qa':qa,'wall_seconds':round(time.perf_counter()-started,3),'report':str(report)}
atomic_json(project/'manual-check.json',summary)
print(json.dumps({'technical_pass':qa.technical_pass,'render':str(rendered.path),'report':str(report)},ensure_ascii=False),flush=True)
