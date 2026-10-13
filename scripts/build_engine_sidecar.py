"""Builds the standalone Python engine sidecar executable for Tauri desktop distribution."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TAURI_BIN_DIR = ROOT_DIR / "desktop" / "src-tauri" / "bin"
ENTRY_POINT = ROOT_DIR / "engine" / "cli.py"

def get_target_triple() -> str:
    """Returns the host Rust target triple for Tauri sidecar naming."""
    try:
        out = subprocess.check_output(["rustc", "-vV"], text=True)
        for line in out.splitlines():
            if line.startswith("host:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    if os.name == "nt":
        return "x86_64-pc-windows-msvc"
    return "x86_64-unknown-linux-gnu"

def build():
    print("=== AutoClip Engine Sidecar Builder ===")
    TAURI_BIN_DIR.mkdir(parents=True, exist_ok=True)
    triple = get_target_triple()

    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=autoclip-engine",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--distpath", str(ROOT_DIR / "build" / "engine-dist"),
        "--workpath", str(ROOT_DIR / "build" / "engine-build"),
        "--collect-all=engine",
        "--collect-all=uvicorn",
        "--collect-all=starlette",
        "--collect-data=faster_whisper",
        "--hidden-import=uvicorn",
        "--hidden-import=fastapi",
        "--hidden-import=ctranslate2",
        "--hidden-import=faster_whisper",
        "--hidden-import=psutil",
        "--hidden-import=keyring",
        "--hidden-import=keyring.backends.Windows",
        "--hidden-import=engine.system.profiler",
        "--hidden-import=engine.system.provisioner",
        "--hidden-import=engine.system.subprocesses",
    ]

    dist_folder = ROOT_DIR / "desktop" / "dist"
    if (dist_folder / "index.html").is_file():
        sep = ";" if os.name == "nt" else ":"
        pyinstaller_cmd.append(f"--add-data={dist_folder}{sep}desktop/dist")
        print(f"Bundling frontend from: {dist_folder}")
    else:
        print(f"Notice: frontend dist not found at {dist_folder}; ensure it is built if frontend bundling is required.")

    pyinstaller_cmd.append(str(ENTRY_POINT))

    print(f"Executing: {' '.join(pyinstaller_cmd)}")
    subprocess.check_call(pyinstaller_cmd, cwd=str(ROOT_DIR))

    exe_name = "autoclip-engine.exe" if os.name == "nt" else "autoclip-engine"
    built_binary = ROOT_DIR / "build" / "engine-dist" / exe_name
    if not built_binary.exists():
        built_binary = ROOT_DIR / "build" / "engine-dist" / "autoclip-engine" / exe_name

    target_standard = TAURI_BIN_DIR / exe_name
    target_triple = TAURI_BIN_DIR / f"autoclip-engine-{triple}{Path(exe_name).suffix}"

    if built_binary.exists():
        shutil.copy2(built_binary, target_standard)
        shutil.copy2(built_binary, target_triple)
        print(f"Sidecar binary installed to: {target_standard}")
        print(f"Tauri triple binary installed to: {target_triple}")
    else:
        print(f"Warning: Compiled binary not found at {built_binary}")

if __name__ == "__main__":
    build()
