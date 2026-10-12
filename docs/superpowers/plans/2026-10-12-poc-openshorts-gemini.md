# PoC OpenShorts + Gemini Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validar o motor baseado no núcleo MIT do OpenShorts, usando Gemini para selecionar cortes informativos do vídeo escolhido e CPU para transcrição/renderização.

**Architecture:** Adaptadores isolam os módulos OpenShorts dos contratos v1; uma CLI coordena etapas e manifests retomáveis. A seleção Gemini recebe somente texto, e o render consome uma revisão com EDL, legendas e atribuição. Esta PoC usa arquivos de projeto e manifests; SQLite, API e desktop pertencem aos marcos seguintes.

**Tech Stack:** Python 3.12, Pydantic, faster-whisper 1.2.1, PyAV 18.1.0, google-genai, keyring, yt-dlp, FFmpeg/ffprobe, pytest. Congelar dependências efetivamente verificadas em lock de produto separado do ambiente de pesquisa.

**Spec:** [Arquitetura aprovada](../../04-arquitetura.md), [contratos v1](../../05-dados-contratos.md), [Gemini](../../09-gemini.md), [PRD](../../03-prd.md) e [roadmap M1](../../06-roadmap.md). Aprovação da arquitetura pelo usuário em 12/10/2026; este plano ainda requer revisão antes de execução.

## Global Constraints

- Base: Marsic1/openshorts, SHA `b1f5350fcf24b17cb48b581400c35ad9f3974ba5`; não importar `cloud/`, `main.py`, `app.py` ou dashboard no motor.
- Windows 11 x64; Python 3.12; saída/console UTF-8. GPU, Docker, Ollama e API HTTP não são requisitos desta PoC.
- ASR: Whisper `small` multilíngue, CPU/int8, idioma `pt`, timestamps por palavra; usar peso já baixado e verificar digest.
- Gemini: modelo obrigatório em configuração explícita; chave no keyring ou ambiente do processo; somente transcrição/contexto textual; concorrência 1; sem provider alternativo automático.
- Artefatos `schema_version="1.0"`, timestamps em microssegundos inteiros e intervalos semiabertos; IDs, hashes, provenance e revisões imutáveis.
- Até três candidatos por projeto, 20–60 segundos cada; permitir zero; sem score viral, correção automática de transcrição, montagens de frases distantes, pausa removida ou alteração de velocidade.
- Primeiro render 9:16 com fit-blur explicitamente identificado, sem acompanhamento facial. Tracking e silêncio seguro ficam em M2; não declarar esses requisitos implementados.
- Fonte nunca sobrescrita; revisão humana obrigatória para declarar integridade editorial. Preview pode existir sem aprovação, mas export aprovado exige ReviewDecision.
- Render CPU libx264/AAC, 1080×1920, CFR 30, yuv420p, áudio 48 kHz; profiles e fontes registrados; nenhuma fonte baixada implicitamente durante render.
- Estágios escrevem temporários no mesmo volume, validam checksum/schema e promovem por rename atômico; existência de arquivo não valida cache.
- Provider: timeout 60 s, no máximo duas tentativas de transporte por solicitação e um reparo de JSON; cancelamento com grace period de 5 s.
- Sem inicialização/commit Git implícitos: o workspace não era um repositório na investigação. Se Git for solicitado/configurado, commits por tarefa; caso contrário preservar evidências no disco.

## Review Focus

1. **Console e paths Windows:** acento, espaço e apóstrofo não interrompem ASR nem queimam legenda errada — testes nas tarefas 2, 3 e 6.
2. **Ressalva/negação ausentes:** estrutura válida não basta para preservar sentido — teste de contexto na tarefa 4 e revisão audiovisual na tarefa 8.
3. **429, janela perdida e JSON inválido:** não concluir uma análise parcial como completa — testes na tarefa 4.
4. **Fonte/modelo/prompt alterados:** retomada não reaproveita timestamps/cortes antigos — testes na tarefa 7.
5. **VFR, rotação e offset de áudio:** imagem, fala, legenda e mapa até origem continuam coerentes — testes nas tarefas 2, 5 e 6.

## Estrutura prevista

| Caminho | Responsabilidade |
|---|---|
| `pyproject.toml`, `requirements-poc.lock.txt` | Instalação e entrypoint `autoclip-engine` |
| `vendor/openshorts/` | Núcleo MIT selecionado, licença e manifests de origem |
| `engine/contracts/` | Modelos, configuração, erros e schemas v1 |
| `engine/adapters/openshorts/` | Conversão/transcrição/janelas/legendas/EDL upstream |
| `engine/adapters/gemini/` | Credencial, cliente textual e schema de análise |
| `engine/media/` | Importação, probe e extração de áudio |
| `engine/editorial/` | Seleção validada, EDL contínua e revisão |
| `engine/render/` | FFmpeg, checks técnicos e mapa de saída |
| `engine/pipeline/` | Artefatos, manifests, cache, runner e cancelamento |
| `engine/cli.py` | Commands de execução, revisão, export e credencial |
| `tests/unit/`, `tests/integration/`, `tests/real_media/` | Regras determinísticas, subprocessos e corpus real |
| `docs/poc-runbook.md` | Comandos reais, resultados, limites e reprodução |

## Tarefa 1 — núcleo OpenShorts e contratos instaláveis

**Files:** criar `pyproject.toml`, `requirements-poc.lock.txt`, `vendor/openshorts/{LICENSE,UPSTREAM.json}`, `engine/contracts/{__init__.py,artifacts.py,config.py,errors.py}`, `tests/unit/test_contracts.py`, `tests/unit/test_upstream_boundary.py`.

**Interfaces:** produzir os modelos do documento de contratos: `Source`, `AudioArtifact`, `TranscriptArtifact`, `AnalysisArtifact`, `CandidateArtifact`, `EDLArtifact`, `CropArtifact`, `CaptionRevision`, `CaptionArtifact`, `ReviewDecision`, `RenderArtifact`, `StageRequest`, `StageResult`. Configs: `ASRConfig(model_path,language,device,compute_type)`, `AnalysisConfig(model,prompt_version,timeout_s,offline,max_calls)`, `SelectionConfig(min_us,max_us,max_clips)`, `CaptionConfig(font_path,style_id)`, `ExportConfig(width,height,fps_num,fps_den,crf,output_root)`. `PipelineError(code,stage,message,retryable)` não contém credenciais.

- [ ] Escrever `test_contracts_reject_invalid_temporal_bounds_and_major`: major incompatível, NaN, start≥end e hash inválido são rejeitados; probability aceita null; sobreposição ASR gera warning sem reescrever tempos.
- [ ] Escrever `test_engine_imports_without_cloud_or_heavy_platform`: importar engine sem cloud/main/app e sem torch/Ultralytics/Remotion; nenhuma solicitação de rede na importação.
- [ ] Executar `python -m pytest tests/unit/test_contracts.py tests/unit/test_upstream_boundary.py -q`; confirmar falha antes de implementação.
- [ ] Criar schemas v1 e copiar somente `clip_selection.py`, `transcribe_backends.py`, `subtitles.py`, `ffmpeg_utils.py` e `recut.py` como baseline MIT. Converter imports locais para relativos e registrar SHA/hashes originais, alterações e código extraído. Remover do caminho executável wrappers pesados de `recut`; conservar matemática pura utilizada. Não importar `gemini_worker` com seus prompts virais; reaproveitar padrão de chamada estruturada, com atribuição, na tarefa 4.
- [ ] Fixar `faster-whisper==1.2.1`, `av==18.1.0`; usar demais versões do lock de pesquisa como baseline e gerar lock mínimo da PoC após teste de instalação. Validar todas as dependências declaradas, sem SDK/detector que a PoC não usa.
- [ ] Reexecutar os dois arquivos: PASS; gerar schemas e importar pacote instalado num processo isolado sem módulos proibidos.

## Tarefa 2 — fonte íntegra e áudio normalizado

**Files:** criar `engine/media/{importer.py,probe.py,audio.py}`, `engine/pipeline/artifacts.py`, `tests/unit/test_media.py`, `tests/integration/test_probe_audio.py`.

**Interfaces:** consumir `ASRConfig`/artefatos da tarefa 1; produzir `import_source(input_value: str, project_root: Path) -> Source`, `probe_source(source: Source, ffprobe: Path) -> Source`, `extract_audio(source: Source, ffmpeg: Path, project_root: Path) -> AudioArtifact`, `write_artifact(payload: BaseModel, kind: str, root: Path) -> ArtifactRef`. `ArtifactRef` tem id, kind, relative_path, sha256, size_bytes e schema_version.

- [ ] Escrever `test_local_source_is_not_overwritten` e `test_url_download_failure_does_not_publish_partial`: fonte mantém hash; `.part` não aparece como artefato pronto.
- [ ] Escrever `test_probe_rotation_vfr_and_audio_offset_are_recorded`: timebase/FPS racional, orientação e deslocamento A/V preservados; sem stream de áudio produz erro explícito.
- [ ] Rodar `python -m pytest tests/unit/test_media.py tests/integration/test_probe_audio.py -q`; confirmar falhas iniciais.
- [ ] Implementar importer com arquivo/yt-dlp por argumentos, paths de FFmpeg explícitos e sem cookies automáticos; reutilizar vídeo já baixado para o teste comum, evitando novo download. Extrair PCM mono 16 kHz, registrando conversão PTS/timebase e origem temporal.
- [ ] Implementar `write_artifact` com JSON canônico, checksum, temporário e rename; tratar disco cheio sem promover output.
- [ ] Reexecutar testes; ffprobe do WAV confirma 16 kHz/mono e duration coerente. Testar nomes `Vídeo d'água 01.mp4` num diretório de fixture do workspace.

## Tarefa 3 — ASR CPU com adapter OpenShorts

**Files:** criar `engine/adapters/openshorts/transcriber.py`, `tests/unit/test_transcriber.py`, `tests/real_media/test_asr_smoke.py`; modificar módulos vendorizados somente quando necessário para config explícita.

**Interfaces:** consumir `AudioArtifact` e `ASRConfig`; produzir `OpenShortsTranscriber.transcribe(audio: AudioArtifact, config: ASRConfig) -> TranscriptArtifact`. IDs determinísticos dentro da revisão, raw transcript como artefato separado.

- [ ] Escrever `test_transcriber_forces_pt_cpu_int8_and_preserves_words`: config passada ao modelo é pt/cpu/int8; IDs existentes, microssegundos e probability nula permitida; nenhum texto polido por LLM.
- [ ] Escrever `test_empty_asr_returns_no_speech_without_remote_fallback` e `test_windows_utf8_progress`: falta de fala gera NO_SPEECH; emoji não derruba processamento; fonte/tempos não são truncados ao imprimir.
- [ ] Rodar `python -m pytest tests/unit/test_transcriber.py -q`; confirmar falhas antes do adapter.
- [ ] Adaptar backend Whisper existente sem singleton compartilhado por configs/jobs incompatíveis nem env global mutável; completar lazy generator antes de marcar estágio pronto. Registrar versão do engine/decoder e digest dos arquivos do modelo.
- [ ] Reexecutar unitários; rodar smoke real com flag opt-in e o WAV 60–180 s existente. Confirmar word JSON, idioma, bounds e checksum; não declarar WER sem anotação humana.

## Tarefa 4 — Gemini textual e seleção com contexto

**Files:** criar `engine/adapters/gemini/{credentials.py,analyzer.py}`, `engine/adapters/openshorts/windows.py`, `engine/editorial/select.py`, `engine/prompts/analysis_v1.txt`, `tests/unit/{test_credentials.py,test_gemini.py,test_selection.py}`.

**Interfaces:** consumir `TranscriptArtifact`, `AnalysisConfig`, `SelectionConfig`; produzir `set_gemini_key(secret: str) -> None`, `get_gemini_key() -> str`, `GeminiAnalyzer.analyze(transcript: TranscriptArtifact, config: AnalysisConfig) -> AnalysisArtifact`, `select_candidates(analysis: AnalysisArtifact, transcript: TranscriptArtifact, config: SelectionConfig) -> CandidateArtifact`. `Analyzer` protocol permite trocar provider sem alterar runner. `AnalysisArtifact` registra complete, cobertura de word IDs, modelo/version retornada, payload/prompt hashes e uso, sem chave.

- [ ] Escrever `test_gemini_request_contains_only_text_and_word_ids`: request não contém bytes/URI de mídia, upload, frames, tools ou comando FFmpeg; schema exige evidências e flags editoriais, sem score viral.
- [ ] Escrever `test_window_failure_is_not_complete_analysis`, `test_auth_error_is_not_retried`, `test_429_respects_attempt_budget`, `test_invalid_json_has_one_repair`: transport attempts≤2; uma janela perdida marca falha/partial explícito; 401/403 não acionam provider alternativo.
- [ ] Escrever `test_qualification_context_is_present_in_prompt` e `test_candidate_bounds_and_overlap`: fornecer ressalva tardia e negação; prompt contém contexto original; IDs ausentes/fora da ordem e duração >60 s são rejeitados; máximo 3; vazio válido preservado como resultado distinto de erro.
- [ ] Rodar `python -m pytest tests/unit/test_credentials.py tests/unit/test_gemini.py tests/unit/test_selection.py -q`; confirmar falhas iniciais.
- [ ] Adaptar janelas do OpenShorts para IDs/tempos v1: máximo 180 s, overlap 30 s; se texto exceder 12.000 caracteres, subdividir por segmentos conservando 30 s de contexto quando houver. Incluir pergunta/ressalvas; candidatos podem citar IDs somente da janela recebida. Uma passada estruturada por janela produz temas/candidatos; deduplicar por IoU temporal≥0,5 e ordenar completude/contexto/densidade explicitada, sem exigir quantidade mínima.
- [ ] Implementar Gemini SDK com modelo escolhido em `--model`, temperatura 0, timeout 60 s, concorrência 1 e orçamento `--max-calls` obrigatório para chamadas reais. Reparos/retries contam nesse orçamento. Rate limit espera Retry-After até 30 s ou backoff de 2 s; esgotar orçamento é erro acionável.
- [ ] Implementar keyring service `autoclip-editor`, account `gemini`; env `GEMINI_API_KEY` como entrada temporária explícita. Se keyring falhar, não persistir plaintext; solicitar env/entrada da sessão. Nunca ecoar segredo ou response body que possa contê-lo.
- [ ] Reexecutar unitários com cliente injetado/stub e sentinel secret; PASS e nenhum segredo nos logs/artefatos. Integração real é somente tarefa 8, quando chave for inserida localmente.

## Tarefa 5 — revisão, EDL contínua e legendas

**Files:** criar `engine/editorial/{edl.py,review.py}`, `engine/adapters/openshorts/captions.py`, `tests/unit/{test_edl.py,test_review.py,test_captions.py}`.

**Interfaces:** consumir candidates/transcript/Source; produzir `plan_continuous_edit(candidate: Candidate, transcript: TranscriptArtifact, source: Source) -> EDLArtifact`, `record_review(revision_id: UUID, decision: Literal['approved','rejected'], checks: EditorialChecks, notes: str) -> ReviewDecision`, `OpenShortsCaptionBuilder.build(transcript: TranscriptArtifact, edl: EDLArtifact, revision: CaptionRevision, config: CaptionConfig) -> CaptionArtifact`. `EditorialChecks` exige completude, contexto, ressalvas/negações, palavras/bordas e áudio/legenda/quadro; approval só quando todos confirmados por humano.

- [ ] Escrever `test_continuous_edl_preserves_every_word_and_source_bounds` e `test_source_output_roundtrip_at_join`: speed=1, removed vazio, output começa em 0; bordas protegem palavra completa; candidato não pode exceder 60 s após padding.
- [ ] Escrever `test_caption_edit_does_not_mutate_raw_asr` e `test_no_approval_for_uncertain_editorial_check`: edições têm nova revision; flag incerta não vira aprovação automática.
- [ ] Rodar `python -m pytest tests/unit/test_edl.py tests/unit/test_review.py tests/unit/test_captions.py -q`; confirmar falhas iniciais.
- [ ] Reutilizar helpers de recut para remap/validação e geradores ASS/SRT do OpenShorts, adaptando nomes/tempos/config ao contrato v1; sem chamadas a main.py. Padding máximo 150 ms limitado pelas palavras vizinhas e duração 60 s; não aparar palavra para acomodar padding.
- [ ] Exportar words/cues, ASS karaoke e SRT; limitar 2 linhas, grupos de até 4 palavras, sem alterá-las; font file fornecido explicitamente ou fonte local instalada detectada/registrada. Escapar texto ASS e paths por parser de FFmpeg, não quoting de shell.
- [ ] Reexecutar unitários; cobertura lexical total do candidato na EDL e captions dentro de duration_us. Isso prova mapping, não sentido editorial.

## Tarefa 6 — render CPU e QA técnico

**Files:** criar `engine/render/{ffmpeg.py,verify.py}`, `tests/unit/test_render_command.py`, `tests/integration/test_render.py`.

**Interfaces:** produzir `FFmpegRenderer.render(source: Source, edl: EDLArtifact, crop: CropArtifact, captions: CaptionArtifact, config: ExportConfig) -> RenderArtifact`, `verify_render(render: RenderArtifact, source: Source, edl: EDLArtifact) -> ExportValidation`. Crop inicial é fit-blur estático, anotado como fallback, sem face_track_id.

- [ ] Escrever `test_render_uses_cpu_and_no_shell` e `test_partial_render_is_never_completed`: libx264/AAC, sem NVENC, shell=False; falha/cancelamento não publica output final.
- [ ] Escrever integração `test_rotated_vfr_video_with_audio_offset_and_unicode_path`: fixture curta com fala/tom e markers conhecidos, fonte rotacionada/VFR; verificar duração, orientação normalizada, áudio e captions no tempo esperado com tolerância≤1 frame na fixture, sem rotation tag residual.
- [ ] Rodar `python -m pytest tests/unit/test_render_command.py tests/integration/test_render.py -q`; confirmar falhas iniciais.
- [ ] Implementar render a partir da fonte original e EDL, fit-blur 1080×1920, 30 fps, CRF 20, preset medium, AAC 192 kb/s/48 kHz/yuv420p e faststart. Usar nomes internos neutros de arquivos ASS e cwd de staging para contornar apóstrofos; manter fonte path como argv separado.
- [ ] Implementar QA: ffprobe/decodificação completa, duração dentro de 1 frame+1 amostra do plano, áudio presente/não totalmente silencioso, dimensões/codecs/FPS, hash/tamanho, mapping e captions bounds. Black-frame detection gera aviso com frames, não rejeita automaticamente uma source legitimamente preta.
- [ ] Reexecutar testes e inspecionar frames do render sintético; verificar que legenda realmente foi queimada, além de conferir a existência do arquivo ASS.

## Tarefa 7 — runner retomável e CLI

**Files:** criar `engine/pipeline/{manifest.py,runner.py,cancellation.py}`, `engine/cli.py`, `tests/unit/test_cache.py`, `tests/integration/test_cli_resume.py`, modificar `pyproject.toml`.

**Interfaces:** `run_project(source: Source, config: PipelineConfig, project_root: Path, cancelled: Callable[[],bool]) -> ProjectRun`; `resume_project(project_root: Path, config: PipelineConfig) -> ProjectRun`; `PipelineConfig` agrega configs das tarefas anteriores e runtime/paths sem segredo. Manifest inclui stage/version, inputs/config hashes, modelo/prompt/code versions, outputs, status e error; ProjectRun referencia artefatos e review state.

- [ ] Escrever `test_modified_source_model_prompt_and_caption_invalidate_only_dependents`, `test_corrupt_or_partial_artifact_is_not_reused`, `test_two_projects_never_share_outputs`.
- [ ] Escrever `test_kill_resume_and_cancel`: SIGINT/encerramento abrupto no processo fixture, retomada só de stages completos; grace period 5 s; checksums/artefatos anteriores preservados; falha em item de render não perde demais.
- [ ] Rodar `python -m pytest tests/unit/test_cache.py tests/integration/test_cli_resume.py -q`; confirmar falhas iniciais.
- [ ] Implementar sequência ingest/probe/audio/transcribe/analyze/select/edit_plan/captions/preview/verify. Preview fica `needs_review`; comando humano aprova revisão e `export` gera pacote com ReviewDecision. Não usar existência de arquivo como checkpoint. Offline recusa análise Gemini; permite ASR/revisão/render com artefatos existentes e EDL manual validada.
- [ ] Expor comandos `doctor`, `auth set-gemini-key` (getpass), `run <source> --project <path> --model <name> --max-calls <n>`, `resume --project <path>`, `review --project <path>`, `approve <revision> --project <path>`, `export --project <path>`. Review cria relatório HTML estático local com original, previews e contexto ±30 s; sem servidor/API ou desktop.
- [ ] `approve` apresenta os checks da tarefa 5 para confirmação interativa, não adiciona aprovação automática no `run`. Metadata inclui canal/URL/título original/hash e sugestões claramente identificadas como sugestões. Export guarda MP4/ASS/SRT/word JSON/EDL/metadata/QA/manifests por revisão.
- [ ] Reexecutar testes; `autoclip-engine doctor` detecta caminho real de FFmpeg mesmo fora do PATH e registra falta de chave/modelo sem revelá-los. API/Postman e SQLite não estão no aceite desta tarefa.

## Tarefa 8 — vídeo real, auditoria editorial e entrega da PoC

**Files:** criar `tests/real_media/test_pipeline_real.py`, `docs/poc-runbook.md`, `poc-results/summary.json`, `poc-results/editorial-review.json`; ignorar mídia, modelos e secrets no Git. Atualizar `docs/08-validacao.md` com evidência efetiva.

**Interfaces:** consumir CLI/ProjectRun e rubrica de `docs/07-testes-benchmark.md`; produzir relatório final com estados `technical_pass`, `editorial_review_pending|pass|fail`, resultados por corte e limitações. Não transformar aprovação do plano em aprovação editorial dos vídeos.

- [ ] Escrever `test_pipeline_real_source_matches_and_exports_are_traceable` com opt-in para mídia/chave: input hash esperado, nenhuma alteração de fonte, até 3 candidatos válidos, todos outputs mapeados e nenhum media upload. Se não houver chave, indicar skip reason sem alegar execução real.
- [ ] Rodar suite offline `python -m pytest tests/unit tests/integration -q`; PASS. Rodar opt-in real separado quando credencial local estiver disponível; preservar uso/token counts e orçamento de chamadas.
- [ ] Usar fonte `research/media/z0cf-eWBVCo.mp4`, SHA `bc190e8b2d93ab3c3d9d413402d3c11da1a060ea45b2e3ac961f5417cf19c396`, duração 1773,194 s. Reutilizar downloads/modelos existentes, mas transcrever vídeo integral — não converter o smoke de 120 s em avaliação integral.
- [ ] Solicitar a credencial somente por fluxo local seguro. Se ainda não fornecida, concluir todo o motor, testes com stub, previews a partir de EDL manual e preparação do relatório; manter análise real como pendência explícita, sem fabricar resultado.
- [ ] Executar pipeline com modelo Gemini disponível e selecionado na conta; conferir payload textual, metadata de modelo e budget. Provider indisponível interrompe análise e mantém etapas locais concluídas; nenhum gasto além do teto de chamadas autorizado na configuração.
- [ ] Ouvir fonte/contexto e cada preview inteiro; inspecionar começo/fim/frames de legenda. Preencher rubrica com falhas de negação/número/ressalva e ajustes necessários; obter revisão humana para cada aprovação, podendo aceitar zero cortes.
- [ ] Forçar interrupção após ASR e durante render e retomar; verificar hashes e stages reutilizados. Confirmar export local a partir de análise cacheada sem acesso ao Gemini.
- [ ] Registrar comandos, wall time medido, número de revisores, testes/skips/falhas e alcance da PoC. Gate final: técnico PASS e editorial PASS nos cortes aprovados; qualquer pendência mantém estado “PoC não validada integralmente”.

## Rastreabilidade e limites de escopo

| Requisito/gate | Tarefas |
|---|---|
| Núcleo permissivo, provider desacoplado, sem mídia enviada | 1 e 4 |
| Fonte/metadados e ASR local PT-BR | 2 e 3 |
| Trecho contínuo 20–60 s, palavras/ressalvas | 4, 5 e 8 |
| Legendas, MP4, atribuição e rastreabilidade | 5, 6 e 7 |
| Retomada/invalidação/cancel e lote de até 3 | 7 e 8 |
| Sem GPU; teste real antes do desktop | 3, 6 e 8 |
| Remoção segura de pausas e face tracking | M2, explicitamente fora desta PoC |
| SQLite, API/Postman, Vue/Tauri e distribuição | M3–M5; exigem planos próprios depois do gate da PoC |

## Self-review e handoff

Plano revisado contra arquitetura e contratos: cada tarefa produz interface/teste verificável; cinco riscos de entrada cobertos; nenhuma promessa de completude editorial baseada em mocks. Reutilização da base OpenShorts tem arquivos/métodos identificados; nenhuma tarefa depende de módulo comercial. Esta PoC valida motor e fluxo de revisão, sem apresentar fit-blur como tracking ou edição contínua como remoção de pausas.

Recomendação de execução: **nativa**, com as tarefas implementadas por este agente na sequência. As interfaces são dependentes e o escopo é um pipeline único; isso reduz contextos e mantém a evolução dos contratos consistente. Alternativa: subagentes com revisão por tarefa, caso o usuário escolha explicitamente. Revisão independente final conforme a skill de execução escolhida.

Próximo gate: usuário revisa este plano e escolhe execução nativa ou por subagentes. Não instalar dependências de produto, copiar vendor ou criar engine antes desse gate. A arquitetura está aprovada; o plano de implementação ainda não foi aprovado.
