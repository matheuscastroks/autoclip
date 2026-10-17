import importlib.metadata,subprocess,os
from pathlib import Path
from engine.pipeline.artifacts import file_hash,object_hash
from engine.contracts import PipelineError

ROOT=Path(__file__).resolve().parents[2]
# Exact (reviewed telemetry contents, e7febcf baseline) pairs. Unknown changes always
# receive their actual digest; this is not a general cache-version bypass.
TELEMETRY_COMPATIBILITY={
    'engine/media/audio.py': ('37321262f012669d06298c1c6db06db6c422032103512dca562abd056a9f5fe3', 'cc6a07199dcb8055a853a6f44eee688cfdf6223fb9fe09565ba99f1ce33a316d'),
    'engine/worker.py': ('402fd6b5b1a15de2197b77e4fba72c113ca06e4bbf9e282c6dfa5af549a516c6', 'bb668ee28c693a3d870e09d5e13cb9e365ab481de1939d4f5262050afa04c356'),
    'engine/adapters/openshorts/transcriber.py': ('90f437df3f0372b5e1621a7a407b033c3f791578639c36709478d0058bbc1af6', '94d79fe3ce8e3eed4cb4ba67f1970ed353768144776ecd3a4d9746e7fcc4e477'),
    'engine/render/verify.py': ('03285901ec3d7fe08aa136d1fe350076a2098eb90c3ac5dda6e5c8b62e0b4b05', '67b0779af0fddd4771536292e049adb2068d2ca6aa97119a96a415dcccc25ba5'),
    'engine/media/face_tracking.py': ('388520f86f12b86107f39af569e75a9c5754597b9892859dde38a92ee6975ea7', 'd31c259714221604c1caa5f7b3e3492a659aa597b77c24522d28f421d3588c7f'),
    'engine/pipeline/cancellation.py': ('959c7bb5e57299df79d98763385ed835c503ff1ef258da52316dd671b8559431', '62758d93d439e97e54973dcfcaecaa0ec01c85537e53c1ab6501d683fa1a0a3b'),
}


def media_code_hash(name,digest):
    reviewed=TELEMETRY_COMPATIBILITY.get(name)
    return reviewed[1] if reviewed and digest==reviewed[0] else digest

FILES={
 'audio':['engine/media/audio.py','engine/pipeline/cancellation.py'],
 'pauses':['engine/media/pauses.py'],
 'transcribe':['engine/adapters/openshorts/transcriber.py','engine/worker.py','vendor/openshorts/transcribe_backends.py','vendor/openshorts/subtitles.py'],
 'analyze':['engine/adapters/gemini/analyzer.py','engine/adapters/gemini/request_worker.py','engine/adapters/gemini/checkpoints.py','engine/adapters/openshorts/windows.py','vendor/openshorts/clip_selection.py'],
 'select':['engine/editorial/select.py'],
 'edit_plan':['engine/editorial/edl.py','vendor/openshorts/recut.py','vendor/openshorts/clip_selection.py'],
 'captions':['engine/render/presets.py','engine/render/opening.py','engine/adapters/openshorts/captions.py','vendor/openshorts/subtitles.py','vendor/openshorts/ffmpeg_utils.py'],
 'reframe':['engine/media/face_tracking.py','engine/pipeline/cancellation.py'],
 'render':['engine/media/face_tracking.py','engine/render/ffmpeg.py','engine/pipeline/cancellation.py'],
 'verify':['engine/render/verify.py','engine/media/probe.py']}
PACKAGES={'reframe':['mediapipe','numpy'],'transcribe':['faster-whisper','ctranslate2','av','tokenizers','onnxruntime'],'pauses':['faster-whisper','onnxruntime','numpy'],'analyze':['google-genai','pydantic'],'captions':['pydantic']}

def safe_file_hash(path: Path) -> str:
    try:
        if path.is_file():
            digest=file_hash(path)
            name=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else ''
            return media_code_hash(name,digest)
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
