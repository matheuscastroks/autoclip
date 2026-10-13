from dataclasses import dataclass, asdict
from typing import Optional
import os
import psutil

@dataclass
class HardwareProfile:
    cpu_physical_cores: int
    cpu_logical_cores: int
    ram_total_gb: float
    ram_available_gb: float
    has_cuda: bool
    gpu_name: Optional[str]
    vram_gb: float
    recommended_tier: int
    recommended_model_id: str
    tier_title: str
    tier_description: str

    def to_dict(self) -> dict:
        return asdict(self)

def recommend_tier(cpu_cores: int, ram_gb: float, has_cuda: bool = False, vram_gb: float = 0.0) -> dict:
    if ram_gb >= 16.0 or (has_cuda and vram_gb >= 4.0):
        return {
            "recommended_tier": 3,
            "recommended_model_id": "Systran/faster-whisper-large-v3-turbo",
            "tier_title": "Tier 3 (Alta Performance)",
            "tier_description": "Whisper Large v3 Turbo com máxima fidelidade em português e aceleração por hardware."
        }
    elif cpu_cores >= 6 and ram_gb >= 8.0:
        return {
            "recommended_tier": 2,
            "recommended_model_id": "Systran/faster-whisper-small",
            "tier_title": "Tier 2 (Equilibrado)",
            "tier_description": "Whisper Small com excelente equilíbrio entre velocidade de corte e precisão editorial."
        }
    else:
        return {
            "recommended_tier": 1,
            "recommended_model_id": "Systran/faster-whisper-base",
            "tier_title": "Tier 1 (Leve)",
            "tier_description": "Whisper Base otimizado para máquinas compactas, baixo uso de RAM e processamento rápido."
        }

def _detect_gpu() -> tuple[bool, Optional[str], float]:
    has_cuda = False
    gpu_name = None
    vram_gb = 0.0
    try:
        import ctranslate2
        count = ctranslate2.get_cuda_device_count()
        if count > 0:
            has_cuda = True
    except Exception:
        has_cuda = False

    # Optional fast query for NVIDIA GPU name/VRAM on Windows without blocking
    if has_cuda and os.name == "nt":
        try:
            import subprocess
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                timeout=1.5,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            ).strip()
            if out:
                first = out.splitlines()[0]
                parts = [p.strip() for p in first.split(",")]
                if len(parts) >= 2:
                    gpu_name = parts[0]
                    vram_gb = round(float(parts[1]) / 1024.0, 1)
        except Exception:
            pass

    return has_cuda, gpu_name, vram_gb

def profile_hardware() -> HardwareProfile:
    physical = psutil.cpu_count(logical=False) or 1
    logical = psutil.cpu_count(logical=True) or physical
    vm = psutil.virtual_memory()
    ram_total = round(vm.total / (1024 ** 3), 1)
    ram_avail = round(vm.available / (1024 ** 3), 1)

    has_cuda, gpu_name, vram_gb = _detect_gpu()
    rec = recommend_tier(cpu_cores=logical, ram_gb=ram_total, has_cuda=has_cuda, vram_gb=vram_gb)

    return HardwareProfile(
        cpu_physical_cores=physical,
        cpu_logical_cores=logical,
        ram_total_gb=ram_total,
        ram_available_gb=ram_avail,
        has_cuda=has_cuda,
        gpu_name=gpu_name,
        vram_gb=vram_gb,
        recommended_tier=rec["recommended_tier"],
        recommended_model_id=rec["recommended_model_id"],
        tier_title=rec["tier_title"],
        tier_description=rec["tier_description"]
    )
