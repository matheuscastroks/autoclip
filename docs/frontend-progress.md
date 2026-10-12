# Execution ledger — docs/superpowers/plans/2026-10-12-project-manager.md

Spec and native execution plan approved by user. Base commit: 49b2b15.

Ruling: execute in the existing user-approved project/feature branch, preserving the notebook's venv/models/media — another checkout would duplicate runtime setup and break existing local paths; cost if wrong: changes share this feature branch rather than a linked worktree.
Ruling: use a tracked PowerShell-compatible ledger instead of Unix skill bookkeeping scripts — Windows shell and local Git are the existing workflow; cost if wrong: script-generated review metadata must be assembled manually.

Pre-flight Task1→2: registry id/path consumed by jobs; independent of source and ProjectRun IDs. Task2→3: operations and persisted status consumed by typed client; render cannot analyze remotely. Task3→4: production build served by API, token only in fragment/memory. Task4→5: launcher handshake and actual browser validation, no fake completion from endpoint existence.

Task 1: in progress — API/registry tests first; baseline existing suite running.

Task 1: complete — 8 tests observed RED (missing API/dependencies) → GREEN (8 passed). Baseline 52 passed/1 skipped. Registry persists; partial projects honest; media supports signed tickets/Range; secrets omitted. Asyncio socketpair hangs only under restricted sandbox; a minimal FastAPI reproduction confirmed it. API tests run with loopback permitted, no external provider calls.

Task 2: complete — 7 new tests observed RED → GREEN; combined API/budget/boundaries/cache suite 16 passed. Durable counter reserves before transport/retry; single heavy worker, cancel marker/tree grace and interrupted recovery. Analysis requires explicit new text authorization; no implicit remote resume. Audio fixtures initially escaped their project; confined fixtures corrected, storage guard preserved. Native file picker plumbing prepared for Task3.

Task 3: complete — Vue tests observed RED (components absent) → GREEN (7 passed); review API RED → GREEN (2 passed). TypeScript and Vite production build pass; 113.90 kB JS / 41.95 kB gzip. Real window/UI inspection still Task5. Approval click now explicitly checks readiness; async handlers moved to script for vue-tsc. Npm audit reported real issues in Vitest3; upgraded to4.1.11 (audit0), deprecated icon package replaced by official @lucide/vue. No remote provider request.

Task 4: in progress — 4 launcher tests observed RED → GREEN, within combined API suite21 passed. Own-process/session validation, double-click lock and native picker implemented. Actual shortcut/startup verification follows.

Task 4: complete — hidden WScript launcher opened actual service/browser; read-only smoke passed:3 projects,5,414 preserved words,0 jobs/requests,32-byte Range response. Reopening reused session. Workspace-local AutoClip.lnk generated; no system startup/global installation. Browser-panel authentication inspection awaits explicit authorization after automatic approval review rejected printing session token; unaffected tests continue.

Task 5: initial validation complete — full Python74 passed/1 skipped (real Gemini opt-in), Vue7 passed, build/typecheck passed. Actual Chrome already opened by launcher permitted safe UI inspection without token extraction:1366×768 library/workspace/settings/manual preview;390×844 settings with0 overflowing controls; search, timestamp seek22.02s, settings save, empty cuts/manual notice confirmed. Initial token-printing action was rejected; it was not retried/bypassed. User later authorized local authenticated opening, but safer existing-tab workflow required no token extraction.0 actual provider requests; source transcript unchanged.

Final review: one fresh reviewer (gpt-6-astra), base49b2b15..54d47ac. Three Important findings entered ONE fix pass. Five regression cases observed RED: wrong preview after second-clip approval; out-of-order media; independent source/transcript blocked by revisions failure; missing revision directory; old analysis seeded under new model. Fixes preserve selected revision, clear/block media loading and discard obsolete responses; independent artifact loading; contain invalid revision per row; rendering consumes validated original analysis without writing provider cache under current configuration. Targeted2 Python and10 Vue tests GREEN; final complete suite in progress. No second review dispatched.

Final: minor (deferred): textual caption-word and detailed QA-warning panels are not yet displayed; burned captions and technical pass gate are available. Cost: detailed caption/warning inspection still uses artifacts/video until that panel is added.
Final: Ruling: real Gemini selection remains deferred as explicitly requested — no API test costs or fake approval; cost if wrong: semantic quality is still unvalidated.
Final: Ruling: Tauri installer/clean-machine distribution remains next milestone per approved spec — local launcher uses provisioned runtime; cost if wrong: this checkout cannot be distributed as an installer.
Final: Ruling: accept reviewer leaving actual Windows/browser QA to author — existing Chrome, real video/seek, forms and responsive layout checked; native-picker cancel contract tested but not exhaustively automated through Windows UI; cost if wrong: system-dialog behavior needs manual follow-up.
Final: Ruling: preserve explicitly imported original media outside project folders — asset ids whitelist originals and confine generated outputs; cost if wrong: moving that external source requires relinking/new import.
Final: Ruling: use author's full-suite rerun rather than require reviewer rerun writing fixtures — independent source review plus recorded runtime evidence; cost if wrong: reviewer has no separate test-execution provenance.

Final: fixed preview/decision mismatch and obsolete responses — review-integration.test.ts first two tests RED→GREEN; selected revision and loaded video stay bound and approval is blocked during loading.
Final: fixed render poisoning changed-model cache — test_precomputed_analysis_does_not_seed_current_model_cache RED→GREEN; existing analysis provenance preserved, no analyze stage cache written by render.
Final: fixed damaged preview blocking original/transcript — test_missing_revision_is_an_invalid_row_not_a_project_failure and Vue independent-artifact regression RED→GREEN.
Task 5: complete — final Python76 passed/1 skipped in144.33s; Vue10 passed; vue-tsc/Vite build pass. Current bundle114.82kB JS/42.23kB gzip. Actual idle service restarted into corrected code and new Chrome tab retained as deliverable; second read-only smoke3 projects5,414words0jobs0requests passed. Native create-project modal inspected and cancel confirmed; viewport reset. Logs/media/model/secret paths untracked. User-requested local branch preserved; no push or merge.

12/10/2026 — Fluxo aprovado entregue: progresso na sidebar, preparação automática até análise para novos vídeos, capas FFmpeg e lixeira reversível de projetos/cortes. Revisão independente encontrou três regressões; todas corrigidas com testes. Validação final: Python94 passou/1 geração real ignorada; Vue18 passou; TypeScript/Vite passou. Aplicativo final aberto em Chrome; worker de transcrição preexistente preservado por PID/data de criação durante atualização do servidor. Nenhuma nova análise Gemini iniciada pelo agente. Evidência em poc-results/frontend/workflow-validation.md. Trabalhos anteriores não são convertidos implicitamente em análise automática com novo orçamento.

12/10/2026 — Duração preferida/máxima até180s, redução conservadora de pausas verificada com VAD+volume+palavras e feedback Gemini em streaming implementados após aprovação. Histórico local paginado por trabalho/janela/tentativa, temas e propostas somente após validar JSON; resumos ausentes, parciais ou de cache identificados. Revisão independente: timeout de processo corrigido para retry contado; inspeção visual: falha da análise não marca etapas pendentes/concluídas como falhas. Python106 passou/1 geração real ignorada; Vue25 passou; TypeScript/Vite passou. Render real multispan e Silero local passaram. API metadata confirmou thinking=true no Gemini2.5Flash; agente não gerou conteúdo real nem alterou o limite de chamadas escolhido pelo usuário. Evidência em poc-results/frontend/editorial-feedback-validation.md.


## 2026-10-12 — Chamadas automáticas, sem checkbox

- Novas tarefas da interface dimensionam chamadas pelas janelas reais da transcrição; limite legado salvo não restringe o planejamento. Até duas tentativas de transporte e uma reparação de JSON por janela; falhas persistentes encerram a análise. Nenhum retry infinito.
- Criação e análise não exigem checkbox de envio nem limite manual; texto sobre o uso da API continua nos formulários. CLI/API preservam limites explicitamente informados.
- Retomada de análise cria um novo trabalho/ledger automático; histórico e tarefas antigas são preservados. Planejamento e consumo real aparecem na sidebar e no histórico.
- Verificação: 27 testes Vue e build passaram; suíte Python final teve 107 passes, 1 skip (Gemini real opt-in) e 1 PermissionError temporário de Windows em test_failed_producer_does_not_become_checkpoint. Reexecução desse teste e das duas suítes API modificadas: 16 passes. Relatórios python-tests.xml e automatic-confirm.xml preservam ambos os resultados.
- Serviço atualizado e saudável; formulário real inspecionado no navegador, sem checkbox ou limite. Nenhuma geração Gemini foi disparada durante a validação.


## 2026-10-12 — Layout 50/50 e feedback estável

- Causa reproduzida: INSERT OR REPLACE alterava rowid, e ORDER BY rowid mudava o trabalho considerado mais recente em cada consulta. Corrigido com UPSERT e ordenação por created_at/id; interface também seleciona por data.
- Conteúdo mantém chunks recebidos ao avançar o tail de 100 eventos da API, com cache de sessão limitado a 2.000 eventos. Novas tentativas permanecem separadas; histórico completo continua paginado.
- Autoscroll pausável, scrollbar oculta, região focável para teclado e indicação de status separada do texto. Etapas compactas e colunas 50/50, responsivas. Parâmetros de janela/chars em ajustes avançados com explicação.
- Regressões RED/GREEN: ordenação após quatro consultas, seleção diante de respostas reordenadas, retenção de chunks, autoscroll e pausa/retomada. Verificação final: 30 testes Vue, 16 testes API jobs/workflow e 2 de feedback/histórico passaram; vue-tsc e Vite build passaram.
- Inspeção real: 606,4 px por coluna; nenhum overflow horizontal; scrollbar-width none; scrollTop acompanhando o fim. Serviço atualizado e saudável. Nenhuma chamada de geração disparada na verificação; a falha PROVIDER_UNAVAILABLE da análise anterior é preservada, sem confundi-la com erros antigos de orçamento.


## 2026-10-12 — Painel sem histórico visível

Removidos o botão de histórico, modal, seleção de trabalhos antigos e sua navegação no frontend. Mantidos resumo atual, temas, propostas, indicação de análise parcial, autoscroll e revisão de cortes. Endpoint e logs locais são preservados para diagnóstico interno. O frontend não consulta o endpoint paginado de histórico. Os 30 testes Vue passaram; regressões verificam ausência do botão e do modal sem afetar o feedback atual. Nenhuma geração Gemini disparada.


## 2026-10-12 — Recuperação de falhas repetidas Gemini

- Diagnóstico confirmado nas últimas quatro tarefas reais: TimeoutError na primeira janela, após aproximadamente 60 segundos por tentativa; nenhuma janela foi validada. Configuração anterior pedia thinking_budget=-1.
- Correção: timeout padrão 180 segundos, orçamento de pensamento 2048 nos modelos 2.5 compatíveis e nível baixo em 3 compatíveis, independente da visibilidade. Modelos sem suporte não recebem os parâmetros. Limite de saída 16384 tokens e detecção explícita MAX_TOKENS; erro acionável.
- Prompt recebe transcrição inteira como contexto global em cada janela e remove regra de três propostas. IDs aceitos continuam limitados à janela. Seleção final mantém suas regras existentes.
- Checkpoints atômicos por resposta validada, digest e chave de transcrição/modelo/prompt/schema/runtime, cobertura e proveniência preservadas. Retomada não repete janela aceita; orçamento confere apenas janelas pendentes. Sem reutilização de JSON parcial ou resumos. Botão Continuar análise e marcação de resultado reaproveitado.
- RED/GREEN comprovou retomada sob novo orçamento, invalidação e corrupção, contexto completo, truncamento e modelos sem suporte. Suíte: 113 Python passaram, 1 opt-in real foi ignorado; 30 Vue passaram; build/TypeScript passaram. Revisão independente identificou dois pontos de compatibilidade de thinking, ambos corrigidos e retestados.
- Teste real tentou ser solicitado, mas a revisão automática de aprovação rejeitou iniciar geração por falta de autorização atual segundo seu critério; comando não executado, nenhuma solicitação gerada. Serviço/interface locais foram atualizados sem chamada remota. Validação real permanece pendente de aprovação expressa.


## 2026-10-12 — Validação real concluída e JSON compacto

Após aprovação expressa, a execução real enviou somente texto ao Gemini 2.5 Flash. Duas chamadas de diagnóstico atingiram MAX_TOKENS. Telemetria confirmou pensamento1593, saída14770 tokens: o schema permitia listas de evidência/contexto sem limite. Corrigido com max8 IDs/lista e instrução de preservar todo o start/end; não encurta fala. Primeira janela real validada em cerca de30 segundos, saída2663tokens.

Execução concluída: 7/7janelas, 5556/5556palavras, 19propostas. Total11/28tentativas autorizadas;9 na execução concluída, incluindo2reparações de JSON. Teste local reutilizou7checkpoints com chamada remota proibida e0solicitações. Seleção existente de3 planos:51,46/59,34/100,06s. MP4 não gerado; revisão humana pendente. Interface Concluído/Analisado, sem aviso antigo, Gerar prévias habilitado.

Correção adicional do aviso antigo foi RED→GREEN em execução e conclusão. Suíte final115Python/1skip,32Vue e compilação passaram. Revisão adicional sem defeitos materiais. Relatórios real-gemini-recovery.md/json e python-tests.xml registram o resultado, sem credenciais.
