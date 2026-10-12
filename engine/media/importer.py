from pathlib import Path
from urllib.parse import urlparse
from engine.contracts import Source, PipelineError
from engine.pipeline.artifacts import file_hash, atomic_json


def _download(url: str, root: Path):
    import yt_dlp
    import shutil
    opts={'format':'bv*[height<=720]+ba/best','outtmpl':str(root/'source.%(ext)s'),'noplaylist':True,'writeinfojson':True,'retries':1,'socket_timeout':20}
    node=shutil.which('node')
    if node: opts['js_runtimes']={'node':{'path':node}}
    from .probe import locate_tools
    ffmpeg,_=locate_tools()
    opts['ffmpeg_location']=str(ffmpeg.parent)
    opts['merge_output_format']='mp4'
    with yt_dlp.YoutubeDL(opts) as dl:
        info=dl.extract_info(url,download=True)
        paths=[root/'source.mp4',Path(dl.prepare_filename(info))]
        file=next((p for p in paths if p.is_file() and p.stat().st_size>0),None)
        if file is None: raise RuntimeError('Downloaded file unavailable')
        return file,info

def import_source(input_value: str,project_root: Path) -> Source:
    project_root=Path(project_root).resolve(); project_root.mkdir(parents=True,exist_ok=True)
    url=urlparse(input_value)
    try:
        if url.scheme in ('https','http'):
            if url.hostname not in {'youtube.com','www.youtube.com','youtu.be'}:
                raise ValueError('PoC URL support is limited to YouTube; use local file.')
            folder=project_root/'input'; folder.mkdir(exist_ok=True)
            path,info=_download(input_value,folder)
            source=Source(sha256=file_hash(path),local_path=path.resolve(),kind='url',original_url=input_value,original_title=info.get('title',''),channel=info.get('channel',''))
        else:
            path=Path(input_value).expanduser().resolve()
            if not path.is_file() or path.stat().st_size==0: raise ValueError('Source missing or empty.')
            source=Source(sha256=file_hash(path),local_path=path,original_title=path.stem)
            # Preserve source attribution when importing the downloaded test file.
            sidecar=path.with_suffix('.info.json')
            if sidecar.exists():
                import json
                info=json.loads(sidecar.read_text(encoding='utf-8'))
                source.original_url=info.get('webpage_url'); source.original_title=info.get('title',path.stem); source.channel=info.get('channel','')
        source.attribution=' — '.join(p for p in [source.channel,source.original_title,source.original_url] if p)
        atomic_json(project_root/'source.json',source)
        return source
    except Exception as exc:
        if isinstance(exc,PipelineError): raise
        raise PipelineError('SOURCE_UNAVAILABLE','ingest','Unable to import source. '+str(exc)) from exc
