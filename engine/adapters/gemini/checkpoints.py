"""Only complete, validated window responses can become durable checkpoints."""
import json
from pathlib import Path
from engine.pipeline.artifacts import atomic_json,object_hash

def load_checkpoint(root:Path|None,key:str):
    if root is None:return None
    try:
        row=json.loads((root/(key+'.json')).read_text(encoding='utf-8'))
        digest=row.pop('sha256')
        if row.get('checkpoint_version')!=1 or row.get('key')!=key or object_hash(row)!=digest:return None
        return row
    except (OSError,ValueError,KeyError,TypeError,AttributeError):return None

def save_checkpoint(root:Path|None,key:str,response,provenance,payload_hashes):
    if root is None:return
    row={'checkpoint_version':1,'key':key,'response':response.model_dump(mode='json'),'provenance':provenance,'payload_hashes':payload_hashes}
    atomic_json(root/(key+'.json'),{**row,'sha256':object_hash(row)})
