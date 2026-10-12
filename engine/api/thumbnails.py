"""Small local cover, cached by source content hash."""
import os,subprocess,threading,uuid
from pathlib import Path
from fastapi import HTTPException
from engine.contracts import Source

_lock=threading.Lock()

def thumbnail(root,ffmpeg):
    root=Path(root)
    try:source=Source.model_validate_json((root/'source.json').read_bytes())
    except (OSError,ValueError):raise HTTPException(404,'Capa ainda indisponível.')
    target=root/'covers'/(source.sha256+'.jpg')
    with _lock:
        if target.is_file():return target
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_name(uuid.uuid4().hex+'.jpg')
        try:
            seconds=min(5,max(0,source.duration_us/1e6/10))
            result=subprocess.run([str(ffmpeg),'-hide_banner','-loglevel','error','-ss',str(seconds),'-i',str(source.local_path),'-frames:v','1','-vf','scale=320:-2','-q:v','4','-y',str(temporary)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=25,**({'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}))
            if result.returncode or not temporary.is_file():raise HTTPException(404,'Capa indisponível.')
            temporary.replace(target)
        except (OSError,subprocess.TimeoutExpired):raise HTTPException(404,'Capa indisponível.') from None
        finally:temporary.unlink(missing_ok=True)
    return target
