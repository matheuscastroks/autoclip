from uuid import UUID
from typing import Literal
from pathlib import Path
import json
from engine.contracts import ReviewDecision,EditorialChecks
from engine.contracts.api import RevisionReviewStatus
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


def current_review(folder:Path,revision_id:UUID,content_hash:str,technical_pass:bool) -> tuple[RevisionReviewStatus,ReviewDecision|None]:
    if not technical_pass:
        return 'invalid',None
    review_path=Path(folder)/'review.json'
    if not review_path.exists():
        return 'needs_review',None
    try:
        decision=ReviewDecision.model_validate_json(review_path.read_bytes())
    except (OSError,ValueError):
        return 'stale_review',None
    if decision.revision_id!=revision_id or decision.content_hash!=content_hash:
        return 'stale_review',decision
    return decision.decision,decision
