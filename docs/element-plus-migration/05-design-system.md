# AutoClip — Sistema de Design e Integração de Tokens com Element Plus

## 1. Visão Geral e Filosofia Visual

O AutoClip possui uma identidade visual consolidada de **workstation de edição audiovisual dark**, concebida para longas sessões de trabalho sem fadiga ocular. O ecossistema visual baseia-se em:
- **Canvas escuro profundo** (`#0E1013`) com superfícies de elevação calibradas (`#16191F`, `#1E232B`, `#252B35`).
- **Acento cromático âmbar/laranja quente** (`#D97724` / `#F9A35C`), remetendo a hardware de estúdio de pós-produção e fitas de áudio analógicas.
- **Tipografia neutra e tabular** (`Segoe UI`, `system-ui`, `Inter`), otimizada para timestamps e contadores com `font-variant-numeric: tabular-nums`.
- **Bordas sutis com contraste de profundidade** (`#2E3644` e `#475366`), evitando sombras excessivas e brilhos plásticos.

A integração do Element Plus **não altera a identidade do produto**. O Element Plus é uma engine de componentes funcionais e acessíveis; suas variáveis CSS são mapeadas 1:1 com os tokens semânticos existentes do AutoClip (`tokens.css`), garantindo que nenhum componente pareça "genérico", "cinza corporativo claro" ou "estrangeiro" à interface desktop.

---

## 2. Mapeamento de Tokens Semânticos (AutoClip ➔ Element Plus)

O Element Plus utiliza o namespace `--el-*` para todos os aspectos de renderização. Ao carregar `element-plus/theme-chalk/dark/css-vars.css` e sobrepor com um arquivo `desktop/src/element-theme.css`, mapeamos cada variável do Element Plus para os tokens do AutoClip:

### 2.1 Cores Primárias e Acento (Brand Accent)

| Token AutoClip (`tokens.css`) | Valor Hex / RGB | Variável Element Plus (`--el-*`) | Função na Interface |
|---|---|---|---|
| `--color-accent` | `#D97724` | `--el-color-primary` | Ações principais, tabs ativas, links, seleções |
| `--color-accent-hover` | `#BF651B` | `--el-color-primary-light-3` / `--el-color-primary-hover` | Estado hover de botões primários |
| `--color-accent-on` | `#FFFFFF` | `--el-color-white` (em botões primários) | Texto de alto contraste sobre o acento |
| `--color-accent-light` | `#F9A35C` | `--el-color-primary-light-5` | Texto destacado, ícones ativos, badges |
| `--color-accent-soft` | `rgba(217, 119, 36, 0.16)` | `--el-color-primary-light-9` | Background de itens selecionados, chips |
| `--color-accent-subtle` | `rgba(217, 119, 36, 0.12)` | `--el-color-primary-light-8` | Linhas de destaque e foco secundário |
| `--color-border-focus` | `#E08A3C` | `--el-color-primary-dark-2` | Anel de foco visível (focus-ring) |

### 2.2 Superfícies e Backgrounds (Dark Elevation)

| Token AutoClip | Valor Hex | Variável Element Plus | Aplicação |
|---|---|---|---|
| `--color-canvas` | `#0E1013` | `--el-bg-color-page` / `--el-bg-color` | Fundo principal da aplicação (`app-shell`) |
| `--color-surface` | `#16191F` | `--el-bg-color-overlay` | Painéis, cards (`ElCard`), modais (`ElDialog`), gavetas (`ElDrawer`) |
| `--color-surface-raised` | `#1E232B` | `--el-fill-color-light` / `--el-fill-color` | Cabeçalho de tabelas (`ElTable`), steps inativos, inputs |
| `--color-surface-hover` | `#252B35` | `--el-fill-color-dark` / `--el-table-row-hover-bg-color` | Hover em linhas de tabela, botões secundários |

### 2.3 Texto e Tipografia

| Token AutoClip | Valor Hex | Variável Element Plus | Uso |
|---|---|---|---|
| `--color-text-primary` | `#F2F4F7` | `--el-text-color-primary` | Títulos, rótulos de campos, texto ativo |
| `--color-text-secondary` | `#CBD5E1` | `--el-text-color-regular` | Corpo de texto, descrições secundárias |
| `--color-text-muted` | `#A0ABBA` | `--el-text-color-secondary` / `--el-text-color-placeholder` | Placeholders, metadados, timestamps secundários |

### 2.4 Bordas e Divisores

| Token AutoClip | Valor Hex | Variável Element Plus | Uso |
|---|---|---|---|
| `--color-border-subtle` | `#2E3644` | `--el-border-color` / `--el-border-color-light` | Bordas de inputs, botões secundários, separadores |
| `--color-border-strong` | `#475366` | `--el-border-color-darker` / `--el-border-color-dark` | Linhas de cabeçalho de tabela, contorno de popover |

### 2.5 Estados Funcionais (Status / Feedback)

| Estado | Token AutoClip | Valor Hex | Variável Element Plus |
|---|---|---|---|
| **Sucesso** | `--color-success` | `#10B981` | `--el-color-success` |
| Sucesso Suave | `--color-success-soft` | `rgba(16, 185, 129, 0.16)` | `--el-color-success-light-9` |
| Sucesso Borda | `--color-success-border` | `rgba(16, 185, 129, 0.35)` | `--el-color-success-light-8` |
| Sucesso Texto | `--color-success-text` | `#34D399` | `--el-color-success-dark-2` |
| **Aviso** | `--color-warning-text` | `#FBBF24` | `--el-color-warning` |
| Aviso Superfície | `--color-warning-surface` | `rgba(245, 158, 11, 0.14)` | `--el-color-warning-light-9` |
| Aviso Borda | `--color-warning-border` | `rgba(245, 158, 11, 0.35)` | `--el-color-warning-light-8` |
| **Erro / Perigo** | `--color-danger` | `#EF4444` | `--el-color-danger` |
| Perigo Suave | `--color-danger-soft` | `rgba(239, 68, 68, 0.16)` | `--el-color-danger-light-9` |
| Perigo Borda | `--color-danger-border` | `rgba(239, 68, 68, 0.35)` | `--el-color-danger-light-8` |
| Perigo Texto | `--color-danger-text` | `#F87171` | `--el-color-danger-dark-2` |

---

## 3. Implementação Técnica: `element-theme.css`

Para aplicar o mapeamento sem overhead ou seletores complexos, criamos o arquivo [desktop/src/element-theme.css](file:///C:/Users/Matheus/Projects/autoclip-editor/desktop/src/element-theme.css) importado no topo de `main.ts` logo após o dark theme oficial do Element Plus:

```css
/* desktop/src/element-theme.css */
@import 'element-plus/theme-chalk/dark/css-vars.css';

html.dark, :root {
  /* Marca e Destaque */
  --el-color-primary: var(--color-accent);
  --el-color-primary-light-3: var(--color-accent-hover);
  --el-color-primary-light-5: var(--color-accent-light);
  --el-color-primary-light-7: rgba(217, 119, 36, 0.3);
  --el-color-primary-light-8: var(--color-accent-subtle);
  --el-color-primary-light-9: var(--color-accent-soft);
  --el-color-primary-dark-2: var(--color-border-focus);

  /* Superfícies e Fundos */
  --el-bg-color: var(--color-canvas);
  --el-bg-color-page: var(--color-canvas);
  --el-bg-color-overlay: var(--color-surface);
  --el-fill-color: var(--color-surface-raised);
  --el-fill-color-light: var(--color-surface-raised);
  --el-fill-color-dark: var(--color-surface-hover);
  --el-fill-color-blank: var(--color-surface);

  /* Texto */
  --el-text-color-primary: var(--color-text-primary);
  --el-text-color-regular: var(--color-text-secondary);
  --el-text-color-secondary: var(--color-text-muted);
  --el-text-color-placeholder: var(--color-text-muted);

  /* Bordas e Divisores */
  --el-border-color: var(--color-border-subtle);
  --el-border-color-light: var(--color-border-subtle);
  --el-border-color-lighter: var(--color-border-subtle);
  --el-border-color-extra-light: rgba(46, 54, 68, 0.5);
  --el-border-color-dark: var(--color-border-strong);
  --el-border-color-darker: var(--color-border-strong);

  /* Feedback Funcional */
  --el-color-success: var(--color-success);
  --el-color-success-light-9: var(--color-success-soft);
  --el-color-warning: var(--color-warning-text);
  --el-color-warning-light-9: var(--color-warning-surface);
  --el-color-danger: var(--color-danger);
  --el-color-danger-light-9: var(--color-danger-soft);

  /* Raios de Arredondamento */
  --el-border-radius-base: var(--radius-control); /* 8px */
  --el-border-radius-small: 6px;
  --el-border-radius-round: 999px;

  /* Fontes e Tipografia */
  --el-font-family: var(--body);
  --el-font-size-base: 13px;

  /* Sombras */
  --el-box-shadow: var(--shadow-panel);
  --el-box-shadow-light: var(--shadow-panel);
  --el-box-shadow-dark: var(--shadow-floating);

  /* Tabelas */
  --el-table-header-bg-color: var(--color-surface-raised);
  --el-table-header-text-color: var(--color-text-secondary);
  --el-table-tr-bg-color: var(--color-surface);
  --el-table-row-hover-bg-color: var(--color-surface-hover);
  --el-table-border-color: var(--color-border-subtle);
}

/* Customização Específica de Diálogos e Drawers */
.el-dialog, .el-drawer {
  background-color: var(--color-surface) !important;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  box-shadow: var(--shadow-floating);
}

.el-dialog__header, .el-drawer__header {
  border-bottom: 1px solid var(--color-border-subtle);
  margin-bottom: 0;
  padding: 18px 24px;
}

.el-dialog__footer {
  border-top: 1px solid var(--color-border-subtle);
  padding: 14px 24px;
}

/* Tags e Badges */
.el-tag {
  border-radius: 6px;
  font-weight: 500;
}
```

---

## 4. Escalas de Densidade e Dimensões de Componentes

O AutoClip requer alta densidade de informação para permitir que o editor visualize múltiplos tópicos, candidatos de corte e metadados de vídeo simultaneamente.

### 4.1 Tamanho Global dos Controles (`size`)

Configuramos o tamanho padrão como `size="default"` via `ElConfigProvider`:
- **Inputs (`ElInput`, `ElSelect`, `ElInputNumber`)**:
  - `min-height: 36px` (casa perfeitamente com a altura histórica do AutoClip de `36px`).
  - `padding: 0 12px`.
  - `font-size: 13px`.
- **Botões (`ElButton`)**:
  - `default`: `height: 36px`, `font-size: 13px`, `padding: 8px 14px` (Ações principais de tela).
  - `small`: `height: 30px`, `font-size: 12px`, `padding: 4px 10px` (Ações dentro de linhas de tabela, chips e filtros).
  - `large`: reservado apenas para o botão principal de geração final ("Gerar 4 Cortes Selecionados").

### 4.2 Tabela de Alturas e Espaçamentos

```
┌─────────────────────────────────┬───────────┬───────────────┬───────────────────────────────┐
│ Componente                      │ Prop Size │ Altura Real   │ Aplicação                     │
├─────────────────────────────────┼───────────┼───────────────┼───────────────────────────────┤
│ Barra de Busca Principal        │ default   │ 36px          │ LibraryView, TranscriptView   │
│ Selects de Filtro / Ordenação   │ default   │ 36px          │ Cabeçalho da Biblioteca       │
│ Botão Primário ("Novo Projeto") │ default   │ 36px          │ Shell global                  │
│ Ações em Linha (ReviewTable)    │ small     │ 30px          │ Reproduzir, Aprovar, Excluir  │
│ Linha da Tabela de Projetos     │ —         │ 80px (fixa)   │ Thumbnail 16:9 + metadados    │
│ Linha da Tabela de Cortes       │ —         │ 48px          │ Densidade confortável de corte│
│ Card de Candidato de Análise    │ —         │ ~120px        │ Grid de cards na análise      │
└─────────────────────────────────┴───────────┴───────────────┴───────────────────────────────┘
```

---

## 5. Tipografia e Numeração Tabular

Para dados de edição audiovisual (código de tempo, duração, taxas de confiança, métricas de virilidade), números com larguras proporcionais causam tremor visual durante scrub ou atualizações reativas.

1. **Fonte do Corpo e Cabeçalhos**:
   - `var(--body)`: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif`.
   - `font-size-base`: `13px`, `line-height`: `1.5`.
2. **Numeração Tabular para Vídeo**:
   - Para todos os campos de timestamp (`00:01:24`, `00:00:45.300`), contadores de progresso (`45%`, `12/30`) e scores (`8.8 / 10`), a classe `.tabular-nums` ou o estilo `font-variant-numeric: tabular-nums` deve ser aplicado.
3. **Escala de Cabeçalhos**:
   - `h1`: `22px` / peso `600` / `letter-spacing: -0.02em`
   - `h2`: `17px` / peso `600` / `letter-spacing: -0.01em`
   - `h3`: `14px` / peso `600`
   - `label / field`: `12px` / peso `500`
   - `caption / metadata`: `11px` / peso `400` (`--color-text-secondary`)

---

## 6. Gestão de Z-Index e Camada de Teleporte (Teleport & Overlays)

### 6.1 O Problema Histórico
Anteriormente, o AutoClip utilizava tags nativas `<dialog>` para o modal de criação de projeto e onboarding. No navegador Chromium / Tauri WebView2, `<dialog>` é renderizado na *top-layer* do browser. Isso fazia com que toasts de notificação (`vue-sonner`) ficassem ocultos atrás do modal, exigindo um hack complexo de `MutationObserver` em `AppToaster.vue` para tentar reparentar os toasts dinamicamente dentro do diálogo aberto.

### 6.2 A Solução do Element Plus
O Element Plus possui um gerenciador global centralizado de sobreposição: **`PopupManager`**.
- Todos os diálogos (`ElDialog`), gavetas (`ElDrawer`), menus flutuantes (`ElDropdown`), tooltips (`ElTooltip`) e popovers (`ElPopover`) utilizam um z-index incremental gerenciado a partir de uma base configurável.
- `ElNotification` utiliza um z-index superior a qualquer diálogo ativo.
- O z-index base é fixado em `2000` via `ElConfigProvider`:

```html
<!-- desktop/src/App.vue -->
<template>
  <el-config-provider :locale="ptBr" :size="'default'" :z-index="2000">
    <div class="app-shell">
      <!-- Conteúdo da Aplicação -->
    </div>
  </el-config-provider>
</template>
```

**Resultado Arquitetural:**
1. O hack de `MutationObserver` em `AppToaster.vue` é **100% removido**.
2. Notificações disparadas durante o modal de onboarding ou de novo projeto aparecem limpas no canto superior direito, acima do backdrop do modal.
3. Nenhum conflito de z-index ocorre com a barra global sticky (`z-index: 20`).

---

## 7. Interoperabilidade de Ícones: Lucide Vue + Element Plus

O Element Plus possui sua própria biblioteca opcional de ícones (`@element-plus/icons-vue`), porém **não devemos utilizá-la**.
O AutoClip já possui 52 ícones importados e consolidados de `lucide-vue-next` (ex: `Film`, `Sliders`, `Sparkles`, `Trash2`, `Play`, `Check`, `AlertCircle`, etc.).

### 7.1 Como Utilizar Ícones Lucide nos Componentes Element Plus
Todos os componentes do Element Plus (`ElButton`, `ElInput`, `ElSteps`, `ElResult`) aceitam qualquer componente Vue comum através da prop `:icon="Componente"` ou de slots `#prefix` / `#icon`:

```html
<!-- Exemplo 1: Passagem direta como prop em ElButton -->
<script setup lang="ts">
import { Sparkles, Trash2, Play } from 'lucide-vue-next';
</script>

<template>
  <el-button type="primary" :icon="Sparkles">
    Analisar Vídeo
  </el-button>

  <el-button :icon="Trash2" size="small" type="danger" plain />
</template>
```

```html
<!-- Exemplo 2: Slot em ElInput com prefixo -->
<script setup lang="ts">
import { Search } from 'lucide-vue-next';
</script>

<template>
  <el-input v-model="filterText" placeholder="Buscar projetos...">
    <template #prefix>
      <el-icon><Search :size="16" /></el-icon>
    </template>
  </el-input>
</template>
```

Essa abordagem garante zero dependências extras e mantém a linguagem de ícones uniforme em toda a aplicação.

---

## 8. Internacionalização (i18n): Localização Nativa pt-BR

O AutoClip é uma aplicação de língua portuguesa. Todos os componentes interativos do Element Plus (paginação, placeholders de data/hora, mensagens vazias de tabela, botões "OK/Cancelar" de confirmação) devem falar português brasileiro nativamente.

Configuração no ponto de entrada:

```typescript
// desktop/src/App.vue
<script setup lang="ts">
import { ElConfigProvider } from 'element-plus';
import ptBr from 'element-plus/es/locale/lang/pt-br';
</script>

<template>
  <el-config-provider :locale="ptBr">
    <router-view /> <!-- ou telas condicionais do AutoClip -->
  </el-config-provider>
</template>
```

Texto padrão automático:
- `el.table.emptyText`: "Sem dados"
- `el.select.placeholder`: "Selecione"
- `el.messagebox.confirm`: "Confirmar"
- `el.messagebox.cancel`: "Cancelar"
- `el.pagination.total`: "Total {total}"
