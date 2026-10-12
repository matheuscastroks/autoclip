import os,threading
from pathlib import Path
from fastapi import HTTPException

_picker_lock=threading.Lock()

def pick(kind:str)->str|None:
    if kind not in ('video','project','model','ffmpeg','ffprobe'):raise ValueError('Seletor desconhecido.')
    if not _picker_lock.acquire(blocking=False):raise HTTPException(409,'Já existe uma janela de seleção aberta.')
    root=None
    try:
        import tkinter as tk
        from tkinter import filedialog
        root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
        if kind in ('project','model'):
            value=filedialog.askdirectory(parent=root,title='Escolher pasta de '+('projeto' if kind=='project' else 'modelo Whisper'))
        elif kind=='video':
            value=filedialog.askopenfilename(parent=root,title='Escolher vídeo',filetypes=[('Vídeos','*.mp4 *.mov *.mkv *.webm *.avi'),('Todos','*.*')])
        else:value=filedialog.askopenfilename(parent=root,title='Localizar '+kind,filetypes=[('Executável','*.exe'),('Todos','*.*')])
        return str(Path(value).resolve()) if value else None
    except HTTPException:raise
    except Exception:raise HTTPException(503,'Não foi possível abrir o seletor de arquivos nesta sessão do Windows.') from None
    finally:
        if root:root.destroy()
        _picker_lock.release()

def open_directory(path:Path):
    path=Path(path).resolve()
    if not path.is_dir():raise ValueError('Pasta indisponível.')
    if os.name!='nt':raise HTTPException(503,'Abrir pasta está disponível no Windows.')
    os.startfile(str(path))
