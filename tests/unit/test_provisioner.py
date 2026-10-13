import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from engine.system.provisioner import DependencyProvisioner, get_storage_base

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
