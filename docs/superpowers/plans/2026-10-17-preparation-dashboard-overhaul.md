# Implementação do Redesenho da Aba Preparação (Central de Setup & Raio-X do Vídeo)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar a aba Preparação do AutoClip em uma Central de Setup & Raio-X do Vídeo focada no criador de conteúdo, eliminando telemetria técnica de baixo nível e oferecendo conferência de mídia, análise temática e diretrizes de saída dos shorts.

**Architecture:** Decomposição modular da aba em componentes focados: Stepper horizontal de 4 macro-etapas (`PipelineMilestoneStepper.vue`), Player de conferência de mídia (`SourceMediaCard.vue`), Raio-X temático do conteúdo (`ContentXRayCard.vue`), Seletores visuais de estilo e ritmo dos shorts (`OutputGuidelinesCard.vue`) e Cartão de Ação Primária com diagnóstico técnico sob demanda em Drawer (`PrimaryActionCard.vue`).

**Tech Stack:** Vue 3 (Composition API, `<script setup lang="ts">`), TypeScript, Vitest, `@vue/test-utils`.

**Spec:** `docs/superpowers/specs/2026-10-17-preparation-dashboard-overhaul-design.md`

## Global Constraints
- Seguir estritamente o design system do AutoClip: uso de tokens CSS (`--color-surface`, `--color-canvas`, `--color-action-primary`, `--radius-panel`).
- Preservar todos os eventos emitidos para `ProjectWorkspace.vue`: `transcribe`, `analyze`, `render`, `review`, `cancel`, `resume`, `replaceSource`.
- Manter acessibilidade: foco via teclado, atributos `aria-*`, labels semânticos e tags semânticas HTML5.
- Não introduzir dependências externas adicionais no `package.json`.

## Review Focus
1. Quando o projeto estiver no estado inicial `imported` (sem transcrição), o Raio-X deve exibir mensagem informativa acolhedora sem erros de renderização.
2. A seleção de preset de legenda e velocidade no `OutputGuidelinesCard` deve emitir eventos corretos e manter sincronia visual imediata.
3. Se um job estiver em execução (`running`), o botão de ação deve refletir estado ativo com barra de progresso suave e botão de cancelamento funcional.
4. O link "Ver diagnóstico técnico" deve abrir o drawer de telemetria sem desviar o fluxo do usuário ou recarregar a página.
5. Em resoluções menores (< 1000px), o grid de 2 colunas deve se adaptar graciosamente para 1 coluna vertical mantendo o player visível.

---

### Task 1: Stepper de Macro-Etapas (`PipelineMilestoneStepper.vue`)

**Files:**
- Create: `desktop/src/components/pipeline/PipelineMilestoneStepper.vue`
- Test: `desktop/tests/pipeline-milestone-stepper.test.ts`

**Interfaces:**
- Props:
  ```typescript
  defineProps<{
    status: ProjectStatus;
    hasTranscript: boolean;
    hasAnalysis: boolean;
    hasCuts: boolean;
    busy?: boolean;
    activeOperation?: string | null;
  }>();
  ```
- Steps calculados: `Mídia Importada`, `Transcrição`, `Análise IA`, `Cortes Prontos`.

- [ ] **Step 1: Escrever teste de unidade para o Stepper**

```typescript
// desktop/tests/pipeline-milestone-stepper.test.ts
import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import PipelineMilestoneStepper from '../src/components/pipeline/PipelineMilestoneStepper.vue';

it('renders 4 human-friendly steps and flags current progress correctly', () => {
  const w = mount(PipelineMilestoneStepper, {
    props: {
      status: 'transcribed',
      hasTranscript: true,
      hasAnalysis: false,
      hasCuts: false,
    },
  });

  const steps = w.findAll('.milestone-step');
  expect(steps).toHaveLength(4);
  expect(steps[0].text()).toContain('Mídia Importada');
  expect(steps[0].classes()).toContain('is-completed');
  expect(steps[1].text()).toContain('Transcrição');
  expect(steps[1].classes()).toContain('is-completed');
  expect(steps[2].text()).toContain('Análise IA');
  expect(steps[2].classes()).toContain('is-current');
  expect(steps[3].text()).toContain('Cortes Prontos');
  expect(steps[3].classes()).toContain('is-pending');
});
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `npm --prefix desktop run test:run -- tests/pipeline-milestone-stepper.test.ts`  
Expected: FAIL (componente inexistente).

- [ ] **Step 3: Implementar `PipelineMilestoneStepper.vue`**

Criar `desktop/src/components/pipeline/PipelineMilestoneStepper.vue` com barra de progresso horizontal e estados visuais claros (`completed`, `current`, `pending`, `failed`).

- [ ] **Step 4: Executar teste para verificar aprovação**

Run: `npm --prefix desktop run test:run -- tests/pipeline-milestone-stepper.test.ts`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add desktop/src/components/pipeline/PipelineMilestoneStepper.vue desktop/tests/pipeline-milestone-stepper.test.ts
git commit -m "feat(desktop): add human-friendly pipeline milestone stepper"
```

---

### Task 2: Card de Mídia Original e Metadados (`SourceMediaCard.vue`)

**Files:**
- Create: `desktop/src/components/pipeline/SourceMediaCard.vue`
- Test: `desktop/tests/source-media-card.test.ts`

**Interfaces:**
- Props:
  ```typescript
  defineProps<{
    sourceUrl?: string;
    durationUs?: number;
    wordCount?: number;
    title?: string;
  }>();
  ```

- [ ] **Step 1: Escrever teste de unidade para `SourceMediaCard`**

```typescript
// desktop/tests/source-media-card.test.ts
import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import SourceMediaCard from '../src/components/pipeline/SourceMediaCard.vue';

it('renders video element and human-readable metadata badges', () => {
  const w = mount(SourceMediaCard, {
    props: {
      sourceUrl: '/videos/sample.mp4',
      durationUs: 125_000_000, // 2m 5s
      wordCount: 350,
      title: 'Entrevista Podcast',
    },
  });

  expect(w.find('video').exists()).toBe(true);
  expect(w.text()).toContain('2:05');
  expect(w.text()).toContain('350 palavras');
});
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `npm --prefix desktop run test:run -- tests/source-media-card.test.ts`  
Expected: FAIL.

- [ ] **Step 3: Implementar `SourceMediaCard.vue`**

Criar `desktop/src/components/pipeline/SourceMediaCard.vue` com o player de vídeo 16:9, fallback quando sem mídia, e grade de badges de metadados legíveis.

- [ ] **Step 4: Executar teste para verificar aprovação**

Run: `npm --prefix desktop run test:run -- tests/source-media-card.test.ts`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add desktop/src/components/pipeline/SourceMediaCard.vue desktop/tests/source-media-card.test.ts
git commit -m "feat(desktop): add source media conference card"
```

---

### Task 3: Card de Raio-X & Tópicos Identificados (`ContentXRayCard.vue`)

**Files:**
- Create: `desktop/src/components/pipeline/ContentXRayCard.vue`
- Test: `desktop/tests/content-xray-card.test.ts`

**Interfaces:**
- Props:
  ```typescript
  defineProps<{
    hasTranscript: boolean;
    analysis?: AnalysisView | null;
    wordCount?: number;
  }>();
  defineEmits<{
    openTranscript: [];
    openAnalysis: [];
  }>();
  ```

- [ ] **Step 1: Escrever teste para `ContentXRayCard`**

```typescript
// desktop/tests/content-xray-card.test.ts
import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import ContentXRayCard from '../src/components/pipeline/ContentXRayCard.vue';

it('displays friendly placeholder before analysis and shows topic chips when ready', async () => {
  const w = mount(ContentXRayCard, {
    props: {
      hasTranscript: true,
      analysis: {
        state: 'completed',
        proposals: [
          { candidate_id: 'c1', topic_title: 'Produtividade Pessoal' },
          { candidate_id: 'c2', topic_title: 'Dicas de Foco' },
        ],
        topics: [
          { id: 't1', title: 'Produtividade Pessoal' },
          { id: 't2', title: 'Dicas de Foco' },
        ],
      } as any,
    },
  });

  expect(w.text()).toContain('Produtividade Pessoal');
  expect(w.text()).toContain('Dicas de Foco');
  expect(w.text()).toContain('2 propostas de cortes');

  const btn = w.get('[data-action=open-transcript]');
  await btn.trigger('click');
  expect(w.emitted('openTranscript')).toBeTruthy();
});
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `npm --prefix desktop run test:run -- tests/content-xray-card.test.ts`  
Expected: FAIL.

- [ ] **Step 3: Implementar `ContentXRayCard.vue`**

Criar `desktop/src/components/pipeline/ContentXRayCard.vue` exibindo lista de tópicos em chips, total de propostas e botão de atalho para a transcrição.

- [ ] **Step 4: Executar teste para verificar aprovação**

Run: `npm --prefix desktop run test:run -- tests/content-xray-card.test.ts`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add desktop/src/components/pipeline/ContentXRayCard.vue desktop/tests/content-xray-card.test.ts
git commit -m "feat(desktop): add content x-ray and topics card"
```

---

### Task 4: Card de Diretrizes de Saída dos Cortes (`OutputGuidelinesCard.vue`)

**Files:**
- Create: `desktop/src/components/pipeline/OutputGuidelinesCard.vue`
- Test: `desktop/tests/output-guidelines-card.test.ts`

**Interfaces:**
- Props:
  ```typescript
  defineProps<{
    selectedPreset?: string;
    selectedSpeed?: string;
  }>();
  defineEmits<{
    'update:preset': [preset: string];
    'update:speed': [speed: string];
  }>();
  ```

- [ ] **Step 1: Escrever teste para `OutputGuidelinesCard`**

```typescript
// desktop/tests/output-guidelines-card.test.ts
import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import OutputGuidelinesCard from '../src/components/pipeline/OutputGuidelinesCard.vue';

it('allows choosing caption preset and playback speed', async () => {
  const w = mount(OutputGuidelinesCard, {
    props: {
      selectedPreset: 'karaoke-yellow-v1',
      selectedSpeed: '1.0x',
    },
  });

  expect(w.text()).toContain('Karaoke');
  expect(w.text()).toContain('1080×1920 (9:16)');

  const minimalPreset = w.get('[data-preset=clean-white-v1]');
  await minimalPreset.trigger('click');
  expect(w.emitted('update:preset')?.[0]).toEqual(['clean-white-v1']);
});
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `npm --prefix desktop run test:run -- tests/output-guidelines-card.test.ts`  
Expected: FAIL.

- [ ] **Step 3: Implementar `OutputGuidelinesCard.vue`**

Criar `desktop/src/components/pipeline/OutputGuidelinesCard.vue` com seletor dos 4 presets validados, botões de velocidade (1.0x, 1.1x, 1.15x) e indicador visual de enquadramento 9:16.

- [ ] **Step 4: Executar teste para verificar aprovação**

Run: `npm --prefix desktop run test:run -- tests/output-guidelines-card.test.ts`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add desktop/src/components/pipeline/OutputGuidelinesCard.vue desktop/tests/output-guidelines-card.test.ts
git commit -m "feat(desktop): add output guidelines card for caption presets and speed"
```

---

### Task 5: Card de Ação Primária & Diagnóstico Técnico (`PrimaryActionCard.vue` e `TechnicalDiagnosticsDrawer.vue`)

**Files:**
- Create: `desktop/src/components/pipeline/PrimaryActionCard.vue`
- Create: `desktop/src/components/pipeline/TechnicalDiagnosticsDrawer.vue`
- Test: `desktop/tests/primary-action-card.test.ts`

**Interfaces:**
- Props:
  ```typescript
  defineProps<{
    status: ProjectStatus;
    hero: PipelineHero;
    technicalSteps: PipelineStep[];
    busy?: boolean;
  }>();
  defineEmits<{
    action: [value: PipelineAction];
  }>();
  ```

- [ ] **Step 1: Escrever teste para `PrimaryActionCard`**

```typescript
// desktop/tests/primary-action-card.test.ts
import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import PrimaryActionCard from '../src/components/pipeline/PrimaryActionCard.vue';

it('renders context-aware action button and reveals technical drawer on demand', async () => {
  const w = mount(PrimaryActionCard, {
    props: {
      status: 'transcribed',
      hero: {
        title: 'Transcrição Concluída',
        description: 'Pronto para analisar ganchos.',
        state: 'ready',
        primary: { id: 'analyze', label: 'Buscar Cortes com IA', disabled: false },
        secondary: [],
      },
      technicalSteps: [],
      busy: false,
    },
  });

  const btn = w.get('[data-action=primary-action]');
  expect(btn.text()).toBe('Buscar Cortes com IA');
  await btn.trigger('click');
  expect(w.emitted('action')).toBeTruthy();

  // Test technical details link exists
  const link = w.get('[data-action=open-diagnostics]');
  await link.trigger('click');
  expect(w.find('.diagnostics-drawer').exists()).toBe(true);
});
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `npm --prefix desktop run test:run -- tests/primary-action-card.test.ts`  
Expected: FAIL.

- [ ] **Step 3: Implementar `PrimaryActionCard.vue` e `TechnicalDiagnosticsDrawer.vue`**

Criar os componentes com botão primário limpo, progresso suave em linguagem natural e drawer lateral para visualização dos logs técnicos sob demanda.

- [ ] **Step 4: Executar teste para verificar aprovação**

Run: `npm --prefix desktop run test:run -- tests/primary-action-card.test.ts`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add desktop/src/components/pipeline/PrimaryActionCard.vue desktop/src/components/pipeline/TechnicalDiagnosticsDrawer.vue desktop/tests/primary-action-card.test.ts
git commit -m "feat(desktop): add primary action card with on-demand technical diagnostics"
```

---

### Task 6: Integração no `PipelinePanel.vue` e Verificação E2E do Dashboard

**Files:**
- Modify: `desktop/src/components/PipelinePanel.vue`
- Test: `desktop/tests/preparation.test.ts`
- Test: `desktop/tests/project-tabs.test.ts`

- [ ] **Step 1: Atualizar `PipelinePanel.vue` para integrar a nova arquitetura em 2 colunas**

Substituir o layout antigo pelo novo arranjo:
- `PipelineMilestoneStepper` no topo.
- Coluna esquerda: `SourceMediaCard` e `ContentXRayCard`.
- Coluna direita: `OutputGuidelinesCard` e `PrimaryActionCard`.

- [ ] **Step 2: Executar testes de preparação existentes e novos**

Run: `npm --prefix desktop run test:run -- tests/preparation.test.ts tests/project-tabs.test.ts`  
Ajustar eventuais seletores caso os testes anteriores buscassem nós legados de telemetria.

- [ ] **Step 3: Executar typecheck e suite completa**

Run: `npm --prefix desktop run check`  
Run: `npm --prefix desktop run test:run`  
Expected: 0 erros, todos os testes passando.

- [ ] **Step 4: Commit**

```bash
git add desktop/src/components/PipelinePanel.vue desktop/tests/preparation.test.ts
git commit -m "feat(desktop): assemble preparation dashboard into video setup and content x-ray"
```
