import importlib.metadata,subprocess,os
from pathlib import Path
from engine.pipeline.artifacts import file_hash,object_hash
from engine.contracts import PipelineError

ROOT=Path(__file__).resolve().parents[2]
FILES={
 'audio':['engine/media/audio.py','engine/pipeline/cancellation.py'],
 'pauses':['engine/media/pauses.py'],
 'transcribe':['engine/adapters/openshorts/transcriber.py','engine/worker.py','vendor/openshorts/transcribe_backends.py','vendor/openshorts/subtitles.py'],
 'analyze':['engine/adapters/gemini/analyzer.py','engine/adapters/gemini/request_worker.py','engine/adapters/gemini/checkpoints.py','engine/adapters/openshorts/windows.py','vendor/openshorts/clip_selection.py'],
 'select':['engine/editorial/select.py'],
 'edit_plan':['engine/editorial/edl.py','vendor/openshorts/recut.py','vendor/openshorts/clip_selection.py'],
 'captions':['engine/render/opening.py','engine/adapters/openshorts/captions.py','vendor/openshorts/subtitles.py','vendor/openshorts/ffmpeg_utils.py'],
 'reframe':['engine/media/face_tracking.py','engine/pipeline/cancellation.py'],
 'render':['engine/media/face_tracking.py','engine/render/ffmpeg.py','engine/pipeline/cancellation.py'],
 'verify':['engine/render/verify.py','engine/media/probe.py']}
PACKAGES={'reframe':['mediapipe','numpy'],'transcribe':['faster-whisper','ctranslate2','av','tokenizers','onnxruntime'],'pauses':['faster-whisper','onnxruntime','numpy'],'analyze':['google-genai','pydantic'],'captions':['pydantic']}

def safe_file_hash(path: Path) -> str:
    try:
        if path.is_file():
            return file_hash(path)
    except Exception:
        pass
    import hashlib
    return hashlib.sha256(f"autoclip-engine:{path.name}".encode('utf-8')).hexdigest()

def stage_dependencies(stage:str) -> dict:
    packages={}
    for name in PACKAGES.get(stage,[]):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]='missing'
    assets={}
    if stage=='pauses':
        try:
            from faster_whisper.utils import get_assets_path
            assets={p.name:file_hash(p) for p in Path(get_assets_path()).glob('*.onnx')}
        except ImportError:pass
    return {'files':{name:safe_file_hash(ROOT/name) for name in FILES[stage]},'packages':packages,'contracts':safe_file_hash(ROOT/'engine/contracts/models.py'),**({'vad_assets':assets} if stage=='pauses' else {})}

def tool_fingerprint(path:Path):
    return {'sha256':file_hash(path),'path':str(path.resolve())}

def resolve_font(path:Path|None,name:str) -> Path:
    if path is not None:
        if not path.is_file():raise PipelineError('FONT_MISSING','captions','Configured font file unavailable.')
        return path.resolve()
    if name.casefold()=='montserrat extrabold':
        bundled=Path(__file__).resolve().parents[1]/'assets/fonts/Montserrat-ExtraBold.ttf'
        if bundled.is_file():return bundled.resolve()
    if os.name=='nt' and name.lower()=='arial':
        p=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/arial.ttf'
        if p.is_file():return p
    raise PipelineError('FONT_MISSING','captions','Provide an explicit locally installed font file.')

def font_fingerprint(path:Path|None,name:str):
    actual=resolve_font(path,name)
    return {'name':name,'path':str(actual),'sha256':file_hash(actual)}
