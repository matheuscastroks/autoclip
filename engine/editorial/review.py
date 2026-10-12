from uuid import UUID
from typing import Literal
from pathlib import Path
import json
from engine.contracts import ReviewDecision,EditorialChecks
from engine.pipeline.artifacts import file_hash,object_hash

def review_fingerprint(project_root:Path,revision_id:UUID) -> str:
    folder=Path(project_root)/'revisions'/str(revision_id)
    inputs={name:file_hash(folder/(name+'.json')) for name in ['edl','candidate','captions','render','qa']}
    captions=json.loads((folder/'captions.json').read_text(encoding='utf-8'))
    for field in ['ass_path','srt_path']:
        if field in captions: inputs[field]=file_hash(Path(captions[field]))
    source=Path(project_root)/'source.json'
    if source.exists(): inputs['source']=file_hash(source)
    return object_hash(inputs)

def record_review(revision_id:UUID,decision:Literal['approved','rejected'],checks:EditorialChecks,notes:str,content_hash:str|None=None) -> ReviewDecision:
    return ReviewDecision(revision_id=revision_id,decision=decision,checks=checks,notes=notes,content_hash=content_hash)
