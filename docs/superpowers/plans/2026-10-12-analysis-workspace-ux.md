# Analysis Workspace UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exibir temas e propostas antes da geração, permitir seleção explícita e acompanhar processamento/revisão/exportação com estados distintos.

**Architecture:** API local projeta artefatos validados em uma visão de análise; seleção pertence ao hash dessa análise. O motor recebe candidatos explícitos e publica progresso estruturado por corte. A interface consome esses contratos sem usar logs brutos ou disparar Gemini ao navegar.

**Tech Stack:** Vue 3, TypeScript, CSS existente, Python/FastAPI, contratos Pydantic, SQLite/JSON local, FFmpeg.

**Spec:** ../specs/2026-10-12-analysis-workspace-ux-design.md

**Status:** planejamento proposto; nenhum item implementado neste documento. Execução padrão inline com executing-plans; delegação depende das instruções aplicáveis e da autorização necessária. Esta entrega não inicia implementação.

## Global Constraints

- Manter Visão geral 50/50 em desktop e empilhar em telas menores.
- Sem histórico visível, consentimento por checkbox ou limite manual de chamadas.
- Ler resultados não dispara Gemini; geração usa análise completa existente.
- Original e transcrição permanecem íntegros; nenhum corte é aprovado automaticamente.
- Não mostrar percentuais ou previsão de tempo sem medição.
- Seleção manual explícita não sofre limite silencioso de 3 candidatos.
- Resultados de lotes anteriores, revisão e checkpoints permanecem preservados.
- Sem dependências de UI novas e sem alteração de modelo/chave.

## Review Focus

1. Resultado antigo não pode aparecer como nova análise parcial ou como erro atual.
2. Troca de modelo/transcrição/análise não reutiliza uma seleção desatualizada.
3. Uma falha/cancelamento de lote não perde cortes já prontos ou aprovados.
4. Atualizações não roubam foco, mudam a aba ou alteram o candidato selecionado.
5. Campos/counters refletem resultados validados; resumos e sugestões não significam aprovação editorial.

## Task 1 — Contrato e leitura da análise atual

**Files:** criar engine/api/analysis_view.py e tests/api/test_analysis_view.py; modificar engine/api/app.py, engine/adapters/gemini/analyzer.py, engine/api/job_worker.py, desktop/src/types.ts e desktop/src/api.ts.

**Interfaces:** GET /api/v1/projects/{pid}/analysis retorna AnalysisView schema_version 1.0: state (not_started/running/partial/completed/failed/cancelled), job_id, analysis_hash (null enquanto parcial), model, completed_windows, total_windows, topic_groups e proposals. ProposalView inclui candidate_id, topic_ids, title, rationale, start_us, end_us, duration_us, word IDs, eligibility e reasons. Estruturas finais derivam de AnalysisArtifact/TranscriptArtifact; dados parciais de um snapshot validado do trabalho atual (analysis-preview.json), não de resumos nem de um tail truncado de logs.

- [ ] Escrever casos RED: 19 propostas do fixture visíveis sem render; duração medida nos words; agrupamento não elimina negações; janela incompleta não publica proposta; novo trabalho parcial não usa resultado antigo.
- [ ] Implementar projeção e snapshot atômico das janelas aceitas, mantendo IDs consistentes entre snapshot e artefato final. Agrupar conservadoramente rótulos equivalentes, preservando IDs originais.
- [ ] Validar origem/hash/referências e autenticação local existente; sem provider calls.
- [ ] Executar `.venv/Scripts/python.exe -X utf8 -m pytest tests/api/test_analysis_view.py -q` com basetemp no workspace e permissões de testes locais adequadas.
- [ ] Verificar fixtures corrompidos/ausentes com estado acionável; commit independente.

**Aceite:** resultados do vídeo real podem ser lidos sem gerar MP4, chamar Gemini ou navegar no histórico.

## Task 2 — Seleção explícita persistida e geração dos escolhidos

**Files:** criar engine/api/analysis_selection.py, tests/api/test_analysis_selection.py e tests/unit/test_explicit_selection.py; modificar engine/api/app.py, engine/api/job_worker.py, engine/pipeline/runner.py, engine/editorial/select.py e desktop/src/types.ts/api.ts.

**Interfaces:** PUT /api/v1/projects/{pid}/analysis-selection recebe schema_version, analysis_hash e candidate_ids; grava analysis-selection.json com validação. JobOptions para render aceita analysis_hash/candidate_ids. Engine run_project recebe seleção explícita opcional e a valida contra o artefato. Implementar validate_explicit_candidates(analysis, transcript, config, candidate_ids) -> CandidateArtifact: aplica IDs, duração e flags, sem usar max_clips automático; chamadas legadas sem seleção mantêm comportamento anterior.

- [ ] RED para seleção persistida, análise desatualizada rejeitada, IDs desconhecidos, critérios de duração/contexto e lote com mais de 3 escolhidos.
- [ ] Implementar distinção de elegibilidade técnica/editorial e limitação de lote; sobreposição é aviso na seleção manual, não exclusão silenciosa. Não remover palavras ou relaxar flags atuais sem decisão editorial explícita.
- [ ] Implementar geração somente dos IDs escolhidos; verificar hash na inicialização e antes de montar EDL.
- [ ] Testar que render não chama Gemini; preservar revisão/artefatos de candidatos não escolhidos em novo lote.
- [ ] Executar testes focados da API, seletor e integração; commit independente.

**Aceite:** escolher 6 sugestões elegíveis gera exatamente essas 6, sem sumir com outras prévias. Nova análise inválida a seleção antiga com mensagem clara.

## Task 3 — Nova aba Análise e navegação contextual

**Files:** criar desktop/src/components/AnalysisPanel.vue e desktop/tests/analysis-panel.test.ts; modificar ProjectWorkspace.vue, PipelinePanel.vue, AnalysisFeedback.vue, App.vue, styles.css e os testes de navegação existentes.

**Interfaces:** AnalysisPanel consome AnalysisView/Selection, sourceUrl e feedback atual; emite select, generate, seek-original e continue-analysis. GETs e PUT de escolha são locais. O player limita o trecho selecionado e permite conferir antes/depois no original.

- [ ] RED: quarta aba, lista de temas/propostas, detalhe de evidências, busca/filtro, reprodução no original, seleção múltipla e CTA Gerar N prévias.
- [ ] Construir lista/detalhe adaptável; agrupar e contar temas sem afirmar que entradas por janela são temas únicos. Implementar navegação por teclado nas abas (setas/Home/End), painel associado e foco visível.
- [ ] Mover o resumo longo para Análise; Visão geral mantém resumo compacto e ação Ver análise. Remover linguagem que sugere que uma proposta já é corte renderizado.
- [ ] Preservar filtros, seleção e posição de leitura em refresh; avisos/ações contextualizados para estados vazio/parcial/interrompido.
- [ ] Executar `npm test -- --run` e `npm run build` em desktop; commit independente.

**Aceite:** os 19 candidatos do fixture são examináveis antes de renderização; consulta/reprodução não faz chamada ao Gemini. Navegação e leitura funcionam durante análise.

## Task 4 — Progresso medido por etapa e por corte

**Files:** criar engine/pipeline/progress.py e tests/unit/test_pipeline_progress.py; modificar engine/api/job_worker.py, engine/api/jobs.py, engine/pipeline/runner.py, engine/render/ffmpeg.py e engine/pipeline/cancellation.py; adicionar testes em tests/integration/test_render_progress.py.

**Interfaces:** ProgressSnapshot 1.0 inclui operation, phase, current_candidate_id, current_index, total_items, completed_items, failed_items, processed_us, total_us e activity_at. Fases de geração: edit_plan, pauses, captions, render e verify. Renderizador recebe callback opcional de progresso; parsing de FFmpeg é numérico, nunca repassa stderr bruto.

- [ ] RED para progressão monotônica, duração da EDL após pausas, fases sem percentual, MAX/fim da codificação antes da verificação e cancelamento sem bloquear leitura dos pipes.
- [ ] Emitir snapshots atômicos reais do motor, incluindo cache reused sem fingir renderização nova.
- [ ] Usar protocolo `-progress` do FFmpeg com leitura que não bloqueie stdout/stderr ou cancelamento; medir out_time_us versus EDL.
- [ ] Testar um vídeo sintético pequeno por CLI/API, falha técnica e subprocesso encerrado. Não anunciar acompanhamento facial inexistente.
- [ ] Rodar testes de progresso, cancelamento e render existente; commit independente.

**Aceite:** a UI sabe qual corte/etapa está em execução; percentual de renderização tem origem real. Não tratar 100% de codificação como prévia tecnicamente aprovada.

## Task 5 — Fila de geração, revisão e exportação distintas

**Files:** criar desktop/src/components/GenerationQueue.vue e desktop/tests/generation-queue.test.ts; modificar PipelinePanel.vue, ProjectWorkspace.vue, ReviewPanel.vue, App.vue, styles.css, engine/api/reviews.py e testes de preservação de revisões.

**Interfaces:** fila consome ProgressSnapshot + seleção + revisões; emite cancel/retry-failed/open-revision. Revisões prontas mantêm candidate_id/revision_id/checks/content_hash; decisões existentes continuam vinculadas à revisão.

- [ ] RED: estados aguardando/processando/pronto/falhou por candidato, reexecução só dos falhos, outros resultados consultáveis, revisão não concluída pelo worker.
- [ ] Separar Gerar prévias, Revisar cortes e Exportar na sidebar; apresentação compacta da etapa atual e próxima ação.
- [ ] Na aba Cortes, filtros Em geração/Para revisar/Aprovados/Exportados; liberar prévias assim que cada verificação concluir, sem esperar o lote inteiro.
- [ ] Preservar cortes de lotes anteriores e aprovações de revisões não alteradas; geração/cancelamento nunca apagam esses dados.
- [ ] Expor erros localizados e ação Retomar pendentes; exportação mostra pacotes concluídos e mantém bloqueio editorial atual.
- [ ] Testar revisão/exportação existentes, cancelamento e lotes parciais; commit independente.

**Aceite:** falha em 1 de 6 cortes não bloqueia os 5 prontos. Ao terminar geração, a UI informa que falta revisão humana, sem declarar o projeto concluído/publicável.

## Task 6 — Validação da experiência integrada

**Files:** ampliar desktop/tests/workflow.test.ts, review-integration.test.ts e novos testes de análise/fila; criar tests/integration/test_analysis_to_review_flow.py; atualizar docs/frontend-runbook.md e relatório poc-results/frontend/analysis-workspace-ux-validation.md.

- [ ] Testar fluxo transcrição → análise parcial/completa → escolha → geração parcial → revisão → exportação, com fixtures e provider proibido quando apenas navegando/renderizando.
- [ ] Verificar recuperação após fechamento da aba/reinício, escolha persistida, análise alterada, erro e cancelamento.
- [ ] Validar teclado, status acessível, pausa do autoscroll e ausência de troca automática de aba/foco.
- [ ] Inspecionar visualmente 1440×900, 1366×768 e 390×844: sem overflow/clipping, botões acessíveis e estado atual legível. Resetar overrides após verificação.
- [ ] Usar análise real já salva de 19 propostas como teste de leitura; render sintético curto para telemetria. Não iniciar nova geração Gemini paga para QA sem autorização aplicável.
- [ ] Rodar pytest completo, Vitest e build; registrar evidência real e limitações; commit de validação.

**Aceite global:** usuário identifica o que o modelo encontrou, o que escolheu, o que está sendo processado, o que já pode revisar e o que pode exportar, sem terminal, histórico de falhas ou loading como único feedback.

## Ordem de entrega

Primeira entrega útil: tarefas 1–3 (Análise e escolha). Segunda: tarefas 4–5 (progresso por corte e revisão separada). Encerramento: tarefa 6. Cada entrega mantém a navegação atual funcional. O plano não exige refazer a interface desktop inteira.
