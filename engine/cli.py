import argparse,getpass,json,sys,os
from pathlib import Path
from engine.contracts import *
from engine.media.importer import import_source
from engine.media.probe import locate_tools
from engine.adapters.openshorts.transcriber import configure_utf8
from engine.adapters.gemini.credentials import set_gemini_key,get_gemini_key
from engine.pipeline.runner import run_project,resume_project,export_approved
from engine.pipeline.artifacts import atomic_json,file_hash
from engine.editorial.review import record_review,review_fingerprint
from engine.editorial.report import create_report

def main(argv=None):
    configure_utf8()
    parser=argparse.ArgumentParser(description='OpenShorts-based CPU media pipeline with text-only Gemini analysis.')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    auth=sub.add_parser('auth');auth.add_argument('action',choices=['set-gemini-key'])
    run=sub.add_parser('run');run.add_argument('source');run.add_argument('--project',type=Path,required=True);run.add_argument('--model',required=True);run.add_argument('--max-calls',type=int,required=True);run.add_argument('--offline',action='store_true');run.add_argument('--asr-model',type=Path,default=Path('research/models/whisper-small'))
    run.add_argument('--preferred-seconds',type=int,default=180);run.add_argument('--max-clip-seconds',type=int,default=300);run.add_argument('--shorten-pauses',action='store_true')
    resume=sub.add_parser('resume');resume.add_argument('--project',type=Path,required=True);resume.add_argument('--model');resume.add_argument('--max-calls',type=int);resume.add_argument('--offline',action=argparse.BooleanOptionalAction,default=None)
    for name in ['review','export']:
        p=sub.add_parser(name);p.add_argument('--project',type=Path,required=True)
    approve=sub.add_parser('approve');approve.add_argument('revision');approve.add_argument('--project',type=Path,required=True)
    a=parser.parse_args(argv)
    try:
        if a.command=='doctor':
            try: ffmpeg,ffprobe=locate_tools();tools={'ffmpeg':str(ffmpeg),'ffprobe':str(ffprobe)}
            except PipelineError:tools={'ffmpeg':None,'ffprobe':None}
            try:get_gemini_key();key=True
            except PipelineError:key=False
            print(json.dumps({'python':sys.version.split()[0],'tools':tools,'gemini_key_configured':key,'mode':'CPU ASR/render; Gemini analysis uses text only','asr_model_exists':Path('research/models/whisper-small/model.bin').exists()},ensure_ascii=False,indent=2));return 0
        if a.command=='auth':
            secret=getpass.getpass('Chave Gemini (entrada oculta, armazenada no Credential Manager): ')
            set_gemini_key(secret);print('Credencial armazenada localmente.');return 0
        root=a.project.resolve()
        if a.command=='run':
            ffmpeg,ffprobe=locate_tools()
            if (root/'source.json').exists():
                source=Source.model_validate_json((root/'source.json').read_bytes())
                requested=Path(a.source).expanduser().resolve()
                if a.source.startswith(('https://','http://')):
                    if source.original_url!=a.source: raise PipelineError('SOURCE_CHANGED','run','Project belongs to a different source URL.')
                elif requested!=source.local_path or file_hash(requested)!=source.sha256:
                    raise PipelineError('SOURCE_CHANGED','run','Use a new project for a changed source.')
            else:source=import_source(a.source,root)
            config=PipelineConfig(asr=ASRConfig(model_path=a.asr_model.resolve()),analysis=AnalysisConfig(clip_min_seconds=60,model=a.model,max_calls=a.max_calls,offline=a.offline,clip_preferred_seconds=a.preferred_seconds,clip_max_seconds=a.max_clip_seconds),selection=SelectionConfig(max_us=a.max_clip_seconds*1_000_000),pauses=PauseConfig(enabled=a.shorten_pauses),export=ExportConfig(output_root=root/'previews'),ffmpeg=ffmpeg,ffprobe=ffprobe)
            from engine.adapters.gemini.analyzer import GeminiAnalyzer
            analyzer=GeminiAnalyzer(work_root=root/'work',events_path=root/'analysis-events.jsonl')
            state=run_project(source,config,root,analyzer=analyzer);print(f'Project: {root}\nStatus: {state.status}')
            if state.revisions: print('Review report:',create_report(root))
            return 0 if state.status!='failed' else 1
        if a.command=='resume':
            config=PipelineConfig.model_validate_json((root/'config.json').read_bytes())
            if a.model:config.analysis.model=a.model
            if a.max_calls:config.analysis.max_calls=a.max_calls
            if a.offline is not None:config.analysis.offline=a.offline
            state=resume_project(root,config);print('Status:',state.status)
            if state.revisions:print('Review report:',create_report(root))
            return 0 if state.status!='failed' else 1
        if a.command=='review':print(create_report(root));return 0
        if a.command=='approve':
            revision=__import__('uuid').UUID(a.revision)
            folder=root/'revisions'/str(revision)
            e=EDLArtifact.model_validate_json((folder/'edl.json').read_bytes())
            qa=ExportValidation.model_validate_json((folder/'qa.json').read_bytes())
            if not qa.technical_pass:raise PipelineError('EXPORT_INVALID','review','Technical QA must pass first.')
            print('Confirme somente depois de ouvir o original com contexto e o corte completo.')
            prompts={'completeness':'Pensamento completo?', 'context':'Compreensível fora do vídeo?', 'qualifications':'Negações, números e ressalvas preservados?', 'words_and_boundaries':'Nenhuma palavra ou argumento cortado?', 'audiovisual':'Áudio, quadro e legenda revisados?'}
            answers={key:input(question+' [s/N]: ').strip().lower()=='s' for key,question in prompts.items()}
            decision='approved' if all(answers.values()) else 'rejected'
            review=record_review(revision,decision,EditorialChecks(**answers),input('Notas da revisão: '),review_fingerprint(root,revision))
            atomic_json(folder/'review.json',review)
            state=ProjectRun.model_validate_json((root/'project.json').read_bytes())
            for item in state.revisions:
                if item['revision_id']==str(revision):item['review_status']=decision
            atomic_json(root/'project.json',state);print('Decision:',decision);return 0
        if a.command=='export':
            print('\n'.join(export_approved(root)));return 0
    except KeyboardInterrupt:
        print('Cancelado. Etapas concluídas continuam disponíveis para resume.',file=sys.stderr);return 130
    except PipelineError as exc:
        print(f'{exc.code}: {exc}',file=sys.stderr);return 1
    except (FileNotFoundError,ValueError) as exc:
        print(f'INVALID_PROJECT: {exc}',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
