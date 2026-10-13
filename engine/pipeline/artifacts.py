import hashlib, json, os, uuid, time
from pathlib import Path
from pydantic import BaseModel
from engine.contracts import ArtifactRef, PipelineError


def canonical(value) -> bytes:
    if isinstance(value,BaseModel): value=value.model_dump(mode='json')
    def encode(item):
        if isinstance(item,BaseModel): return item.model_dump(mode='json')
        if isinstance(item,(Path,uuid.UUID)): return str(item)
        raise TypeError(f'Unsupported JSON type: {type(item).__name__}')
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False,default=encode).encode('utf-8')

def file_hash(path: Path) -> str:
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def object_hash(value) -> str: return hashlib.sha256(canonical(value)).hexdigest()

def confined(root: Path, relative: str) -> Path:
    root=Path(root).resolve()
    p=(root/relative).resolve()
    if not p.is_relative_to(root): raise PipelineError('UNSAFE_PATH','storage','Path escapes project root.')
    return p

def atomic_bytes(path: Path, data: bytes):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(uuid.uuid4().hex[:16]+'.partial')
    try:
        with temp.open('xb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        # Windows readers/antivirus can temporarily deny replacement of a file
        # opened by polling. Preserve atomicity and fail boundedly on real errors.
        for attempt in range(10):
            try:os.replace(temp,path);break
            except PermissionError as exc:
                if getattr(exc,'winerror',None) not in (5,32) or attempt==9:raise
                time.sleep(min(.01*2**attempt,.1))
    finally:
        temp.unlink(missing_ok=True)

def atomic_json(path: Path, value): atomic_bytes(path,canonical(value))

def write_artifact(payload: BaseModel,kind: str,root: Path) -> ArtifactRef:
    if not kind.replace('_','').isalnum(): raise ValueError('invalid artifact kind')
    data=canonical(payload); digest=hashlib.sha256(data).hexdigest()
    relative=f'artifacts/{kind}/{digest}.json'
    p=confined(root,relative)
    if not p.exists() or file_hash(p)!=digest: atomic_bytes(p,data)
    return ArtifactRef(kind=kind,relative_path=relative,sha256=digest,size_bytes=len(data))

def read_artifact(ref: ArtifactRef,root: Path,model):
    p=confined(root,ref.relative_path)
    if not p.is_file() or p.stat().st_size!=ref.size_bytes or file_hash(p)!=ref.sha256:
        raise PipelineError('CORRUPT_ARTIFACT','storage','Artifact checksum or size mismatch.')
    return model.model_validate_json(p.read_bytes())
