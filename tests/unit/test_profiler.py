from unittest.mock import patch, MagicMock
from engine.system.profiler import profile_hardware, HardwareProfile, recommend_tier

def test_hardware_profiler_low_spec_recommends_base():
    profile = recommend_tier(cpu_cores=4, ram_gb=4.0, has_cuda=False, vram_gb=0.0)
    assert profile["recommended_tier"] == 1
    assert profile["recommended_model_id"] == "Systran/faster-whisper-base"
    assert "Leve" in profile["tier_title"]

def test_hardware_profiler_mid_spec_recommends_small():
    profile = recommend_tier(cpu_cores=6, ram_gb=8.0, has_cuda=False, vram_gb=0.0)
    assert profile["recommended_tier"] == 2
    assert profile["recommended_model_id"] == "Systran/faster-whisper-small"
    assert "Equilibrado" in profile["tier_title"]

def test_hardware_profiler_high_spec_ram_recommends_turbo():
    profile = recommend_tier(cpu_cores=8, ram_gb=16.0, has_cuda=False, vram_gb=0.0)
    assert profile["recommended_tier"] == 3
    assert profile["recommended_model_id"] == "Systran/faster-whisper-large-v3-turbo"
    assert "Alta Performance" in profile["tier_title"]

def test_hardware_profiler_cuda_gpu_recommends_turbo():
    profile = recommend_tier(cpu_cores=4, ram_gb=8.0, has_cuda=True, vram_gb=6.0)
    assert profile["recommended_tier"] == 3
    assert profile["recommended_model_id"] == "Systran/faster-whisper-large-v3-turbo"

def test_profile_hardware_handles_cuda_failure_gracefully():
    with patch("ctranslate2.get_cuda_device_count", side_effect=RuntimeError("CUDA driver missing")), \
         patch("psutil.cpu_count", side_effect=lambda logical=True: 16 if logical else 8), \
         patch("psutil.virtual_memory", return_value=MagicMock(total=16 * (1024**3), available=10 * (1024**3))):
        profile = profile_hardware()
        assert isinstance(profile, HardwareProfile)
        assert profile.has_cuda is False
        assert profile.recommended_tier == 3
        assert profile.cpu_logical_cores == 16
        assert profile.ram_total_gb == 16.0
