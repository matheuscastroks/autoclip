import hashlib,hmac,time
from pathlib import Path
from fastapi import HTTPException
from engine.contracts import Source
from .projects import read_json

def asset_path(root:Path,asset:str)->Path:
    root=Path(root).resolve()
    if asset=='source':
        try:path=Source.model_validate_json((root/'source.json').read_bytes()).local_path.resolve()
        except (ValueError,OSError):raise HTTPException(404,'Vídeo original indisponível.')
    else:
        if asset=='manual':
            if not (root/'manual-check.json').is_file():raise HTTPException(404,'Prévia manual indisponível.')
            options=list((root/'previews').glob('*.mp4'));path=options[0].resolve() if options else root/'missing'
        else:
            state=read_json(root/'project.json',{}) or {}
            item=next((i for i in state.get('revisions',[]) if i.get('revision_id')==asset),None)
            if not item:raise HTTPException(404,'Prévia indisponível.')
            path=Path(item.get('render_path','')).resolve()
        if not path.is_relative_to(root):raise HTTPException(404,'Arquivo fora do projeto.')
    if not path.is_file():raise HTTPException(404,'Arquivo de vídeo não encontrado.')
    return path

def signature(token,pid,asset,expires):
    return hmac.new(token.encode(),f'{pid}/{asset}/{expires}'.encode(),hashlib.sha256).hexdigest()

def make_ticket(token,pid,asset):
    expires=int(time.time())+3600
    return f'/api/v1/projects/{pid}/media/{asset}?expires={expires}&ticket={signature(token,pid,asset,expires)}'

def valid_ticket(token,pid,asset,expires,ticket):
    try:
        return int(expires)>=time.time() and int(expires)<=time.time()+3601 and hmac.compare_digest(ticket,signature(token,pid,asset,expires))
    except (ValueError,TypeError):return False
