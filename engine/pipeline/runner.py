import json,sys,shutil,uuid
from pathlib import Path
from engine.contracts import *
from engine.media.probe import probe_source
from engine.media.audio import extract_audio
from engine.pipeline.artifacts import atomic_json,file_hash,object_hash
from engine.pipeline.manifest import StageCache
from engine.pipeline.cancellation import run_process
from engine.adapters.gemini.analyzer import GeminiAnalyzer
from engine.editorial.select import select_candidates,validate_explicit_candidates
from engine.editorial.edl import plan_continuous_edit
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
from engine.render.ffmpeg import FFmpegRenderer
from engine.render.opening import opening_for
from engine.media.face_tracking import track_faces,model_path as face_model_path
from engine.render.verify import verify_render
from engine.editorial.review import review_fingerprint,current_review
from engine.pipeline.fingerprints import stage_dependencies,tool_fingerprint,font_fingerprint,resolve_font
from engine.adapters.openshorts.transcriber import model_fingerprint

CODE_ROOT=Path(__file__).resolve().parents[1]

def code_hash(*relative):
    from engine.pipeline.fingerprints import safe_file_hash
    return object_hash({p:safe_file_hash(CODE_ROOT/p) for p in relative})

def _asr_worker(audio,config,root,cancelled):
    folder=root/'work'/uuid.uuid4().hex;folder.mkdir(parents=True)
    atomic_json(folder/'audio.json',audio);atomic_json(folder/'config.json',config)
    from engine.system.subprocesses import engine_cmd
    cmd = engine_cmd('worker', folder/'audio.json', folder/'config.json', folder/'transcript.json', module='engine.worker')
    result=run_process(cmd,cancelled=cancelled,capture_output=True,text=True,encoding='utf-8')
    if result.returncode:
        raise PipelineError('ASR_FAILED','transcribe','Local worker failed; check model and runtime.')
    return TranscriptArtifact.model_validate_json((folder/'transcript.json').read_bytes())

def run_project(source:Source,config:PipelineConfig,project_root:Path,cancelled=lambda:False,*,analyzer=None,transcriber=None,stop_after='render',precomputed_analysis:AnalysisArtifact|None=None,candidate_ids=None,analysis_hash=None,progress=None) -> ProjectRun:
    if stop_after not in ('transcribe','analyze','render'):raise ValueError('Unknown stage boundary')
    root=Path(project_root).resolve();root.mkdir(parents=True,exist_ok=True)
    state_path=root/'project.json'
    previous=None
    if state_path.exists():
        previous=ProjectRun.model_validate_json(state_path.read_bytes())
        if previous.source.sha256!=source.sha256: raise PipelineError('SOURCE_CHANGED','run','Source changed; create another project.')
        source=previous.source
        project_id=previous.project_id
    else: project_id=uuid.uuid4()
    if file_hash(source.local_path)!=source.sha256: raise PipelineError('SOURCE_CHANGED','run','Source bytes changed; relink or create a new project.')
    source=probe_source(source,config.ffprobe)
    atomic_json(root/'source.json',source);atomic_json(root/'config.json',config)
    state=ProjectRun(project_id=project_id,source=source,status='processing',revisions=list(previous.revisions) if previous else [])
    atomic_json(state_path,state)
    cache=StageCache(root)
    items=[];current=None
    def report(phase,processed_us=0,total_us=None):
        if not progress:return
        from engine.pipeline.progress import activity_time
        if current:current['phase']=phase;current['state']='running';current['processed_us']=processed_us;current['total_us']=total_us
        progress({'schema_version':'1.0','operation':'render','phase':phase,'current_candidate_id':current['candidate_id'] if current else None,'current_index':items.index(current)+1 if current else 0,'total_items':len(items),'completed_items':sum(i['state']=='ready' for i in items),'failed_items':sum(i['state']=='failed' for i in items),'processed_us':processed_us,'total_us':total_us,'activity_at':activity_time(),'items':[dict(i) for i in items]})
    def check():
        if cancelled(): raise PipelineError('CANCELLED','run','Cancellation requested.')
    def stage(name,inputs,produce,model):
        check();print(f'Stage: {name}',flush=True)
        if items:report(name)
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
        semantic={'clip_min_seconds':config.analysis.clip_min_seconds,'model':config.analysis.model,'prompt_version':config.analysis.prompt_version,'window_seconds':config.analysis.window_seconds,'max_text_chars':config.analysis.max_text_chars,'clip_preferred_seconds':config.analysis.clip_preferred_seconds,'clip_max_seconds':config.analysis.clip_max_seconds,'show_thought_summaries':config.analysis.show_thought_summaries}
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
        config.selection=config.selection.model_copy(update={'min_us':analysis.clip_min_seconds*1_000_000})
        if candidate_ids is not None and analysis.clip_min_seconds>=60 and len(candidate_ids)>10:raise PipelineError('INVALID_SELECTION','select','Select at most 10 topic clips.')
        if candidate_ids is not None and analysis_hash!=object_hash(analysis):raise PipelineError('STALE_ANALYSIS','select','Analysis changed; reselect proposals.')
        candidates=stage('select',{'analysis':object_hash(analysis),'selection':candidate_ids,'config':config.selection.model_dump(mode='json'),'runtime':stage_dependencies('select')},lambda:validate_explicit_candidates(analysis,transcript,config.selection,candidate_ids) if candidate_ids is not None else select_candidates(analysis,transcript,config.selection),CandidateArtifact)
        atomic_json(root/'candidates.json',candidates);state.candidates_path=root/'candidates.json'
        verified_silences=None
        items=[{'candidate_id':str(c.id),'title':c.title_suggestion,'state':'pending','phase':'waiting','processed_us':0,'total_us':None} for c in candidates.candidates];report('pauses' if config.pauses.enabled else 'edit_plan')
        if config.pauses.enabled:
            from engine.media.pauses import detect_verified_silences
            verified_silences=stage('pauses',{'audio':audio.sha256,'source':source.sha256,'config':config.pauses.model_dump(mode='json'),'runtime':stage_dependencies('pauses')},lambda:detect_verified_silences(audio,config.pauses,cancelled=cancelled),PauseVerification)
            atomic_json(root/'pause-verification.json',verified_silences)
        failures=[]
        for candidate in candidates.candidates:
            current=next(i for i in items if i['candidate_id']==str(candidate.id))
            try:
                # A changed presentation creates a new revision, retaining the old render and its review.
                recipe={'captions':config.captions,'export':config.export,'crop':config.reframe,'reframe_runtime':stage_dependencies('reframe'),'face_model':file_hash(face_model_path(config.reframe)) if face_model_path(config.reframe).is_file() else 'missing','render_runtime':stage_dependencies('render'),'caption_runtime':stage_dependencies('captions'),'ffmpeg':ffmpeg_identity,'font':font_fingerprint(config.captions.font_path,config.captions.font_name)}
                edl=stage('edit_plan',{'candidate':object_hash(candidate),'source':source.sha256,'transcript':object_hash(transcript),'selection':config.selection.model_dump(mode='json'),'pauses':config.pauses.model_dump(mode='json'),'verified_silences':object_hash(verified_silences) if verified_silences else None,'runtime':stage_dependencies('edit_plan'),'presentation_recipe':object_hash(recipe)},lambda:plan_continuous_edit(candidate,transcript,source,selection=config.selection,pauses=config.pauses,verified_silences=verified_silences),EDLArtifact)
                revision_dir=root/'revisions'/str(edl.revision_id);revision_dir.mkdir(parents=True,exist_ok=True)
                atomic_json(revision_dir/'edl.json',edl);atomic_json(revision_dir/'candidate.json',candidate)
                caption_config=config.captions.model_copy(update={'font_path':resolve_font(config.captions.font_path,config.captions.font_name),'opening_text':config.captions.opening_text or opening_for(candidate)})
                font=font_fingerprint(caption_config.font_path,caption_config.font_name)
                caps=stage('captions',{'edl':object_hash(edl),'transcript':object_hash(transcript),'config':caption_config.model_dump(mode='json'),'font':font,'runtime':stage_dependencies('captions')},lambda:OpenShortsCaptionBuilder(root/'captions').build(transcript,edl,CaptionRevision(),caption_config),CaptionArtifact)
                atomic_json(revision_dir/'captions.json',caps)
                crop=stage('reframe',{'source':source.sha256,'edl':object_hash(edl),'config':config.reframe,'runtime':stage_dependencies('reframe'),'model':recipe['face_model'],'ffmpeg':ffmpeg_identity},lambda:track_faces(source,edl,config.reframe,config.ffmpeg,cancelled=cancelled,progress=lambda done,total:report('reframe',done,total)),CropArtifact)
                atomic_json(revision_dir/'crop.json',crop)
                profile=object_hash({'edl':edl,'caps':caps,'crop':crop,'profile':config.export,'font':font,'ffmpeg':ffmpeg_identity,'runtime':stage_dependencies('render')})
                export_config=config.export.model_copy(update={'output_root':root/'previews'/profile})
                def render():
                    existing=export_config.output_root/(str(edl.revision_id)+'.mp4')
                    if existing.exists(): existing.replace(existing.with_suffix('.corrupt-'+uuid.uuid4().hex))
                    return FFmpegRenderer(config.ffmpeg,run=lambda cmd,**kw:run_process(cmd,cancelled=cancelled,**kw),progress=(lambda done,total:report('render',done,total)) if progress else None).render(source,edl,crop,caps,export_config)
                reused_before=cache.reused.count('render')
                rendered=stage('render',{'profile':profile},render,RenderArtifact)
                reused_render=cache.reused.count('render')>reused_before
                qa=stage('verify',{'render':object_hash(rendered),'edl':object_hash(edl),'ffmpeg':ffmpeg_identity,'ffprobe':tool_fingerprint(config.ffprobe),'runtime':stage_dependencies('verify')},lambda:verify_render(rendered,source,edl,config.ffprobe,config.ffmpeg,cancelled),ExportValidation)
                atomic_json(revision_dir/'render.json',rendered);atomic_json(revision_dir/'qa.json',qa)
                if not qa.technical_pass: raise PipelineError('EXPORT_INVALID','verify','Technical QA failed; inspect revision QA.')
                row={'revision_id':str(edl.revision_id),'candidate_id':str(candidate.id),'render_path':str(rendered.path),'review_status':'needs_review'}
                if not any(r['revision_id']==row['revision_id'] for r in state.revisions):state.revisions.append(row)
                atomic_json(state_path,state)
                current.update(state='ready',phase='ready',revision_id=str(edl.revision_id),reused=reused_render)
                current=None;report('next')
            except (PipelineError,OSError,ValueError) as exc:
                failed_phase=current.get('phase','edit_plan')
                detail=str(exc)[:1000]
                error_type=type(exc).__name__
                if not isinstance(exc,PipelineError):
                    import traceback
                    (root/(str(candidate.id)+'.error.log')).write_text(traceback.format_exc(),encoding='utf-8')
                    exc=PipelineError('ITEM_FAILED','render','Local preview failed; retry this item.')
                if exc.code=='CANCELLED': raise
                failures.append({'candidate_id':str(candidate.id),'error':{**exc.as_dict(),'detail':detail,'failed_stage':failed_phase,'type':error_type}})
                current.update(state='failed',phase='failed',error_code=exc.code,error_message=detail,error_stage=failed_phase,error_type=error_type);current=None;report('next')
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

def export_approved(project_root:Path,revision_ids=None):
    root=Path(project_root).resolve();state=ProjectRun.model_validate_json((root/'project.json').read_bytes())
    if file_hash(state.source.local_path)!=state.source.sha256: raise PipelineError('SOURCE_CHANGED','export','Source changed.')
    exported=[]
    for revision in state.revisions:
        if revision_ids is not None and revision['revision_id'] not in revision_ids:continue
        folder=root/'revisions'/revision['revision_id']
        if (folder/'deleted.json').is_file():continue
        edl=EDLArtifact.model_validate_json((folder/'edl.json').read_bytes())
        caps=CaptionArtifact.model_validate_json((folder/'captions.json').read_bytes())
        rendered=RenderArtifact.model_validate_json((folder/'render.json').read_bytes())
        qa=ExportValidation.model_validate_json((folder/'qa.json').read_bytes())
        if not qa.technical_pass:
            if revision_ids is not None:
                raise PipelineError('EXPORT_INVALID','export','Render is invalid for this revision.')
            continue
        status,decision=current_review(folder,edl.revision_id,review_fingerprint(root,edl.revision_id),qa.technical_pass)
        if status!='approved':
            if revision_ids is not None:
                raise PipelineError('REVIEW_REQUIRED','export','The requested revision needs current editorial approval.')
            continue
        if rendered.revision_id!=edl.revision_id or caps.edl_revision_id!=edl.revision_id or file_hash(rendered.path)!=rendered.sha256:
            raise PipelineError('EXPORT_INVALID','export','Render is invalid for this revision.')
        package_hash=object_hash({'review':decision,'edl':edl,'caption':caps,'render':rendered})
        target=root/'exports'/revision['revision_id']/package_hash[:16];target.mkdir(parents=True,exist_ok=True)
        if (target/'manifest.json').exists() and json.loads((target/'manifest.json').read_text(encoding='utf-8'))['package_hash']!=package_hash:
            raise PipelineError('EXPORT_CONFLICT','export','Export package prefix collision; full content hash differs.')
        for src,name in [(rendered.path,'clip.mp4'),(caps.ass_path,'captions.ass'),(caps.srt_path,'captions.srt'),(folder/'edl.json','edl.json')]:
            dest=target/name
            if not dest.exists(): shutil.copyfile(src,dest)
            if file_hash(src)!=file_hash(dest): raise PipelineError('EXPORT_INVALID','export','Export checksum mismatch.')
        atomic_json(target/'words.json',caps.words)
        from engine.editorial.social_copy import publication_description
        publication_candidate=json.loads((folder/'candidate.json').read_text(encoding='utf-8'))
        publication={'title':publication_candidate.get('title_suggestion',''),'description':publication_description(publication_candidate.get('description_suggestion',''),publication_candidate.get('title_suggestion',''))}
        atomic_json(target/'metadata.json',{'publication':publication,'schema_version':'1.0','source':state.source,'review':decision,'candidate':json.loads((folder/'candidate.json').read_text(encoding='utf-8')),'opening':{'text':caps.opening_text,'duration_us':caps.opening_duration_us},'caption_revision_id':str(caps.revision_id),'transcript_id':str(edl.transcript_id),'render':rendered,'qa':qa})
        atomic_json(target/'manifest.json',{'schema_version':'1.0','revision_id':revision['revision_id'],'package_hash':package_hash,'files':{p.name:{'sha256':file_hash(p),'bytes':p.stat().st_size} for p in target.iterdir() if p.is_file() and p.name!='manifest.json'}})
        exported.append(str(target))
    if not exported: raise PipelineError('NO_APPROVED_CLIPS','export','No technically valid and editorially approved clips available.')
    return exported
