# Design Spec: AutoClip UI Redesign — Phase 1 (Visual Foundations & Neutral Tokens)

- **Date:** 2026-10-14
- **Branch:** `poc-openshorts-gemini`
- **Target Phase:** PR 1 — Fundamentos Visuais
- **Status:** Approved by user

---

## 1. Context & Motivation

A auditoria de UI/UX do AutoClip identificou que, apesar de melhorias anteriores, a aplicação ainda exibe sintomas de "AI slop":
- Laranja como identidade de interação (`#d97724`, `rgba(217, 119, 36, ...)`, `#f9a35c`).
- Abas e seleções com fundos e bordas coloridas competindo por atenção.
- Gradiente decorativo roxo/laranja no painel de prontidão em `App.vue`.
- Animações de pulsação e brilho decorativo em filas e badges.
- Cores de destaque e bordas hardcoded espalhadas por múltiplos componentes Vue.

A Fase 1 estabelece os fundamentos visuais sóbrios, densos e quase monocromáticos inspirados na precisão do Linear, com canvas `#0D0F11`, superfícies `#16181B`, seleção neutra por contraste `#292D32` e ação primária em cinza-claro `#E5E7EB`.

O critério de aceitação primordial do PR 1 é: **nenhuma tela depende do laranja para indicar ação ou seleção, e todos os 106 testes automatizados permanecem verdes**.

---

## 2. Token Architecture (`tokens.css`)

Substituição da paleta de raiz com semântica estrita:

```css
:root {
  /* Canvas e Superfícies Sóbrias */
  --color-canvas: #0d0f11;
  --color-surface: #16181b;
  --color-surface-raised: #1c1f23;
  --color-surface-hover: #23262a;
  --color-surface-selected: #292d32;

  /* Bordas Sutis e Delimitadores */
  --color-border-subtle: rgba(255, 255, 255, 0.07);
  --color-border-strong: rgba(255, 255, 255, 0.14);

  /* Tipografia e Contraste */
  --color-text-primary: #eceef0;
  --color-text-secondary: #a5abb3;
  --color-text-muted: #858c95;

  /* Ação Primária Monocromática */
  --color-action-primary: #e5e7eb;
  --color-action-primary-hover: #f3f4f6;
  --color-action-primary-text: #111317;

  /* Foco Acessível & Neutro */
  --color-focus-ring: #b8c0ca;
  --color-border-focus: rgba(229, 231, 235, 0.35);

  /* Feedback Funcional Controlado */
  --color-warning-surface: rgba(245, 158, 11, 0.08);
  --color-warning-border: rgba(245, 158, 11, 0.2);
  --color-warning-text: #fbbf24;

  --color-danger: #f87171;
  --color-danger-soft: rgba(239, 68, 68, 0.08);
  --color-danger-border: rgba(239, 68, 68, 0.2);
  --color-danger-text: #f87171;

  --color-success: #34d399;
  --color-success-soft: rgba(16, 185, 129, 0.08);
  --color-success-border: rgba(16, 185, 129, 0.2);
  --color-success-text: #34d399;

  /* Variáveis de Compatibilidade (Sem Laranja) */
  --color-accent: var(--color-action-primary);
  --color-accent-hover: var(--color-action-primary-hover);
  --color-accent-soft: var(--color-surface-hover);
  --color-accent-subtle: var(--color-surface-raised);
  --color-accent-text: var(--color-text-primary);
  --color-accent-light: var(--color-text-primary);
  --color-accent-on: var(--color-action-primary-text);
  --accent: var(--color-accent);
  --accent-hover: var(--color-accent-hover);
  --accent-soft: var(--color-accent-soft);
  --accent-on: var(--color-accent-on);
  --accent-light: var(--color-accent-light);
  --blue: var(--color-accent);
  --focus-ring: var(--color-focus-ring);

  /* Geometria e Superfícies */
  --radius-control: 6px;
  --radius-panel: 8px;
  --shadow-panel: none;
  --shadow-floating: 0 12px 32px rgba(0, 0, 0, 0.45);
}
```

---

## 3. Element Plus Overrides (`element-theme.css`)

Neutralização dos componentes do Element Plus:
1. **`--el-color-primary`**: mapeado para `--color-action-primary` (`#e5e7eb`), com variantes claras e escuras derivadas de superfícies cinzas.
2. **Botões:**
   - `.el-button--primary`: Fundo `#e5e7eb`, cor do texto `#111317`, hover `#f3f4f6`, sem borda ou com borda idêntica ao fundo.
   - `.el-button` default: Fundo `#1c1f23` ou transparente, borda `var(--color-border-subtle)`, texto `var(--color-text-primary)`. Hover com fundo `var(--color-surface-hover)`.
3. **Abas (`.el-tabs`):**
   - Eliminação de qualquer borda inferior colorida/laranja (`--el-color-primary`).
   - Abas destacadas exclusivamente por contraste tipográfico (`#eceef0` ativo vs `#858c95` inativo) e marcador sutil neutro.
4. **Controles de Seleção (Checkboxes, Switches, Radios):**
   - Indicador de seleção neutro (branco/cinza contrastante com check escuro), sem `accent-color` laranja.
5. **Diálogos, Drawers e Dropdowns:**
   - Fundo `var(--color-surface)`, bordas `var(--color-border-subtle)`, sem gradientes ou elevações excessivas.

---

## 4. Remoção de Gradientes, Pulsing e Estilos Hardcoded

### 4.1. `theme.css`
- Remoção de keyframes pulsantes (`@keyframes pulse-subtle`, `@keyframes pulse-dot`, `@keyframes border-glow`, etc.) contendo laranjas e gradientes.
- Indicadores de fila e renderização passam a ser estáticos e discretos.

### 4.2. `App.vue`
- Substituição do gradiente da seção de prontidão (`linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(217, 119, 36, 0.06) 100%)`) por superfície sólida `var(--color-surface)` com borda sutil `var(--color-border-subtle)`.
- Fila global: linha lateral neutra estática, sem animação contínua de pulsação.

### 4.3. Componentes Específicos
- **`AnalysisPanel.vue`:**
  - Substituição de `border-left: 3px solid var(--color-accent, #d97724)` e fundos `rgba(217, 119, 36, ...)` por `background: var(--color-surface-selected)` e marcador neutro.
  - Eliminação de `accent-color: var(--color-accent, #d97724)` em inputs/checkboxes.
- **`PipelinePanel.vue`:**
  - Remoção de `color="#d97724"`, bordas e fundos laranjas de etapas ativas; substituição por estados neutros ativos (`var(--color-surface-selected)` / `var(--color-text-primary)`).
  - Remoção da porcentagem arbitrária fictícia `percentage="75"`.
- **`ReviewPanel.vue`:**
  - Remoção de `color="#d97724"`, brilho (`box-shadow: 0 0 6px rgba(217, 119, 36, 0.6)`) e borda esquerda laranja de corte selecionado.
- **`ProjectLibrary.vue`:**
  - Remoção da borda esquerda grossa laranja (`4px solid #d97724`) nos cards de projetos; substituição por seleção sutil neutra.
- **`ProviderSelector.vue` & `SettingsPanel.vue`:**
  - Substituição de bordas e fundos laranjas de seleção por `--color-border-strong` e `--color-surface-selected`.
- **`GlobalQueueModal.vue`, `OnboardingModal.vue`, `ApiKeyField.vue`, `ProjectWorkspace.vue`:**
  - Remoção de props `:color="'#D97724'"` e cores de foco residuais.

---

## 5. Non-Goals (Fases Futuras)

Nesta Fase 1 **não** faremos:
- Refatoração ou fatiamento da árvore de componentes (deixado para PR 2, 3 e 4).
- Alteração nos contratos de API, composables ou gerenciamento de estado.
- Alteração de rotas ou criação de novos fluxos de navegação.

---

## 6. Verification & Quality Gates

1. **Testes Unitários e de Integração:** Execução de `npm test -- --run` no diretório `desktop`. Todos os 106 testes devem continuar passando.
2. **Inspeção de Cores:** Nenhuma ocorrência de `#d97724`, `rgba(217, 119, 36`, `#f9a35c` ou `linear-gradient` laranja/roxo deve permanecer ativa em `desktop/src`.
3. **Contraste e Foco:** Todos os controles interativos mantêm navegabilidade por teclado e anel de foco visível (`--color-focus-ring: #b8c0ca`).
