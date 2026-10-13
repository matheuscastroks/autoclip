import json
from pathlib import Path

def test_tauri_bundle_configuration():
    tauri_conf_path = Path("desktop/src-tauri/tauri.conf.json")
    assert tauri_conf_path.is_file()
    conf = json.loads(tauri_conf_path.read_text(encoding="utf-8"))
    assert conf["bundle"]["active"] is True
    assert "nsis" in conf["bundle"]["targets"]
    assert "bin/autoclip-engine" in conf["bundle"]["externalBin"]

def test_sidecar_build_script_exists():
    script_path = Path("scripts/build_engine_sidecar.py")
    assert script_path.is_file()
