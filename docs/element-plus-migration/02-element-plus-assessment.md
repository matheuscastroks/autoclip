# Avaliação Técnica do Element Plus para o AutoClip

> **Documento:** `docs/element-plus-migration/02-element-plus-assessment.md`  
> **Status:** Concluído / Estudo de Compatibilidade  
> **Referência Oficial:** [https://element-plus.org/en-US/component/overview](https://element-plus.org/en-US/component/overview)

---

## 1. Matriz de Compatibilidade Técnica

A compatibilidade do Element Plus (versão `>= 2.9.x`) com o ecossistema atual do AutoClip foi minuciosamente checada:

| Tecnologia no AutoClip | Versão Atual no Projeto | Requisito do Element Plus | Situação |
| :--- | :--- | :--- | :--- |
| **Vue** | `^3.5.43` | `>= 3.2.0` (suporta 3.4 e 3.5) | **100% Compatível** |
| **Vite** | `^7.3.7` | `>= 4.0.0` (suporta Vite 5, 6 e 7) | **100% Compatível** |
| **TypeScript** | `^5.9.3` | `>= 5.0.0` | **100% Compatível** (tipagens completas de props e eventos) |
| **Tauri** | `^2.12.2` (WebView2 Windows) | Chromium / Evergreen Web standards | **100% Compatível** (Tauri 2 utiliza o WebView2 moderno do Edge) |
| **Vitest** | `^4.1.11` + `jsdom` | jsdom `>= 20` | **100% Compatível** com mocks de ResizeObserver |

---

## 2. Estratégia de Importação e Impacto no Bundle

O Element Plus oferece duas abordagens principais de importação:

### 2.1 Importação Completa (Full Import)
* **Como funciona:** Registra todos os componentes globalmente via `app.use(ElementPlus)` e importa `element-plus/dist/index.css`.
* **Vantagens:** Configuração inicial rápida; não exige plugins extras no `vite.config.ts`.
* **Desvantagens no AutoClip:**
  - Adiciona ~2.8 MB de JavaScript sem compressão (~850 KB comprimido) e ~500 KB de CSS contendo dezenas de componentes desnecessários (DatePicker, Cascader, ColorPicker, TreeSelect, Transfer, etc.).
  - Como o AutoClip é distribuído como executável desktop standalone via PyInstaller e Tauri, aumentar desnecessariamente os arquivos estáticos de `desktop/dist` compromete o tempo de inicialização da janela.

### 2.2 Importação Sob Demanda (On-Demand com Tree-Shaking) — **RECOMENDADA**
* **Como funciona:** Utiliza os plugins oficiais `unplugin-vue-components` e `unplugin-auto-import` com o resolvedor `ElementPlusResolver`.
```typescript
// desktop/vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver({ importStyle: 'css' })],
    }),
    Components({
      resolvers: [ElementPlusResolver({ importStyle: 'css' })],
    }),
  ],
  // ...
})
```
* **Impacto no tamanho:**
  - O Vite inclui apenas os componentes efetivamente consumidos no código.
  - O peso adicional no bundle final cai para aproximadamente **180 KB - 280 KB**, mantendo a compilação do desktop instantânea e reduzindo o consumo de memória no WebView2 do Windows.

---

## 3. Arquitetura de Dark Mode e Design Tokens

O AutoClip possui uma identidade visual estritamente escura com destaque âmbar/laranja (`--color-accent: #D97724`), voltada para uso contínuo em edição audiovisual (estilo DaVinci Resolve / Premiere Pro).

### 3.1 Mecanismo Oficial de Tema Escuro do Element Plus
O Element Plus 2.x suporta modo escuro nativo baseado em variáveis CSS:
1. Importa-se o pacote de variáveis dark: `import 'element-plus/theme-chalk/dark/css-vars.css'`.
2. Aplica-se a classe `dark` no elemento raiz `<html>` ou `<html class="dark">`.

### 3.2 Mapeamento Semântico para os Tokens do AutoClip
Não faremos overrides frágeis com `!important`. A personalização será feita mapeando as variáveis oficiais do Element Plus diretamente para os tokens existentes em `desktop/src/tokens.css`:

```css
/* desktop/src/element-theme.css */
html.dark {
  /* Cores de Marca / Acento */
  --el-color-primary: var(--color-accent); /* #D97724 */
  --el-color-primary-light-3: var(--color-accent-text); /* #F9A35C */
  --el-color-primary-light-5: rgba(217, 119, 36, 0.5);
  --el-color-primary-light-7: rgba(217, 119, 36, 0.3);
  --el-color-primary-light-9: var(--color-accent-soft); /* rgba(217, 119, 36, 0.16) */
  --el-color-primary-dark-2: var(--color-accent-hover); /* #BF651B */

  /* Superfícies e Fundos */
  --el-bg-color-page: var(--color-canvas); /* #0E1013 */
  --el-bg-color: var(--color-surface); /* #16191F */
  --el-bg-color-overlay: var(--color-surface-raised); /* #1E232B */

  /* Tipografia e Textos */
  --el-text-color-primary: var(--color-text-primary); /* #F2F4F7 */
  --el-text-color-regular: var(--color-text-secondary); /* #CBD5E1 */
  --el-text-color-secondary: var(--color-text-muted); /* #A0ABBA */

  /* Bordas e Divisores */
  --el-border-color: var(--color-border-subtle); /* #2E3644 */
  --el-border-color-light: var(--color-border-subtle);
  --el-border-color-dark: var(--color-border-strong); /* #475366 */

  /* Arredondamento */
  --el-border-radius-base: var(--radius-control); /* 8px */
  --el-border-radius-small: 6px;
  --el-border-radius-round: 20px;

  /* Estados Semânticos */
  --el-color-success: var(--color-success); /* #10B981 */
  --el-color-warning: var(--color-warning-text); /* #FBBF24 */
  --el-color-danger: var(--color-danger); /* #EF4444 */
}
```

---

## 4. Localização (i18n) em Português do Brasil

O Element Plus possui suporte nativo ao idioma português brasileiro via pacote oficial:
```typescript
import ptBr from 'element-plus/es/locale/lang/pt-br'
```
No `App.vue`, envolveremos a aplicação com o `<el-config-provider>`:
```vue
<template>
  <el-config-provider :locale="ptBr">
    <div class="app-shell">
      <!-- conteúdo da aplicação -->
    </div>
  </el-config-provider>
</template>
```
**Benefícios imediatos:**
- Paginação de tabelas traduzida automaticamente ("Total 15", "Página 1 de 3").
- Textos padrão de busca e seleção ("Sem dados", "Selecione").
- Confirmações e botões de modais ("Confirmar", "Cancelar").

---

## 5. Interoperabilidade de Ícones: Lucide Vue vs Element Plus Icons

* **Situação Atual:** O AutoClip utiliza `@lucide/vue` com 20+ ícones bem integrados (`Scissors`, `Sparkles`, `Clock`, `Film`, `RotateCcw`, `HardDrive`, etc.).
* **Decisão Arquitetural:** **Manter 100% dos ícones no `@lucide/vue`.**
* **Justificativa:** Todos os componentes do Element Plus (`ElButton`, `ElInput`, `ElTag`, `ElAlert`, etc.) aceitam qualquer componente Vue como prop `icon` ou slot `#icon`. Por exemplo:
  ```vue
  <el-button :icon="Sparkles" type="primary">Analisar</el-button>
  <el-input :prefix-icon="Search" v-model="query" placeholder="Buscar cortes..." />
  ```
  Não há nenhuma necessidade de instalar `@element-plus/icons-vue`. Isso preserva a harmonia visual dos ícones e evita inchar as dependências.

---

## 6. Comportamento no Ambiente Desktop (Tauri 2 + WebView2)

### 6.1 Teleport e Gestão de Z-Index
* **No código antigo:** Modais nativos `<dialog>` ocupavam a *Top Layer* do browser, forçando um hack de `MutationObserver` em `AppToaster.vue` para mover toasts para dentro do `<dialog>`.
* **No Element Plus:** `ElDialog`, `ElDrawer`, `ElMessageBox` e `ElNotification` utilizam um gerenciador de z-index centralizado (`PopupManager`, base `2000`). Toasts e notificações sempre flutuam sobre diálogos abertos, garantindo feedback consistente sem hacks no DOM.

### 6.2 Seleção de Arquivos e o Componente `ElUpload`
* **Limitação Identificada:** `ElUpload` foi projetado para aplicações web onde o usuário envia arquivos para um backend remoto via `multipart/form-data` (`POST /api/upload`).
* **Regra no AutoClip:** O AutoClip é uma aplicação desktop estritamente local. Os vídeos nunca são enviados via HTTP multipart; o usuário escolhe um arquivo no disco e o motor Python acessa diretamente o caminho absoluto via FFmpeg.
* **Diretriz:**
  - Para cliques em "Selecionar Arquivo", **manter a chamada nativa do sistema operacional (`api.pick('video')`)**, que abre a caixa de diálogo nativa do Windows Explorer via Rust.
  - O `ElUpload` pode ser utilizado **estritamente como zona de drag-and-drop visual**, configurado com `:auto-upload="false"`, interceptando o evento `@change` ou `on-drop` para extrair o caminho do arquivo sem disparar requisição HTTP.

---

## 7. Análise de Recursos Experimentais / Beta

### 7.1 `ElSplitter` (Beta na documentação)
* **Avaliação:** Introduzido recentemente no Element Plus para divisão de painéis redimensionáveis (splitter horizontal/vertical).
* **Risco:** Sendo um recurso beta, pode apresentar instabilidades em redimensionamentos extremos ou conflitos com o player de vídeo HTML5 (que recalcula aspect ratio continuamente).
* **Decisão:** Realizar um teste isolado na Fase 1 (PoC). Caso apresente problemas, utilizaremos um divisor flexbox simples com CSS `resize` ou `vue-resizable-panels`, sem bloquear a migração dos demais componentes.

### 7.2 `ElTableV2` (Virtual Table)
* **Avaliação:** Tabela virtualizada para renderizar milhares de linhas simultaneamente.
* **Necessidade real no AutoClip:** A biblioteca de um usuário típico contém entre 5 a 50 projetos, e a análise gera entre 10 a 60 propostas de corte.
* **Decisão:** **Não utilizar `ElTableV2`.** O `ElTable` padrão atende perfeitamente ao volume de dados do AutoClip, com suporte maduro a templates customizados, seleção múltipla e ordenação. A transcrição longa (com milhares de palavras) é renderizada em lista de blocos de fala com rolagem virtual nativa, não em formato tabular.

---

## 8. Inventário de Dependências Elimináveis

Com a adoção do Element Plus, as seguintes bibliotecas e códigos manuais poderão ser eliminados:

| Dependência / Código | Status Atual | Destino após a Migração | Economia |
| :--- | :--- | :--- | :--- |
| `reka-ui` | `^2.11.0` | **Remover do `package.json`** (substituído por `ElSelect`) | ~120 KB bundle / 1 dependência a menos |
| `AppButton.vue` | Custom (6 linhas) | Consolidar em `ElButton` | Código e CSS customizado eliminados |
| `AppSelect.vue` | Custom (21 linhas) | Substituir por `ElSelect` | 10 componentes primitivos removidos |
| `MutationObserver` no `AppToaster.vue` | Hack no DOM | **Remover** (z-index nativo do Element Plus) | Elimina risco de vazamento de memória |
| CSS de tabelas e botões em `theme.css` | ~350 linhas CSS | **Eliminar** em favor dos tokens do Element Plus | CSS mais limpo e padronizado |
