import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from engine.system.provisioner import DependencyProvisioner, get_storage_base


@pytest.mark.parametrize('length, expected', [(None, None), ('6', 100.0)])
def test_download_progress_does_not_invent_unknown_size(tmp_path, monkeypatch, length, expected):
    from io import BytesIO
    class Response(BytesIO):
        headers = {'Content-Length': length} if length else {}
    monkeypatch.setattr('urllib.request.urlopen', lambda *args, **kwargs: Response(b'abcdef'))
    prov = DependencyProvisioner(base_dir=tmp_path)
    prov._download_file('https://example.invalid/synthetic', tmp_path / 'file.bin', 'Synthetic')
    assert (tmp_path / 'file.bin').read_bytes() == b'abcdef'
    assert prov.status()['percent'] == expected
    assert prov.status()['downloaded_bytes'] == 6
    assert prov.status()['heartbeat_at']


def test_extraction_reports_actual_uncompressed_bytes(tmp_path):
    import zipfile
    prov = DependencyProvisioner(base_dir=tmp_path)
    archive = tmp_path / 'tools.zip'
    with zipfile.ZipFile(archive, 'w') as stream:
        stream.writestr('test/bin/ffmpeg.exe', b'a' * 16)
        stream.writestr('test/bin/ffprobe.exe', b'b' * 8)
    prov._extract_ffmpeg_zip(archive, tmp_path / 'bin')
    assert prov.status()['completed_units'] == 24
    assert prov.status()['total_units'] == 24
    assert prov.status()['percent'] == 100


def test_cancelled_extraction_never_truncates_installed_tools(tmp_path):
    import zipfile
    prov=DependencyProvisioner(base_dir=tmp_path)
    tools=tmp_path/'bin';tools.mkdir()
    installed=tools/'ffmpeg.exe';installed.write_bytes(b'previous-valid-tool')
    archive=tmp_path/'tools.zip'
    with zipfile.ZipFile(archive,'w') as stream:
        stream.writestr('test/bin/ffmpeg.exe',b'new-tool')
        stream.writestr('test/bin/ffprobe.exe',b'new-probe')
    prov._cancel_event.set()
    with pytest.raises(RuntimeError):
        prov._extract_ffmpeg_zip(archive,tools)
    assert installed.read_bytes()==b'previous-valid-tool'
    assert not (tools/'ffprobe.exe').exists()
    assert not list(tools.glob('*.partial'))

def test_get_storage_base_uses_localappdata(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    base = get_storage_base()
    assert base == tmp_path / "AutoClip"

def test_provisioner_rejects_concurrent_jobs(tmp_path):
    prov = DependencyProvisioner(base_dir=tmp_path)
    prov._state["status"] = "downloading"
    with pytest.raises(RuntimeError, match="Provisioning already in progress"):
        prov.start("Systran/faster-whisper-base", install_ffmpeg=False)

def test_provisioner_cancellation_cleans_tmp_files(tmp_path):
    prov = DependencyProvisioner(base_dir=tmp_path)
    tmp_file = tmp_path / "test.tmp"
    tmp_file.write_text("partial data")
    prov._active_tmp_file = tmp_file
    prov.cancel()
    assert not tmp_file.exists()
    assert prov.status()["status"] == "cancelled"

def test_provisioner_ffmpeg_extracts_binaries(tmp_path):
    prov = DependencyProvisioner(base_dir=tmp_path)
    import zipfile
    zip_path = tmp_path / "ffmpeg_test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("ffmpeg-6.0-essentials_build/bin/ffmpeg.exe", b"dummy_ffmpeg")
        zf.writestr("ffmpeg-6.0-essentials_build/bin/ffprobe.exe", b"dummy_ffprobe")
        zf.writestr("ffmpeg-6.0-essentials_build/doc/readme.txt", b"dummy_doc")
    
    tools_dir = tmp_path / "bin"
    prov._extract_ffmpeg_zip(zip_path, tools_dir)
    assert (tools_dir / "ffmpeg.exe").read_bytes() == b"dummy_ffmpeg"
    assert (tools_dir / "ffprobe.exe").read_bytes() == b"dummy_ffprobe"
    assert not (tools_dir / "readme.txt").exists()

def test_provisioner_thread_lifecycle_and_cancellation(tmp_path):
    import time
    import threading
    prov = DependencyProvisioner(base_dir=tmp_path)
    
    started = threading.Event()
    unblock = threading.Event()

    def mock_run(model_id, install_ffmpeg):
        prov._active_tmp_file = tmp_path / "mock.tmp"
        prov._active_tmp_file.write_text("downloading...")
        started.set()
        while not prov._cancel_event.is_set():
            time.sleep(0.01)
        # Simulate finally block
        if prov._active_tmp_file and prov._active_tmp_file.exists():
            prov._active_tmp_file.unlink()
        prov._state["status"] = "cancelled"

    prov._run_provision = mock_run
    prov.start("Systran/faster-whisper-base", install_ffmpeg=False)
    assert started.wait(timeout=2.0)

    # While thread is running, start() must raise
    with pytest.raises(RuntimeError, match="Provisioning already in progress"):
        prov.start("Systran/faster-whisper-base", install_ffmpeg=False)

    prov.cancel()
    prov._thread.join(timeout=2.0)
    assert prov.status()["status"] == "cancelled"
    assert not (tmp_path / "mock.tmp").exists()

