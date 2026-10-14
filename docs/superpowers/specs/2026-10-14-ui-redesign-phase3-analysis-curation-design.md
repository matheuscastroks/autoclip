# Design Spec: AutoClip UI Redesign — Phase 3 (Analysis & Curation Redesign)

- **Date:** 2026-10-14
- **Branch:** `poc-openshorts-gemini`
- **Target Phase:** PR 3 — Análise e Curadoria (`AnalysisPanel.vue`)
- **Status:** Approved by user

---

## 1. Context & Motivation

A auditoria de UI/UX do AutoClip identificou a tela de **Análise e Curadoria** (`AnalysisPanel.vue`) como a mais prioritária do redesign.

A estrutura de três colunas (Temas, Propostas e Inspeção) é conceitualmente sólida, mas a lista central de propostas acumulava excesso de ruído: checkbox, título, intervalo, duração, justificativa extensa (`rationale`), transcrição e alertas duplicados dezenas de vezes.

A Fase 3 separa definitivamente:
- **Identificação da proposta** na coluna central (rápida, compacta, visualmente limpa).
- **Avaliação da proposta** na coluna de inspeção (player em destaque, justificativa editorial, transcrição contextual, social hook e ações editoriais).

---

## 2. Hierarchy of the 3 Columns

### Coluna 1: Navegação por Temas
- Lista vertical de grupos de tópicos (`.topic-list`) com contagens numéricas discretas.
- Seleção por contraste tipográfico e fundo sutil `var(--color-surface-hover)`.

### Coluna 2: Lista Central de Propostas
- Cada item (`.proposal-card`) é estritamente uma linha de identificação e seleção rápida:
  - Checkbox nativo com estilo neutro (`input[type=checkbox]`).
  - Botão de abertura para inspeção com título da proposta (`.proposal-open`).
  - Metadados temporais compactos: Início (`04:12`) · Duração (`0:58`).
  - Alerta fino apenas em caso de sobreposição (`Sobrepõe seleção`) ou inelegibilidade.
  - Ação de descarte/restauração (`data-action="discard-proposal"`, `data-action="restore-proposal"`) integrada de forma discreta.
- O texto longo de `rationale`, transcrição e contexto é **removido** da lista central e realocado exclusivamente para a inspeção.
- Filtros segmentados compactos: *"Ativas"*, *"Descartadas"* e *"Todas"* estilizados como controle segmentado discreto no topo da lista.

### Coluna 3: Painel de Inspeção do Corte
- Visualização dedicada do corte selecionado para avaliação profunda:
  - Player de vídeo estável com controles e timecodes (`04:12 – 05:10`).
  - Gancho de abertura para redes sociais (`.opening-copy` com estimativa de retenção).
  - Justificativa editorial detalhada da IA (`rationale`).
  - Trecho transcrito completo com contexto anterior e posterior (`context_before`, `context_after`).
  - Botão primário para incluir/remover corte da seleção final (`data-action="select-focused"`).

---

## 3. Top / Bottom Summary & Action Bar

- Resumo direto no cabeçalho ou barra de fixação:
  `{{ totalProposals }} propostas · {{ selectedCount }} selecionadas`
- Botão de ação primário:
  `Gerar {{ selectedCount }} corte(s)` (`data-action="generate-selected"`), habilitado apenas quando houver propostas elegíveis selecionadas e análise completa.
- Atalhos rápidos:
  `Selecionar todas` (`data-action="select-all-proposals"`), `Limpar` (`data-action="clear-selection"`).
- Retomada de análise parcial com 1 clique (`data-action="resume-analysis"`).

---

## 4. Verification & Quality Gates

1. **Testes de Análise:** `tests/analysis-panel.test.ts` e `tests/analysis-feedback.test.ts` passam 100%.
2. **Suíte Completa:** Todos os 20 arquivos de teste (110 testes) continuam passando.
3. **Ausência de Poluição Visual:** Nenhuma repetição de blocos longos de justificativa editorial dentro da lista central de propostas.
