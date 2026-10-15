# Redesign Ergonômico do Workspace de Análise (AnalysisPanel)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar os problemas visuais e ergonômicos da tela de análise (`AnalysisPanel.vue`) — substituindo a altura rígida de 560px por layout responsivo adaptável ao viewport, organizando a barra de controles e busca da coluna 2, corrigindo o posicionamento quebrado dos botões da coluna 1, refinando a suíte de inspeção e player da coluna 3, e eliminando a competição visual do dock de geração — mantendo 100% dos testes Vitest verdes.

**Architecture:** Refatoração pontual do template e CSS escopado em `desktop/src/components/AnalysisPanel.vue`. Nenhuma API de backend ou contrato de dados é alterado; todas as ações (`data-action="generate-selected"`, `data-action="select-focused"`, etc.) e estados reativos (`selected`, `discarded`, `topic`, `current`) são estritamente preservados.

**Tech Stack:** Vue 3 (Composition API, `<script setup>`), Element Plus (`el-splitter`, `el-splitter-panel`), Lucide Icons, CSS Scoped com tokens de design do estúdio (`tokens.css`).

**Spec:** Diagnóstico ergonômico da tela de curadoria e auditoria dos defeitos de layout no desktop.

## Global Constraints
- Preservar todos os data-actions e atributos usados pela suíte de testes (`tests/analysis-panel.test.ts` e `tests/review-integration.test.ts`):
  - `data-action="select-focused"`
  - `data-action="generate-selected"`
  - `data-action="generate-selected-dock"`
  - `data-action="resume-analysis"`
  - `data-action="discard-proposal"`
  - `data-action="restore-proposal"`
  - `data-action="discard-topic"`
  - `data-action="restore-topic"`
  - `data-action="select-all-proposals"`
  - `data-action="clear-selection"`
- Respeitar estritamente o design system Linear dark neutro: sem gradientes laranja, sem sombras pesadas estilo neon, bordas nítidas `var(--color-border-subtle)` e `var(--color-border-strong)`.
- Todos os 112 testes Vitest devem permanecer passando ao final de cada tarefa.
- Executar `npm run build` ao finalizar para manter `desktop/dist` sincronizado com o launcher.

## Review Focus
1. **Alturas e Scrollbars Aninhadas:** A tela não pode apresentar dupla barra de rolagem nem cortar o botão de seleção do trecho em resoluções padrão (1080p).
2. **Redimensionamento do Splitter:** As 3 colunas (Temas, Propostas, Inspeção) devem manter layout íntegro mesmo quando o usuário arrasta as divisórias do splitter.
3. **Colisão de Botões na Coluna 1:** O botão de lixeira do tema não pode sobrepor o texto do tema nem o contador numérico.
4. **Alinhamento do Card na Coluna 2:** O checkbox deve estar alinhado com o título, e a seleção ativa não deve deslocar o conteúdo (sem layout jump).
5. **Player de Áudio/Vídeo na Coluna 3:** Os botões "Ouvir trecho" e "Contexto (+15s)" não devem quebrar feio nem vazar quando a coluna de inspeção estiver em largura intermediária.

---

### Task 1: Altura Dinâmica do Workspace e Estrutura do Splitter

**Files:**
- Modify: `desktop/src/components/AnalysisPanel.vue:1040-1090`
- Test: `desktop/tests/analysis-panel.test.ts`

**Interfaces:**
- Consumes: `el-splitter`, `el-splitter-panel`, tokens CSS de superfície e bordas.
- Produces: Layout elástico em tela cheia (`calc(100vh - 210px)` ou `flex: 1`) com container scroll interno independente e limpo para cada coluna.

- [ ] **Step 1: Verificar se os testes existentes de AnalysisPanel passam antes de alterar**

Run: `npx vitest run tests/analysis-panel.test.ts`
Expected: PASS (11 testes)

- [ ] **Step 2: Atualizar CSS do container `.analysis-workspace` e `.curation-3col-layout` em `AnalysisPanel.vue`**

Substituir o bloco rígido:
```css
.analysis-layout.curation-3col-layout {
  height: 560px !important;
  min-height: 520px !important;
  ...
}
```
Por altura responsiva ao viewport de estúdio:
```css
.analysis-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  flex: 1;
  min-height: 0;
}

.analysis-layout.curation-3col-layout {
  height: calc(100vh - 215px) !important;
  min-height: 580px !important;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 12px);
  overflow: hidden;
  box-sizing: border-box;
}
```

- [ ] **Step 3: Ajustar min/max e proporção padrão dos painéis do splitter**

Garantir tamanhos mínimos ergonômicos no `<el-splitter>`:
- Coluna 1 (Temas): `:size="240" :min="180" :max="380"`
- Coluna 2 (Propostas): `:size="380" :min="280" :max="550"`
- Coluna 3 (Inspeção): `:min="380"`

- [ ] **Step 4: Executar testes de AnalysisPanel para validar integridade**

Run: `npx vitest run tests/analysis-panel.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add desktop/src/components/AnalysisPanel.vue
git commit -m "style(curation): make analysis layout responsive to viewport height"
```

---

### Task 2: Correção Ergonômica da Coluna 1 (Temas) e Coluna 2 (Propostas e Filtros)

**Files:**
- Modify: `desktop/src/components/AnalysisPanel.vue:460-725`, `desktop/src/components/AnalysisPanel.vue:1160-1580`
- Test: `desktop/tests/analysis-panel.test.ts`

**Interfaces:**
- Consumes: `visibleTopicGroups`, `filtered`, `filterMode`, `discardTopic`, `restoreTopic`, `selectAllEligible`, `clearSelection`.
- Produces: Coluna 1 com botões de ação de tema organizados sem posicionamento absoluto invasivo (`right: 28px`), e Coluna 2 com toolbar de filtros e cards de proposta sem quebras feias de linha.

- [ ] **Step 1: Ajustar layout de `.topic-chip-container` na Coluna 1**

Remover `position: absolute; right: 28px;` de `.topic-action-icon-btn`.
Estruturar `.topic-chip-container` como flexbox:
```css
.topic-chip-container {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  border-radius: 8px;
  position: relative;
}

.topic-chip-container .topic-chip-btn {
  flex: 1;
  min-width: 0;
}

.topic-action-icon-btn {
  position: static;
  opacity: 0;
  flex-shrink: 0;
  margin-right: 4px;
}
```
Isso garante que o botão só apareça no hover ou quando restaurável, sem invadir o texto do tema ou o contador numérico.

- [ ] **Step 2: Alinhar barra de controles (`.proposals-control-bar`) e campo de busca da Coluna 2**

Estruturar a barra de controle para exibir as abas de filtro (`Ativas`, `Descartadas`, `Todas`) e ações em massa (`Todas`, `Limpar`) de forma coesa, com nowrap e espaçamento equilibrado:
```css
.proposals-control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-shrink: 0;
}
```
Ajustar o input de busca para ter transição suave de foco com a borda do estúdio (`var(--color-border-focus)`).

- [ ] **Step 3: Refinar o Card de Proposta (`.proposal-card`)**

Ajustar `.proposal-top-row` e `.proposal-checkbox-label`:
- Alinhamento vertical do checkbox com o texto do título.
- Adicionar `-webkit-line-clamp: 2` no título para que propostas com nomes muito extensos não estourem a altura do card.
- Substituir `border-left: 2px solid var(--color-text-primary)` no estado `.checked` por `box-shadow: inset 2px 0 0 var(--color-text-primary)` para evitar saltos de layout de 2px no hover/seleção.
- Padronizar badges de tempo, sobreposição e descarte com tipografia mono nítida e cores semáforo elegantes.

- [ ] **Step 4: Executar testes de AnalysisPanel para validar integridade**

Run: `npx vitest run tests/analysis-panel.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add desktop/src/components/AnalysisPanel.vue
git commit -m "style(curation): clean up topic actions, filter bar and proposal cards"
```

---

### Task 3: Refatoração da Coluna 3 (Inspeção Editorial) e Ações de Decisão

**Files:**
- Modify: `desktop/src/components/AnalysisPanel.vue:740-985`, `desktop/src/components/AnalysisPanel.vue:1580-2000`
- Test: `desktop/tests/analysis-panel.test.ts`

**Interfaces:**
- Consumes: `current`, `toggle`, `discard`, `restore`, `play`, `stopAtEnd`, `sourceUrl`.
- Produces: Suíte de inspeção com hierarquia visual clara, mini player com proporções elegantes, e rodapé de ações fixado/visível sem necessidade de rolar a transcrição completa.

- [ ] **Step 1: Otimizar o Mini Player de Audição (`.compact-media-bar`)**

Melhorar o layout do player para ser responsivo:
- Permitir que `.mini-video-frame` mantenha proporção 16:9 (`width: 140px; aspect-ratio: 16/9`) com bordas nítidas e fallback de ícone limpo.
- Em larguras menores que 420px na coluna de inspeção, permitir adaptação graciosa dos botões "Ouvir trecho" e "Contexto (+15s)".
- Manter o timecode claro e mono.

- [ ] **Step 2: Organizar seções editoriais da Inspeção**

Dar respiração visual aos blocos de curadoria:
- **Gancho Social (Primeiros 7 segundos):** Estilo editorial destacado com aspas, itálico e cor de texto primária.
- **Justificativa Editorial e Flags:** Alinhamento limpo das badges "Raciocínio completo: Sim", "Contexto suficiente: Sim", "Ressalvas: Sim".
- **Transcrição e Contexto:** Manter `<details class="proposal-transcript">` colapsável e com tipografia confortável de leitura.

- [ ] **Step 3: Tornar as Ações de Decisão da Proposta (`.inspection-footer-actions`) Imediatamente Acessíveis**

Garantir que a área de ações da proposta focada (`.inspection-footer-actions`) tenha posição sticky no rodapé do container da coluna 3 com backdrop sutil, para que o usuário possa selecionar ou descartar a proposta a qualquer momento, sem ter que rolar 500 linhas de transcrição:
```css
.inspection-footer-actions {
  position: sticky;
  bottom: 0;
  background: var(--color-surface, var(--panel));
  border-top: 1px solid var(--color-border-subtle, var(--line));
  padding: 12px 0 4px;
  z-index: 5;
}
```

- [ ] **Step 4: Harmonizar a barra Dock de Geração (`.curation-dock-bar`)**

Evitar que a dock inferior concorra visualmente com o botão do topo da tela:
- Se houver seleções ativas, a dock atua como barra de status discreta e compacta (padding mais econômico, 8px 16px).
- Manter o botão `data-action="generate-selected-dock"` funcionando perfeitamente para atender tanto ao topo quanto ao rodapé.

- [ ] **Step 5: Executar testes de AnalysisPanel para validar integridade**

Run: `npx vitest run tests/analysis-panel.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add desktop/src/components/AnalysisPanel.vue
git commit -m "style(curation): refine inspection media audition and sticky proposal actions"
```

---

### Task 4: Verificação Completa e Build de Produção

**Files:**
- Test: Toda a suíte de testes Vitest (`desktop/tests/*.test.ts`)
- Build: `desktop/dist`

**Interfaces:**
- Produces: 112/112 testes passando e distribuição pronta para o executável desktop.

- [ ] **Step 1: Rodar suíte completa de testes no diretório `desktop`**

Run: `npm test -- --run`
Expected: 112 passed

- [ ] **Step 2: Gerar build de produção**

Run: `npm run build`
Expected: Vite build succeeds and generates clean bundle in `desktop/dist`.

- [ ] **Step 3: Commit final e confirmação de estabilidade**

```bash
git add desktop/dist
git commit -m "build: update desktop dist with responsive curation workspace"
```
