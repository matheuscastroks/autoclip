# Desktop App Distribution & Smart Hardware Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform AutoClip into a zero-configuration, standalone desktop application that automatically inspects user hardware (CPU, RAM, GPU), smartly recommends and provisions the optimal Whisper model (`base`, `small`, or `large-v3-turbo`) and FFmpeg with visual progress in a first-run Onboarding Wizard, seamlessly handing off to Gemini / OpenRouter API key configuration.

**Architecture:** 
1. A lightweight, non-blocking hardware profiler (`engine/system/profiler.py`) classifies the user's machine into Tier 1 (Light), Tier 2 (Balanced), or Tier 3 (High Performance).
2. A streaming dependency provisioner (`engine/system/provisioner.py`) downloads Gyan FFmpeg essentials and Hugging Face CTranslate2 Whisper model weights to `%LOCALAPPDATA%/AutoClip/`, verifying SHA-256 and publishing real-time byte progress.
3. System API endpoints (`engine/api/app.py`) expose `/api/v1/system/profile`, `/api/v1/system/provision`, `/api/v1/system/provision/status`, and `/api/v1/system/provision/cancel`.
4. A Vue 3 Onboarding Wizard modal (`desktop/src/components/OnboardingModal.vue`) opens automatically when dependencies are missing, displaying hardware diagnosis, allowing model selection, rendering real-time download progress, and guiding API key entry.
5. Desktop packaging scaffolding (`scripts/build_engine_sidecar.py` and `desktop/src-tauri/tauri.conf.json`) prepares the PyInstaller sidecar binary and Tauri v2 NSIS bundle configuration.

**Tech Stack:** Python 3.12, `psutil`, `ctranslate2`, `urllib`/`httpx`, FastAPI, Vue 3, TypeScript, Lucide Icons, Vitest, Pytest, Tauri v2.

**Spec:** `docs/superpowers/specs/2026-10-13-desktop-app-onboarding-design.md`

## Global Constraints

- Preserve all 87 passing frontend Vitest tests and all existing backend unit/integration tests without regressions.
- Do not require Python, Node, Git, or developer tools on the end-user machine.
- All downloaded binaries and model weights must reside strictly under `%LOCALAPPDATA%/AutoClip/` (`bin/` and `models/`), fallback to `~/.autoclip/` if `%LOCALAPPDATA%` is missing.
- Downloads must use `.tmp` extensions during streaming and only be promoted to final names upon complete download and integrity verification.
- Hardware detection must run in < 100ms without blocking the event loop or crashing on non-NVIDIA/unsupported platforms.
- Sensitive credentials (Gemini / OpenRouter API keys) must never be written to plaintext settings files or logged.

## Review Focus

1. **Network interruption during multi-hundred-megabyte downloads:** Provisioner must cleanly handle connection drops, clean up orphaned `.tmp` files, report human-readable error messages via `/api/v1/system/provision/status`, and allow resume/retry without corrupting existing files.
2. **Unsupported GPU or missing CUDA drivers:** Hardware profiler must catch `ctranslate2` CUDA initialization errors or missing driver DLLs gracefully and fall back to CPU metrics without crashing.
3. **Existing tools on PATH:** If FFmpeg and ffprobe are already installed and functional on the user system, `locate_tools()` must detect them and the wizard must default the FFmpeg download checkbox to unchecked.
4. **Concurrent provisioning requests:** If a user clicks "Instalar Dependências" multiple times or multiple tabs connect, the provisioner must return HTTP 409 Conflict if an active download is already in flight.
5. **Disk space exhaustion:** If disk space is insufficient for the selected model tier or FFmpeg zip extraction, the provisioner must abort safely before corrupting local application state and emit an actionable error.

---

### Task 1: Hardware Profiler & Model Recommendation Engine

**Files:**
- Create: `engine/system/__init__.py`
- Create: `engine/system/profiler.py`
- Test: `tests/unit/test_profiler.py`

**Interfaces:**
- Consumes: `psutil.cpu_count`, `psutil.virtual_memory`, `ctranslate2.get_cuda_device_count`.
- Produces: `profile_hardware() -> HardwareProfile` (containing `cpu_physical_cores`, `cpu_logical_cores`, `ram_total_gb`, `ram_available_gb`, `has_cuda`, `gpu_name`, `vram_gb`, `recommended_tier`, `recommended_model_id`, `tier_title`, `tier_description`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_profiler.py
from unittest.mock import patch, MagicMock
from engine.system.profiler import profile_hardware, HardwareProfile, recommend_tier

def test_hardware_profiler_low_spec_recommends_base():
    profile = recommend_tier(cpu_cores=4, ram_gb=4.0, has_cuda=False, vram_gb=0.0)
    assert profile["recommended_tier"] == 1
    assert profile["recommended_model_id"] == "Systran/faster-whisper-base"

def test_hardware_profiler_mid_spec_recommends_small():
    profile = recommend_tier(cpu_cores=6, ram_gb=8.0, has_cuda=False, vram_gb=0.0)
    assert profile["recommended_tier"] == 2
    assert profile["recommended_model_id"] == "Systran/faster-whisper-small"

def test_hardware_profiler_high_spec_ram_recommends_turbo():
    profile = recommend_tier(cpu_cores=8, ram_gb=16.0, has_cuda=False, vram_gb=0.0)
    assert profile["recommended_tier"] == 3
    assert profile["recommended_model_id"] == "Systran/faster-whisper-large-v3-turbo"

def test_hardware_profiler_cuda_gpu_recommends_turbo():
    profile = recommend_tier(cpu_cores=4, ram_gb=8.0, has_cuda=True, vram_gb=6.0)
    assert profile["recommended_tier"] == 3
    assert profile["recommended_model_id"] == "Systran/faster-whisper-large-v3-turbo"

def test_profile_hardware_handles_cuda_failure_gracefully():
    with patch("engine.system.profiler.ctranslate2.get_cuda_device_count", side_effect=RuntimeError("CUDA error")), \
         patch("psutil.cpu_count", return_value=8), \
         patch("psutil.virtual_memory", return_value=MagicMock(total=16 * (1024**3), available=10 * (1024**3))):
        profile = profile_hardware()
        assert profile.has_cuda is False
        assert profile.recommended_tier == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest.exe tests/unit/test_profiler.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.system'`

- [ ] **Step 3: Implement `engine/system/profiler.py`**

Create `engine/system/__init__.py` and `engine/system/profiler.py` with:
- Dataclass/Pydantic `HardwareProfile`
- `recommend_tier(cpu_cores: int, ram_gb: float, has_cuda: bool, vram_gb: float) -> dict`
  - Tier 3: `ram_gb >= 16.0 or (has_cuda and vram_gb >= 4.0)` -> `Systran/faster-whisper-large-v3-turbo`
  - Tier 2: `cpu_cores >= 6 and ram_gb >= 8.0` -> `Systran/faster-whisper-small`
  - Tier 1: Otherwise -> `Systran/faster-whisper-base`
- `profile_hardware() -> HardwareProfile` safely querying `psutil` and `ctranslate2`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest.exe tests/unit/test_profiler.py -v`
Expected: PASS (all 5 tests pass)

- [ ] **Step 5: Commit**

```bash
git add engine/system/__init__.py engine/system/profiler.py tests/unit/test_profiler.py
git commit -m "feat(system): add hardware profiler and whisper model recommendation matrix"
```

---

### Task 2: Automated Dependency Provisioner (FFmpeg & Whisper Weights)

**Files:**
- Create: `engine/system/provisioner.py`
- Test: `tests/unit/test_provisioner.py`

**Interfaces:**
- Consumes: Model IDs (`Systran/faster-whisper-base`, `Systran/faster-whisper-small`, `Systran/faster-whisper-large-v3-turbo`), Gyan FFmpeg download URL, storage layout `%LOCALAPPDATA%/AutoClip/`.
- Produces: `DependencyProvisioner` class with:
  - `start(model_id: str, install_ffmpeg: bool) -> dict`
  - `status() -> dict` (`status`: `idle` | `downloading` | `extracting` | `ready` | `failed`, `stage`: str, `item`: str, `downloaded_bytes`: int, `total_bytes`: int, `speed_bps`: float, `percent`: float, `error`: str | None)
  - `cancel()`
  - Storage paths: `get_tools_dir() -> Path`, `get_models_dir() -> Path`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_provisioner.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest.exe tests/unit/test_provisioner.py -v`
Expected: FAIL with `ImportError: cannot import name 'DependencyProvisioner'`

- [ ] **Step 3: Implement `engine/system/provisioner.py`**

Implement:
- `get_storage_base() -> Path` resolving `%LOCALAPPDATA%/AutoClip` (fallback `~/.autoclip`)
- `DependencyProvisioner` managing thread-safe background execution:
  - Streaming download with chunked writing to `.tmp` files.
  - Tracking progress: bytes downloaded, total bytes, speed EMA, percent.
  - `_extract_ffmpeg_zip(zip_path, target_dir)`: extracts only `ffmpeg.exe` and `ffprobe.exe` directly into `target_dir` and removes `.zip`.
  - Downloading Hugging Face model files (`config.json`, `tokenizer.json`, `vocabulary.txt`, `model.bin`) for the given model repo.
  - Safe rename from `.tmp` to final file on verified completion.
  - Clean error recovery on network drops and cancellation.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest.exe tests/unit/test_provisioner.py -v`
Expected: PASS (all 4 tests pass)

- [ ] **Step 5: Commit**

```bash
git add engine/system/provisioner.py tests/unit/test_provisioner.py
git commit -m "feat(system): add streaming dependency provisioner for ffmpeg and whisper models"
```

---

### Task 3: Backend System API Endpoints & Tool Locator Integration

**Files:**
- Modify: `engine/media/probe.py:8-16`
- Modify: `engine/api/app.py`
- Create: `tests/api/test_system_endpoints.py`

**Interfaces:**
- Consumes: `profile_hardware()` from `engine.system.profiler`, `DependencyProvisioner` from `engine.system.provisioner`.
- Produces:
  - `GET /api/v1/system/profile` -> `{ schema_version, profile: HardwareProfile }`
  - `POST /api/v1/system/provision` -> `{ started: bool, model_id: str, install_ffmpeg: bool }`
  - `GET /api/v1/system/provision/status` -> `ProvisionStatus`
  - `POST /api/v1/system/provision/cancel` -> `{ cancelled: bool }`
  - Auto-detection of `%LOCALAPPDATA%/AutoClip/bin/ffmpeg.exe` in `locate_tools()`.

- [ ] **Step 1: Write the failing test**

```python
# tests/api/test_system_endpoints.py
from fastapi.testclient import TestClient
from engine.api.app import create_app

def test_system_profile_endpoint(tmp_path):
    app = create_app(tmp_path, token="test-token")
    client = TestClient(app)
    res = client.get("/api/v1/system/profile", headers={"Authorization": "Bearer test-token"})
    assert res.status_code == 200
    data = res.json()
    assert "recommended_tier" in data["profile"]
    assert "recommended_model_id" in data["profile"]
    assert data["profile"]["recommended_tier"] in (1, 2, 3)

def test_system_provision_status_idle(tmp_path):
    app = create_app(tmp_path, token="test-token")
    client = TestClient(app)
    res = client.get("/api/v1/system/provision/status", headers={"Authorization": "Bearer test-token"})
    assert res.status_code == 200
    assert res.json()["status"] in ("idle", "ready")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest.exe tests/api/test_system_endpoints.py -v`
Expected: FAIL with 404 Not Found for `/api/v1/system/profile`

- [ ] **Step 3: Implement endpoints and update `locate_tools()`**

1. In `engine/media/probe.py`: Add `(get_storage_base() / 'bin/ffmpeg.exe')` to candidate paths in `locate_tools()`.
2. In `engine/api/app.py`:
   - Initialize `provisioner = DependencyProvisioner()` on `app.state`.
   - Register endpoints:
     - `GET /api/v1/system/profile`
     - `POST /api/v1/system/provision` (calls provisioner in thread pool, updates settings with new model path and tools on success)
     - `GET /api/v1/system/provision/status`
     - `POST /api/v1/system/provision/cancel`

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest.exe tests/api/test_system_endpoints.py -v`
Expected: PASS (both tests pass)

- [ ] **Step 5: Run full backend test suite to ensure zero regressions**

Run: `.venv\Scripts\pytest.exe tests/unit/ tests/api/ -v`
Expected: PASS (all tests pass)

- [ ] **Step 6: Commit**

```bash
git add engine/media/probe.py engine/api/app.py tests/api/test_system_endpoints.py
git commit -m "feat(api): expose system hardware profile and dependency provisioning endpoints"
```

---

### Task 4: Frontend API, Types & Onboarding Wizard Modal

**Files:**
- Modify: `desktop/src/types.ts`
- Modify: `desktop/src/api.ts`
- Create: `desktop/src/components/OnboardingModal.vue`
- Modify: `desktop/src/App.vue`
- Create: `desktop/tests/onboarding-modal.test.ts`

**Interfaces:**
- Consumes: Backend system API endpoints via `api.systemProfile()`, `api.provision()`, `api.provisionStatus()`, `api.cancelProvision()`.
- Produces: `OnboardingModal.vue` providing:
  - Step 1: Diagnóstico de hardware (CPU, RAM, GPU) + Card de recomendação com seleção de tiers (Tier 1 Leve, Tier 2 Equilibrado, Tier 3 Turbo) + Checkbox FFmpeg.
  - Step 2: Download ao vivo com barra de progresso em porcentagem, contagem de MB baixados/total, item atual e cancelamento.
  - Step 3: Conclusão com link direto para salvar chave API (Gemini ou OpenRouter) e botão "Abrir AutoClip e Começar".

- [ ] **Step 1: Write the failing test**

```typescript
// desktop/tests/onboarding-modal.test.ts
import {mount} from '@vue/test-utils'
import {describe,it,expect,vi} from 'vitest'
import OnboardingModal from '../src/components/OnboardingModal.vue'

describe('OnboardingModal', () => {
  const mockProfile = {
    cpu_physical_cores: 8,
    cpu_logical_cores: 16,
    ram_total_gb: 16.0,
    ram_available_gb: 11.2,
    has_cuda: true,
    gpu_name: 'NVIDIA GeForce RTX 3060',
    vram_gb: 6.0,
    recommended_tier: 3,
    recommended_model_id: 'Systran/faster-whisper-large-v3-turbo',
    tier_title: 'Tier 3 (Alta Performance)',
    tier_description: 'Recomendado para o seu setup com GPU dedicada'
  }

  it('renders hardware specs and recommended tier badge', () => {
    const wrapper = mount(OnboardingModal, {
      props: {
        profile: mockProfile,
        toolsMissing: true,
        asrMissing: true
      }
    })
    expect(wrapper.text()).toContain('RTX 3060')
    expect(wrapper.text()).toContain('Tier 3')
    expect(wrapper.find('[data-tier="3"]').classes()).toContain('recommended')
  })

  it('allows user to manually override recommended tier', async () => {
    const wrapper = mount(OnboardingModal, {
      props: {
        profile: mockProfile,
        toolsMissing: false,
        asrMissing: true
      }
    })
    const tier2Btn = wrapper.find('[data-tier="2"]')
    await tier2Btn.trigger('click')
    expect(wrapper.find('[data-tier="2"]').classes()).toContain('selected')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd desktop && npm test -- --run tests/onboarding-modal.test.ts`
Expected: FAIL with missing `OnboardingModal.vue`

- [ ] **Step 3: Implement types, API methods, and `OnboardingModal.vue`**

1. In `desktop/src/types.ts`:
   - Define `HardwareProfile`, `ProvisionStatus`, `ProvisionRequest`.
2. In `desktop/src/api.ts`:
   - Add `systemProfile()`, `provision(body: ProvisionRequest)`, `provisionStatus()`, `cancelProvision()`.
3. Create `desktop/src/components/OnboardingModal.vue` matching the polished dark-theme styling of `SettingsPanel.vue` and `GlobalQueueModal.vue`.
4. In `desktop/src/App.vue`:
   - Import `OnboardingModal`.
   - Add `const showOnboarding = computed(() => Boolean(config.value && (!config.value.tools_available || !config.value.asr_available)))`.
   - On close or completion, refresh config and transition smoothly.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd desktop && npm test -- --run tests/onboarding-modal.test.ts`
Expected: PASS

- [ ] **Step 5: Run full frontend test suite to ensure all 87+ tests pass**

Run: `cd desktop && npm test -- --run`
Expected: PASS (all tests pass)

- [ ] **Step 6: Commit**

```bash
git add desktop/src/types.ts desktop/src/api.ts desktop/src/components/OnboardingModal.vue desktop/src/App.vue desktop/tests/onboarding-modal.test.ts
git commit -m "feat(ux): add smart hardware onboarding wizard and visual dependency installer"
```

---

### Task 5: Desktop Packaging Scaffolding & Tauri v2 NSIS Configuration

**Files:**
- Create: `scripts/build_engine_sidecar.py`
- Modify: `desktop/src-tauri/tauri.conf.json`
- Create: `tests/unit/test_sidecar_packaging.py`

**Interfaces:**
- Consumes: `engine/cli.py` entrypoint, PyInstaller parameters, Tauri v2 configuration.
- Produces:
  - Executable build script for engine sidecar packaging into `desktop/src-tauri/bin/autoclip-engine.exe`.
  - Tauri configuration registering `bundle.active = true`, target `nsis`, externalBin `["bin/autoclip-engine"]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_sidecar_packaging.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest.exe tests/unit/test_sidecar_packaging.py -v`
Expected: FAIL with `AssertionError: assert False is True`

- [ ] **Step 3: Implement `scripts/build_engine_sidecar.py` and update `desktop/src-tauri/tauri.conf.json`**

1. Create `scripts/build_engine_sidecar.py`:
   - Configures PyInstaller command with `--name autoclip-engine`, `--clean`, hidden imports (`uvicorn`, `fastapi`, `ctranslate2`, `faster_whisper`, `psutil`, `keyring`).
   - Copies generated binary to `desktop/src-tauri/bin/autoclip-engine.exe` (or architecture target binary name).
2. Update `desktop/src-tauri/tauri.conf.json`:
   - Set `"bundle": { "active": true, "targets": ["nsis"], "externalBin": ["bin/autoclip-engine"] }`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest.exe tests/unit/test_sidecar_packaging.py -v`
Expected: PASS

- [ ] **Step 5: Run production build check**

Run: `cd desktop && npm run build`
Expected: Build completes without errors.

- [ ] **Step 6: Commit**

```bash
git add scripts/build_engine_sidecar.py desktop/src-tauri/tauri.conf.json tests/unit/test_sidecar_packaging.py
git commit -m "feat(dist): configure pyinstaller engine sidecar and tauri nsis installer packaging"
```
