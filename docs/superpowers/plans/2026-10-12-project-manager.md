# Project Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Administrar o AutoClip por interface em português e atalho Windows, sem terminal e sem chamadas Gemini durante implementação.

**Architecture:** Vue 3/TypeScript servido pelo FastAPI em loopback; SQLite registra projetos e trabalhos. API delega às funções existentes do motor, com fronteiras de execução e workers separados. Launcher inicia a instância local; Tauri/instalador permanecem no marco seguinte.

**Tech Stack:** Vue 3, TypeScript, Vite, FastAPI, Uvicorn, SQLite stdlib, Python 3.12 e motor existente. Testes pytest/TestClient e Vitest/Vue Test Utils; dependências frontend/API fixadas por locks após instalação.

**Spec:** `docs/superpowers/specs/2026-10-12-project-manager-design.md` (aprovada pelo usuário).

## Global Constraints

- Nenhuma nova chamada remota está autorizada para testes. O teste do provedor usa fixtures.
- Um trabalho pesado por vez no notebook. Token de sessão, loopback 127.0.0.1, validação de Origin, sem CORS wildcard.
- Projetos e artefatos existentes preservados; abrir/importar não dispara ASR/Gemini.
- Cinco critérios editoriais explícitos e aprovação vinculada ao fingerprint existente.
- Segredos nunca retornam à UI, localStorage, logs, SQLite ou Git.
- Interface em português; paleta, Segoe UI e notebook 1366×768 conforme spec.
- Launcher é de desenvolvimento com os runtimes provisionados; não alegar instalador autossuficiente.
- Git local `poc-openshorts-gemini`, commits por entrega; nenhum push/publicação.

## Review Focus

1. Projeto de ASR parcial ou preview manual: consulta funciona sem fabricar ProjectRun, candidatos ou aprovação — Task 1.
2. Reinício durante trabalho/chamada: interrupted e contador persistido; não gastar novamente silenciosamente — Task 2.
3. URL ou caminhos com acentos/espaços e tentativa de traversal: importação explícita e mídia confinada — Tasks 1/4.
4. Credencial ou erro do provedor: segredo ausente na API/UI/log; falha não é sucesso vazio — Tasks 1/3.
5. Preview/legendas alterados após aprovação: exportação rejeitada; contexto e vídeo continuam acessíveis — Tasks 3/5.

## Task 1: API local e biblioteca persistente

**Files:** Create `engine/api/{__init__,app,store,projects,settings,media}.py`; create `tests/api/test_projects.py`, `tests/api/test_access.py`; modify `pyproject.toml`, dependency locks and `.gitignore` for `.autoclip/` runtime state.

**Interfaces:** `create_app(workspace: Path, token: str) -> FastAPI`; `ProjectStore(database: Path)` exposes `register(path: Path, name: str | None) -> dict`, `list_projects() -> list[dict]`, `get(project_id: str) -> dict`. UUID registry id is independent of optional engine ProjectRun id. Responses have API `schema_version: "1.0"`.

API routes `/api/v1/health`, `/config`, `/config/credential`, `/projects`, `/projects/import`, `/projects/{id}`, `/projects/{id}/transcript`, `/projects/{id}/media/{asset}`. Mutations/queries require bearer token and valid Origin when header exists. Video authentication uses short-lived signed media URL bound to registered asset; no secret/API bearer in video URL. Only localhost frontend origins on bound session port accepted. Range/seek supported, arbitrary filesystem paths never exposed as media endpoint.

- [ ] Write failing tests: register same path twice yields one project; real partial source/transcript without project.json returns `has_transcript=true` and zero invented revisions; opening never calls providers; unauthorized request 401; malicious Origin 403; media traversal denied; config responses exclude supplied secret.
- [ ] Run `.venv/Scripts/python.exe -X utf8 -m pytest tests/api/test_projects.py tests/api/test_access.py -q --basetemp .api-test-tmp`; observe RED for missing API.
- [ ] Implement registry SQLite transactions; discovery restricted to existing `poc-projects` children on first run; tolerate per-project malformed artifact with explicit warning. Configuration default local model/tool paths; resolve FFmpeg via existing helper. Write credential via existing keyring adapter; return presence only.
- [ ] Implement protected API and range media reader; whitelist source and declared revision outputs, resolved against registered project. Validation/errors sanitized and structured, not raw stack traces.
- [ ] Repeat tests to GREEN; commit `feat: add local project library API`.

## Task 2: Etapas acionáveis e trabalhos persistidos

**Files:** Modify `engine/pipeline/runner.py`, `engine/adapters/gemini/analyzer.py`; create `engine/api/{jobs,job_worker}.py`, `engine/pipeline/request_budget.py`; tests `tests/api/test_jobs.py`, `tests/unit/test_request_budget.py`, `tests/integration/test_stage_boundaries.py`.

**Interfaces:** `run_project(..., stop_after: Literal['transcribe','analyze','render']='render', ...) -> ProjectRun`; default retains CLI behavior. `JobManager.start(project_id: str, operation: Literal['import','transcribe','analyze','render','export'], options: dict) -> dict`; `status(job_id: str) -> dict`; `cancel(job_id: str) -> dict`. Status pending/running/completed/failed/cancelled/interrupted. Projects without canonical ProjectRun remain registrable and must be adopted with source/hash validation before execution.

`RequestBudget(path: Path, limit: int)` exposes `reserve(payload_hash: str) -> int`, atomically persists an attempt BEFORE issuing request; denies when exhausted. Analyzer accepts optional budget and uses it for every request/retry/repair. Worker uses persistent job-specific budget and explicit new job authorization; restarting same job never resets budget. Legacy ASR adoption records provenance and distinct cache identity; source/hash mismatch fails.

Routes `POST /projects/{id}/jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/cancel`. SQLite single-heavy-job constraint; worker subprocess writes ordered events and cancel marker. Import uses existing importer; API remains responsive. On API startup orphan running jobs are interrupted only after confirming ownership/liveness, never kill unrelated process. Persistent errors/events exclude provider secrets/text.

- [ ] Write tests asserting transcribe stop never invokes analyzer; analyze stop never renders; job busy response409; cancel reaches worker; new manager marks dead owned worker interrupted; reopened budget with limit2 denies third reserve; retry consumes reserve; budget preflight no provider call.
- [ ] Run these tests and observe RED.
- [ ] Implement boundaries, counters and workers. Local source paths validated; temporary writes confined; existing manifests reused by valid hashes. Cancellation delegates existing tree termination. Persist operation/config/source id for explicit resume.
- [ ] Repeat tests to GREEN, run existing runner/cache tests; commit `feat: expose staged jobs with durable request budgets`.

## Task 3: Interface Vue conectada aos projetos e revisões

**Files:** Create `desktop/package.json`, lock, `index.html`, `vite.config.ts`, `tsconfig*.json`, `src/{main.ts,App.vue,api.ts,types.ts,styles.css}`, `src/components/{ProjectLibrary,ProjectWorkspace,JobPanel,SettingsPanel,ReviewPanel}.vue`; create frontend tests. Create `engine/api/reviews.py` and `tests/api/test_reviews.py`.

**Interfaces:** Typed `api.ts` wrappers mirror Task1/2. App receives session token in URL fragment from launcher, removes fragment immediately; holds token only in memory. No token/key in localStorage. API review routes `GET /projects/{id}/revisions`, `POST /projects/{id}/revisions/{revision}/decision`, `POST /projects/{id}/exports` reuse `review_fingerprint`, `record_review`, `export_approved`.

- [ ] Write tests: library filters failed projects; opens partial project and empty cuts message; settings secret masked and submitted without persisting; job failure displayed with retry action; analysis requires user action/budget summary; five checks needed for approval; changed fingerprint rejects export; manual preview clearly labeled and unapprovable as semantic cut.
- [ ] Run API tests and `npm --prefix desktop test -- --run`, observe missing components/routes RED after minimal test setup.
- [ ] Implement responsive composition from spec: sidebar Projects/Settings, project rows/search/state, original player, stage panel, transcript seek links, review preview/context, five checkboxes/notes, export results. No fictional projects/analytics/percentages. Use Portuguese status translations and safe error messages. Busy/pending/empty/error states and disabled actions have reasons.
- [ ] Native chooser endpoints for local video/project/model/tool paths use explicit picker request; picker executes off event loop. Cancel dialog returns cancelled without creating project. Browser upload fallback may be added only with bounded streaming; no whole-video buffering in RAM.
- [ ] Re-run tests, TypeScript check, production build; serve built assets from FastAPI, not Vite in user launcher. Commit `feat: add graphical project workspace and review`.

## Task 4: Atalho Windows e ciclo de vida local

**Files:** Create `engine/api/launcher.py`, `Abrir AutoClip.vbs`, `scripts/create_shortcut.ps1`, `tests/api/test_launcher.py`; modify API entrypoint and add `docs/frontend-runbook.md`.

**Interfaces:** `launch(workspace: Path, open_browser=True) -> str` starts or reconnects to verified owned instance, random loopback port, session token and pid marker stored only runtime state. `pythonw.exe` starts launcher hidden. VBS resolves its own project directory; no hardcoded user paths. GUI actions open registered project/export folders using native Windows shell, no arbitrary executable commands.

- [ ] Write tests: existing valid owned session reused; stale marker starts fresh; untrusted process/endpoint never accepted; launching path with spaces/accents preserves exact argv; missing runtime/build shows actionable GUI message instead of disappearing.
- [ ] Run tests to RED; implement launcher handshake/session discovery and readiness timeout, browser app window when available with standard browser fallback. Handle second click without second API/job instance; logs local and secret-free.
- [ ] Generate workspace-local `.lnk` from launcher path. Do not modify Windows startup/system profile or install globally. Closing window does not claim worker stopped; provide explicit stop service action that cancels owned work safely.
- [ ] Tests GREEN; actual double-click-equivalent start verifies health and page load; document usage and limitations. Commit `feat: launch local workspace without terminal`.

## Task 5: Validação completa e entrega

**Files:** Update `README.md`, `docs/08-validacao.md`, `docs/frontend-runbook.md`, `docs/frontend-progress.md`; evidence under `poc-results/frontend/` excluding real transcripts/secrets/media. Browser tests under `desktop/tests/` where useful.

- [ ] Full Python suite, Vue tests, TypeScript and build. Verify no secrets/media/model files tracked. Existing opt-in real Gemini test remains skipped honestly.
- [ ] Launch real API/UI on notebook; import/discover existing full ASR and failed Gemini project, play original/seek, inspect transcription, open settings, verify empty-cut state and manual preview distinction. Confirm no outbound provider requests and ASR not rerun. Test supported local controls using short synthetic video and provider fixture only.
- [ ] Render/inspect library, workspace, settings, review at1366×768 and narrow viewport; keyboard/focus/error and cancel-dialog behavior. Fix clipping/overlap and actionable-flow defects.
- [ ] One fresh whole-branch reviewer as required by native execution skill; no per-task implementer agents. One fix pass with regression RED→GREEN for material findings; ledger deferred minors. No second review dispatch.
- [ ] Commit verified delivery, record tests and actual paths; preserve local branch/workspace. Open UI for user. Report real semantic validation and Tauri packaging as pending, not implemented features.

## Self-review and execution

All spec sections map to Tasks1–5. Contracts shared between Vue/API are defined before consumers; no API logic duplicated in UI. Five review inputs each have owning tests. Dependencies: Task1 → Task2 → Task3 → Task4 → Task5. Native execution is recommended because registry, jobs and UI share interfaces and one independent final review is sufficient; separate task agents would repeat engine context.

Plan ready for user review; product implementation waits for that review under writing-plans. After approval execute all tasks without asking between tasks, with progress ledger and local commits.
