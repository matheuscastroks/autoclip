import json,sys,shutil,uuid
from pathlib import Path
from engine.contracts import *
from engine.media.probe import probe_source
from engine.media.audio import extract_audio
from engine.pipeline.artifacts import atomic_json,file_hash,object_hash
from engine.pipeline.manifest import StageCache
from engine.pipeline.cancellation import run_process
from engine.adapters.gemini.analyzer import GeminiAnalyzer
from engine.editorial.select import select_candidates
from engine.editorial.edl import plan_continuous_edit
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
from engine.render.ffmpeg import FFmpegRenderer
from engine.render.verify import verify_render
from engine.editorial.review import review_fingerprint
from engine.pipeline.fingerprints import stage_dependencies,tool_fingerprint,font_fingerprint,resolve_font
from engine.adapters.openshorts.transcriber import model_fingerprint

CODE_ROOT=Path(__file__).resolve().parents[1]

def code_hash(*relative):
    return object_hash({p:file_hash(CODE_ROOT/p) for p in relative})

def _asr_worker(audio,config,root,cancelled):
    folder=root/'work'/uuid.uuid4().hex;folder.mkdir(parents=True)
    atomic_json(folder/'audio.json',audio);atomic_json(folder/'config.json',config)
    result=run_process([sys.executable,'-X','utf8','-m','engine.worker',str(folder/'audio.json'),str(folder/'config.json'),str(folder/'transcript.json')],cancelled=cancelled,capture_output=True,text=True,encoding='utf-8')
    if result.returncode:
        raise PipelineError('ASR_FAILED','transcribe','Local worker failed; check model and runtime.')
    return TranscriptArtifact.model_validate_json((folder/'transcript.json').read_bytes())

def run_project(source:Source,config:PipelineConfig,project_root:Path,cancelled=lambda:False,*,analyzer=None,transcriber=None,stop_after='render',precomputed_analysis:AnalysisArtifact|None=None) -> ProjectRun:
    if stop_after not in ('transcribe','analyze','render'):raise ValueError('Unknown stage boundary')
    root=Path(project_root).resolve();root.mkdir(parents=True,exist_ok=True)
    state_path=root/'project.json'
    if state_path.exists():
        previous=ProjectRun.model_validate_json(state_path.read_bytes())
        if previous.source.sha256!=source.sha256: raise PipelineError('SOURCE_CHANGED','run','Source changed; create another project.')
        source=previous.source
        project_id=previous.project_id
    else: project_id=uuid.uuid4()
    if file_hash(source.local_path)!=source.sha256: raise PipelineError('SOURCE_CHANGED','run','Source bytes changed; relink or create a new project.')
    source=probe_source(source,config.ffprobe)
    atomic_json(root/'source.json',source);atomic_json(root/'config.json',config)
    state=ProjectRun(project_id=project_id,source=source,status='processing')
    atomic_json(state_path,state)
    cache=StageCache(root)
    def check():
        if cancelled(): raise PipelineError('CANCELLED','run','Cancellation requested.')
    def stage(name,inputs,produce,model):
        check();print(f'Stage: {name}',flush=True)
        result=cache.run(name,inputs,produce,model)
        check();return result
    try:
        ffmpeg_identity=tool_fingerprint(config.ffmpeg)
        audio=stage('audio',{'source':source.sha256,'probe':source.probe,'runtime':stage_dependencies('audio'),'ffmpeg':ffmpeg_identity},lambda:extract_audio(source,config.ffmpeg,root,cancelled),AudioArtifact)
        model_file=config.asr.model_path/'model.bin'
        if not model_file.exists() and transcriber is None: raise PipelineError('MODEL_MISSING','transcribe','Local multilingual Whisper model missing.')
        assets=model_fingerprint(config.asr.model_path) if transcriber is None else 'injected:'+str(getattr(transcriber,'cache_identity',type(transcriber).__qualname__))
        transcript=stage('transcribe',{'audio':audio.sha256,'source_id':str(source.id),'config':config.asr.model_dump(mode='json'),'model_digest':assets,'runtime':stage_dependencies('transcribe')},lambda:transcriber.transcribe(audio,config.asr) if transcriber else _asr_worker(audio,config.asr,root,cancelled),TranscriptArtifact)
        atomic_json(root/'transcript.json',transcript);state.transcript_path=root/'transcript.json';atomic_json(state_path,state)
        if stop_after=='transcribe':
            state.status='transcribed';atomic_json(state_path,state);return state
        semantic={'model':config.analysis.model,'prompt_version':config.analysis.prompt_version,'window_seconds':config.analysis.window_seconds,'max_text_chars':config.analysis.max_text_chars,'clip_preferred_seconds':config.analysis.clip_preferred_seconds,'clip_max_seconds':config.analysis.clip_max_seconds,'show_thought_summaries':config.analysis.show_thought_summaries}
        if precomputed_analysis is not None:
            if stop_after!='render' or not precomputed_analysis.complete or precomputed_analysis.transcript_id!=transcript.transcript_id or set(precomputed_analysis.covered_word_ids)!={w.id for w in transcript.words}:
                raise PipelineError('INCOMPLETE_ANALYSIS','analyze','Existing analysis must cover the complete current transcript for rendering.')
            # Rendering consumes original analysis provenance. It must never seed
            # a provider cache under the user's current/new analysis settings.
            analysis=precomputed_analysis
        else:
            analysis=stage('analyze',{'transcript':object_hash(transcript),'config':semantic,'prompt_hash':file_hash(CODE_ROOT/'prompts/analysis_v1.txt'),'runtime':stage_dependencies('analyze')},lambda:(analyzer or GeminiAnalyzer(work_root=root/'work')).analyze(transcript,config.analysis,cancelled=cancelled),AnalysisArtifact)
            if 'analyze' in cache.reused and hasattr(analyzer,'publish_cached'):analyzer.publish_cached(analysis)
        atomic_json(root/'analysis.json',analysis)
        if stop_after=='analyze':
            state.status='analyzed';atomic_json(state_path,state);return state
        candidates=stage('select',{'analysis':object_hash(analysis),'config':config.selection.model_dump(mode='json'),'runtime':stage_dependencies('select')},lambda:select_candidates(analysis,transcript,config.selection),CandidateArtifact)
        atomic_json(root/'candidates.json',candidates);state.candidates_path=root/'candidates.json'
        verified_silences=None
        if config.pauses.enabled:
            from engine.media.pauses import detect_verified_silences
            verified_silences=stage('pauses',{'audio':audio.sha256,'source':source.sha256,'config':config.pauses.model_dump(mode='json'),'runtime':stage_dependencies('pauses')},lambda:detect_verified_silences(audio,config.pauses,cancelled=cancelled),PauseVerification)
            atomic_json(root/'pause-verification.json',verified_silences)
        failures=[]
        for candidate in candidates.candidates:
            try:
                edl=stage('edit_plan',{'candidate':object_hash(candidate),'source':source.sha256,'transcript':object_hash(transcript),'selection':config.selection.model_dump(mode='json'),'pauses':config.pauses.model_dump(mode='json'),'verified_silences':object_hash(verified_silences) if verified_silences else None,'runtime':stage_dependencies('edit_plan')},lambda:plan_continuous_edit(candidate,transcript,source,selection=config.selection,pauses=config.pauses,verified_silences=verified_silences),EDLArtifact)
                revision_dir=root/'revisions'/str(edl.revision_id);revision_dir.mkdir(parents=True,exist_ok=True)
                atomic_json(revision_dir/'edl.json',edl);atomic_json(revision_dir/'candidate.json',candidate)
                caption_config=config.captions.model_copy(update={'font_path':resolve_font(config.captions.font_path,config.captions.font_name)})
                font=font_fingerprint(caption_config.font_path,caption_config.font_name)
                caps=stage('captions',{'edl':object_hash(edl),'transcript':object_hash(transcript),'config':caption_config.model_dump(mode='json'),'font':font,'runtime':stage_dependencies('captions')},lambda:OpenShortsCaptionBuilder(root/'captions').build(transcript,edl,CaptionRevision(),caption_config),CaptionArtifact)
                atomic_json(revision_dir/'captions.json',caps)
                crop=CropArtifact(source_id=source.id,edl_revision_id=edl.revision_id)
                profile=object_hash({'edl':edl,'caps':caps,'crop':crop,'profile':config.export,'font':font,'ffmpeg':ffmpeg_identity,'runtime':stage_dependencies('render')})
                export_config=config.export.model_copy(update={'output_root':root/'previews'/profile})
                def render():
                    existing=export_config.output_root/(str(edl.revision_id)+'.mp4')
                    if existing.exists(): existing.replace(existing.with_suffix('.corrupt-'+uuid.uuid4().hex))
                    return FFmpegRenderer(config.ffmpeg,run=lambda cmd,**kw:run_process(cmd,cancelled=cancelled,**kw)).render(source,edl,crop,caps,export_config)
                rendered=stage('render',{'profile':profile},render,RenderArtifact)
                qa=stage('verify',{'render':object_hash(rendered),'edl':object_hash(edl),'ffmpeg':ffmpeg_identity,'ffprobe':tool_fingerprint(config.ffprobe),'runtime':stage_dependencies('verify')},lambda:verify_render(rendered,source,edl,config.ffprobe,config.ffmpeg,cancelled),ExportValidation)
                atomic_json(revision_dir/'render.json',rendered);atomic_json(revision_dir/'qa.json',qa)
                if not qa.technical_pass: raise PipelineError('EXPORT_INVALID','verify','Technical QA failed; inspect revision QA.')
                state.revisions.append({'revision_id':str(edl.revision_id),'candidate_id':str(candidate.id),'render_path':str(rendered.path),'review_status':'needs_review'})
            except PipelineError as exc:
                if exc.code=='CANCELLED': raise
                failures.append({'candidate_id':str(candidate.id),'error':exc.as_dict()})
                atomic_json(root/'item-errors.json',failures)
        state.status='failed' if failures else ('needs_review' if state.revisions else 'no_candidates')
        atomic_json(root/'last-run.json',{'reused':cache.reused,'failures':failures})
        atomic_json(state_path,state)
        return state
    except (PipelineError,KeyboardInterrupt) as exc:
        state.status='cancelled' if isinstance(exc,KeyboardInterrupt) or getattr(exc,'code',None)=='CANCELLED' else 'failed'
        atomic_json(state_path,state)
        if isinstance(exc,PipelineError): atomic_json(root/'last-error.json',exc.as_dict())
        raise

def resume_project(project_root:Path,config:PipelineConfig|None=None) -> ProjectRun:
    root=Path(project_root).resolve()
    source=Source.model_validate_json((root/'source.json').read_bytes())
    config=config or PipelineConfig.model_validate_json((root/'config.json').read_bytes())
    return run_project(source,config,root)

def export_approved(project_root:Path):
    root=Path(project_root).resolve();state=ProjectRun.model_validate_json((root/'project.json').read_bytes())
    if file_hash(state.source.local_path)!=state.source.sha256: raise PipelineError('SOURCE_CHANGED','export','Source changed.')
    exported=[]
    for revision in state.revisions:
        folder=root/'revisions'/revision['revision_id']
        if (folder/'deleted.json').is_file():continue
        decision_path=folder/'review.json'
        if not decision_path.exists(): continue
        decision=ReviewDecision.model_validate_json(decision_path.read_bytes())
        if decision.decision!='approved': continue
        edl=EDLArtifact.model_validate_json((folder/'edl.json').read_bytes())
        caps=CaptionArtifact.model_validate_json((folder/'captions.json').read_bytes())
        rendered=RenderArtifact.model_validate_json((folder/'render.json').read_bytes())
        qa=ExportValidation.model_validate_json((folder/'qa.json').read_bytes())
        if decision.revision_id!=edl.revision_id or decision.content_hash!=review_fingerprint(root,edl.revision_id) or not qa.technical_pass or file_hash(rendered.path)!=rendered.sha256:
            raise PipelineError('STALE_REVIEW','export','Review or render is invalid for this revision.')
        package_hash=object_hash({'review':decision,'edl':edl,'caption':caps,'render':rendered})
        target=root/'exports'/revision['revision_id']/package_hash[:16];target.mkdir(parents=True,exist_ok=True)
        if (target/'manifest.json').exists() and json.loads((target/'manifest.json').read_text(encoding='utf-8'))['package_hash']!=package_hash:
            raise PipelineError('EXPORT_CONFLICT','export','Export package prefix collision; full content hash differs.')
        for src,name in [(rendered.path,'clip.mp4'),(caps.ass_path,'captions.ass'),(caps.srt_path,'captions.srt'),(folder/'edl.json','edl.json')]:
            dest=target/name
            if not dest.exists(): shutil.copyfile(src,dest)
            if file_hash(src)!=file_hash(dest): raise PipelineError('EXPORT_INVALID','export','Export checksum mismatch.')
        atomic_json(target/'words.json',caps.words)
        atomic_json(target/'metadata.json',{'schema_version':'1.0','source':state.source,'review':decision,'candidate':json.loads((folder/'candidate.json').read_text(encoding='utf-8')),'caption_revision_id':str(caps.revision_id),'transcript_id':str(edl.transcript_id),'render':rendered,'qa':qa})
        atomic_json(target/'manifest.json',{'schema_version':'1.0','revision_id':revision['revision_id'],'package_hash':package_hash,'files':{p.name:{'sha256':file_hash(p),'bytes':p.stat().st_size} for p in target.iterdir() if p.is_file() and p.name!='manifest.json'}})
        exported.append(str(target))
    if not exported: raise PipelineError('REVIEW_REQUIRED','export','No human-approved revisions available.')
    return exported
