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


def clip_thumbnail(root, revision_id: str, ffmpeg):
    """Gera e faz cache da thumbnail do corte: primeiro frame do vídeo sem legenda de fala, com título no topo."""
    root = Path(root).resolve()
    from uuid import UUID
    try:
        rid = str(UUID(revision_id))
    except ValueError:
        raise HTTPException(404, 'Corte não encontrado.')
    folder = root / 'revisions' / rid
    if not folder.is_dir():
        raise HTTPException(404, 'Pasta do corte não encontrada.')
    target = folder / 'thumbnail.jpg'
    with _lock:
        if target.is_file():
            return target
        try:
            from engine.contracts import EDLArtifact, Candidate, Source
            edl = EDLArtifact.model_validate_json((folder / 'edl.json').read_bytes())
            candidate = Candidate.model_validate_json((folder / 'candidate.json').read_bytes())
            source = Source.model_validate_json((root / 'source.json').read_bytes())
        except (OSError, ValueError):
            raise HTTPException(404, 'Dados do corte indisponíveis para gerar miniatura.')

        start_seconds = max(0.0, edl.spans[0].source_start_us / 1e6) if edl.spans else 0.0
        raw_title = (candidate.title or 'Corte em Destaque').strip()

        # Quebra de linhas inteligente para largura 9:16 (~26 caracteres por linha)
        words = raw_title.replace('{', '').replace('}', '').split()
        lines = []
        cur = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + (1 if cur else 0) > 26:
                if cur:
                    lines.append(' '.join(cur))
                    cur = [w]
                    cur_len = len(w)
                else:
                    lines.append(w)
                    cur = []
                    cur_len = 0
            else:
                cur.append(w)
                cur_len += len(w) + (1 if len(cur) > 1 else 0)
        if cur:
            lines.append(' '.join(cur))

        formatted_title = '\\N'.join(lines)
        fonts_dir = Path(__file__).resolve().parents[1] / 'assets' / 'fonts'
        font_file = fonts_dir / 'Montserrat-ExtraBold.ttf'

        # Arquivo ASS para overlay estilizado no topo (sem legenda de fala)
        ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Montserrat,68,&H00FFFFFF,&H000000FF,&H0005080E,&HB0000000,-1,0,0,0,100,100,0,0,1,6,3,8,64,64,180,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:01:00.00,Title,,0,0,0,,{{\\b1}}{formatted_title}{{\\b0}}
"""
        random_id = uuid.uuid4().hex
        temporary = folder / f'.thumb-{random_id}.jpg'
        ass_path = folder / f'.thumb-{random_id}.ass'
        try:
            ass_path.write_text(ass_content, encoding='utf-8')
            # Detecta o arquivo de vídeo de entrada (fonte ou preview gerada)
            input_path = source.local_path
            origin_offset = 0.0
            if not Path(input_path).is_file():
                # Fallback para a prévia do corte caso a fonte tenha sido movida
                preview_file = folder / f'preview-{rid}.mp4'
                if not preview_file.is_file():
                    candidates = list(folder.glob('*.mp4'))
                    if candidates:
                        preview_file = candidates[0]
                if preview_file.is_file():
                    input_path = preview_file
                    start_seconds = 0.0

            flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
            ass_escaped = ass_path.name.replace(':', '\\:').replace("'", "\\'")
            fonts_escaped = fonts_dir.as_posix().replace(':', '\\:').replace("'", "\\'")
            vf = f"scale=1080:1920:force_original_aspect_ratio=increase:force_divisible_by=2,crop=1080:1920:(iw-1080)/2:(ih-1920)/2,ass=filename='{ass_escaped}':fontsdir='{fonts_escaped}'"

            cmd = [
                str(ffmpeg),
                '-hide_banner',
                '-loglevel', 'error',
                '-ss', f'{start_seconds:.3f}',
                '-i', str(input_path),
                '-frames:v', '1',
                '-vf', vf,
                '-q:v', '2',
                '-y', str(temporary)
            ]
            res = subprocess.run(cmd, cwd=folder, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25, **flags)
            if res.returncode or not temporary.is_file():
                # Fallback sem o filtro ass caso a libass não esteja disponível no binário
                cmd_fallback = [
                    str(ffmpeg),
                    '-hide_banner',
                    '-loglevel', 'error',
                    '-ss', f'{start_seconds:.3f}',
                    '-i', str(input_path),
                    '-frames:v', '1',
                    '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase:force_divisible_by=2,crop=1080:1920:(iw-1080)/2:(ih-1920)/2',
                    '-q:v', '2',
                    '-y', str(temporary)
                ]
                res_fallback = subprocess.run(cmd_fallback, cwd=folder, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25, **flags)
                if res_fallback.returncode or not temporary.is_file():
                    raise HTTPException(404, 'Não foi possível gerar miniatura do corte.')
            temporary.replace(target)
        except (OSError, subprocess.TimeoutExpired):
            raise HTTPException(404, 'Tempo limite ou erro ao gerar miniatura do corte.') from None
        finally:
            ass_path.unlink(missing_ok=True)
            temporary.unlink(missing_ok=True)
    return target
