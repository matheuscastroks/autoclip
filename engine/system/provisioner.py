import os
import shutil
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, Callable
from engine.pipeline.telemetry import stamp

def get_storage_base() -> Path:
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        return Path(localappdata) / "AutoClip"
    return Path.home() / ".autoclip"

GYAN_FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

MODEL_MAP = {
    "Systran/faster-whisper-base": "whisper-base",
    "Systran/faster-whisper-small": "whisper-small",
    "Systran/faster-whisper-large-v3-turbo": "whisper-large-v3-turbo",
}

MODEL_FILES = ["config.json", "tokenizer.json", "vocabulary.txt", "model.bin"]

class DependencyProvisioner:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or get_storage_base()
        self.tools_dir = self.base_dir / "bin"
        self.models_dir = self.base_dir / "models"
        self._lock = threading.Lock()
        self._cancel_event = threading.Event()
        self._cancelled = False
        self._active_tmp_file: Optional[Path] = None
        self._thread: Optional[threading.Thread] = None

        self._state = {
            "status": "idle",
            "stage": "idle",
            "item": "",
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "speed_bps": 0.0,
            "percent": None,
            "heartbeat_at": None,
            "eta_seconds": None,
            "completed_units": None,
            "total_units": None,
            "error": None,
            "model_path": None,
            "ffmpeg_path": None,
            "ffprobe_path": None
        }

    def status(self) -> dict:
        with self._lock:
            return dict(self._state)

    def cancel(self):
        with self._lock:
            self._cancel_event.set()
            self._cancelled = True
            if self._thread and self._thread.is_alive():
                self._state["status"] = "cancelling"
                self._state["stage"] = "cancelling"
            else:
                self._state["status"] = "cancelled"
                self._state["stage"] = "cancelled"
                if self._active_tmp_file and self._active_tmp_file.exists():
                    try:
                        self._active_tmp_file.unlink()
                    except OSError:
                        pass
                    self._active_tmp_file = None
            self._state["error"] = "Operação cancelada pelo usuário."

    def start(self, model_id: str, install_ffmpeg: bool = True):
        with self._lock:
            if (self._thread and self._thread.is_alive()) or self._state["status"] in ("downloading", "extracting", "cancelling"):
                raise RuntimeError("Provisioning already in progress")
            self._cancel_event.clear()
            self._cancelled = False
            self._active_tmp_file = None
            self._state.update({
                "status": "downloading",
                "stage": "starting",
                "item": "",
                "downloaded_bytes": 0,
                "total_bytes": 0,
                "speed_bps": 0.0,
                "percent": None,
                "heartbeat_at": stamp(),
                "eta_seconds": None,
                "error": None
            })

        self._thread = threading.Thread(
            target=self._run_provision,
            args=(model_id, install_ffmpeg),
            daemon=True
        )
        self._thread.start()
        return self.status()

    def _extract_ffmpeg_zip(self, zip_path: Path, tools_dir: Path):
        tools_dir.mkdir(parents=True, exist_ok=True)
        from uuid import uuid4
        pending=[]
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                members=[m for m in zf.infolist() if '/bin/' in m.filename.lower().replace('\\','/') and m.filename.lower().replace('\\','/').split('/')[-1] in ('ffmpeg','ffmpeg.exe','ffprobe','ffprobe.exe')]
                total=sum(m.file_size for m in members);done=0
                for member in members:
                    target=tools_dir/member.filename.lower().replace('\\','/').split('/')[-1]
                    temp=tools_dir/(uuid4().hex+'.partial')
                    pending.append((temp,target))
                    with zf.open(member) as src,temp.open('xb') as dst:
                        while chunk:=src.read(128*1024):
                            if self._cancel_event.is_set():raise RuntimeError('Extraction cancelled')
                            dst.write(chunk);done+=len(chunk)
                            with self._lock:
                                self._state.update(percent=round(done/total*100,1) if total else None,
                                                   completed_units=done,total_units=total or None,
                                                   heartbeat_at=stamp(),eta_seconds=None)
            if self._cancel_event.is_set():raise RuntimeError('Extraction cancelled')
            for temp,target in pending:temp.replace(target)
        finally:
            for temp,_ in pending:temp.unlink(missing_ok=True)

        try:
            zip_path.unlink()
        except OSError:
            pass

    def _download_file(self, url: str, target_path: Path, item_name: str):
        target_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = target_path.with_name(target_path.name + ".tmp")

        with self._lock:
            self._active_tmp_file = tmp_path
            self._state["item"] = item_name
            self._state.update(percent=None,downloaded_bytes=0,total_bytes=0,
                               completed_units=None,total_units=None,eta_seconds=None,heartbeat_at=stamp())

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AutoClip-Desktop/1.0 (Windows; x64)"}
        )

        with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, "wb") as out_f:
            total = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            start_time = time.time()
            chunk_size = 128 * 1024

            while True:
                if self._cancel_event.is_set():
                    raise RuntimeError("Download cancelled")

                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_f.write(chunk)
                downloaded += len(chunk)
                elapsed = max(0.001, time.time() - start_time)
                speed = downloaded / elapsed

                pct = min(100,round((downloaded / total * 100), 1)) if total > 0 else None

                with self._lock:
                    self._state["downloaded_bytes"] = downloaded
                    self._state["total_bytes"] = total
                    self._state["speed_bps"] = speed
                    self._state["percent"] = pct
                    self._state.update(completed_units=downloaded,total_units=total or None,
                                       heartbeat_at=stamp(),eta_seconds=max(0,(total-downloaded)/speed) if total and elapsed>=10 and speed>0 else None)

        if not self._cancel_event.is_set() and tmp_path.exists():
            if target_path.exists():
                target_path.unlink()
            tmp_path.rename(target_path)

        with self._lock:
            self._active_tmp_file = None

    def _run_provision(self, model_id: str, install_ffmpeg: bool):
        try:
            exe_ext = ".exe" if os.name == "nt" else ""
            ffmpeg_bin = self.tools_dir / f"ffmpeg{exe_ext}"
            ffprobe_bin = self.tools_dir / f"ffprobe{exe_ext}"

            # Step 1: FFmpeg provisioning if requested
            if install_ffmpeg and not (ffmpeg_bin.is_file() and ffprobe_bin.is_file()):
                with self._lock:
                    self._state["stage"] = "ffmpeg"
                zip_path = self.tools_dir / "ffmpeg-download.zip"
                self._download_file(GYAN_FFMPEG_URL, zip_path, "FFmpeg Essentials")

                if self._cancel_event.is_set():
                    return

                with self._lock:
                    self._state["stage"] = "extracting_ffmpeg"
                    self._state["item"] = "Extraindo ferramentas de áudio e vídeo..."
                self._extract_ffmpeg_zip(zip_path, self.tools_dir)

            # Step 2: Hugging Face Whisper weights provisioning
            folder_name = MODEL_MAP.get(model_id, model_id.split("/")[-1])
            model_target_dir = self.models_dir / folder_name

            with self._lock:
                self._state["stage"] = "whisper"

            for fname in MODEL_FILES:
                if self._cancel_event.is_set():
                    return
                file_dest = model_target_dir / fname
                if not file_dest.exists():
                    url = f"https://huggingface.co/{model_id}/resolve/main/{fname}"
                    self._download_file(url, file_dest, f"Whisper {folder_name}: {fname}")

            if self._cancel_event.is_set():
                return

            with self._lock:
                self._state.update({
                    "status": "ready",
                    "stage": "done",
                    "item": "Concluído",
                    "percent": 100.0,
                    "model_path": str(model_target_dir),
                    "ffmpeg_path": str(ffmpeg_bin) if ffmpeg_bin.exists() else None,
                    "ffprobe_path": str(ffprobe_bin) if ffprobe_bin.exists() else None
                })

        except Exception as exc:
            with self._lock:
                if not self._cancel_event.is_set():
                    self._state["status"] = "failed"
                    self._state["stage"] = "error"
                    self._state["error"] = str(exc)
        finally:
            with self._lock:
                if self._cancel_event.is_set():
                    self._state["status"] = "cancelled"
                    self._state["stage"] = "cancelled"
                    self._state["error"] = "Operação cancelada pelo usuário."
                if self._active_tmp_file and self._active_tmp_file.exists():
                    try:
                        self._active_tmp_file.unlink()
                    except OSError:
                        pass
                    self._active_tmp_file = None
