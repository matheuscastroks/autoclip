# Inventário de Componentes e Funcionalidades do AutoClip

> **Documento:** `docs/element-plus-migration/01-component-inventory.md`  
> **Status:** Concluído / Levantamento Atualizado  
> **Repositório:** `matheuscastroks/autoclip` (`poc-openshorts-gemini` @ commit `11cb4fa`)

---

## 1. Visão Geral do Frontend

O frontend do AutoClip é uma aplicação desktop desenvolvida em **Vue 3 (Composition API com `<script setup>`)**, **TypeScript 5.9**, **Vite 7** e **Tauri 2**. Toda a interface gráfica comunica-se localmente com o motor FastAPI via loopback (`http://127.0.0.1:<port>`).

### 1.1 Pilha de Dependências de Interface Atual

| Pacote | Versão | Responsabilidade |
| :--- | :--- | :--- |
| `vue` | `^3.5.43` | Framework reativo e Composition API |
| `@lucide/vue` | `^1.55.0` | Conjunto consistente de ícones vetoriais |
| `reka-ui` | `^2.11.0` | Primitivas headless utilizadas exclusivamente no `AppSelect.vue` |
| `vue-sonner` | `^2.0.9` | Notificações toast consumidas por meio do `AppToaster.vue` |
| `CSS Nativo` | Custom | Três arquivos de estilização: `tokens.css`, `layouts.css` e `theme.css` |

---

## 2. Inventário Componente a Componente

Abaixo está o mapeamento detalhado dos 15 componentes Vue existentes em `desktop/src/components/` e da raiz `desktop/src/App.vue`.

---

### 2.1 `AppButton.vue`
* **Caminho:** `desktop/src/components/AppButton.vue` (6 linhas, 216 bytes)
* **Responsabilidade:** Wrapper elementar de `<button>` que injeta a classe `.ui-control` e permite herança de atributos nativos (`inheritAttrs: true`).
* **Onde é utilizado:** Em praticamente todos os componentes (80+ ocorrências).
* **Controles HTML / Libs:** Elemento HTML `<button>` nativo.
* **Funcionalidades manuais:** Nenhuma além da classe CSS. Não gerencia variantes, tamanhos, foco, acessibilidade ou estado `loading` de forma estruturada. As classes CSS (`.button.primary`, `.button.secondary`, `.button.small`, `.icon-button`, `.text-button`) estão dispersas em `theme.css`.
* **Acessibilidade:** Delega integralmente ao desenvolvedor; foco gerenciado via CSS global.
* **Classificação:** **Substituição direta** por [`ElButton`](https://element-plus.org/en-US/component/button). Pode-se manter temporariamente um wrapper `AppButton.vue` redirecionando para `el-button` para evitar quebra de 80 arquivos de uma só vez.

---

### 2.2 `AppSelect.vue`
* **Caminho:** `desktop/src/components/AppSelect.vue` (21 linhas, 2.030 bytes)
* **Responsabilidade:** Seletor dropdown personalizado construído com primitivas headless do Reka UI.
* **Onde é utilizado:** Em `SettingsPanel.vue` (seleção de modelos Gemini/OpenRouter, modos de corte) e `ProjectLibrary.vue` (filtros de estado e ordenação).
* **Controles HTML / Libs:** Importa 10 componentes primitivos de `reka-ui`: `SelectRoot`, `SelectTrigger`, `SelectPortal`, `SelectContent`, `SelectViewport`, `SelectItem`, `SelectItemText`, `SelectItemIndicator`, `SelectScrollUpButton`, `SelectScrollDownButton`, além de ícones Lucide.
* **Funcionalidades manuais:**
  - Montagem de portal flutuante com cálculo de colisão e offset (`side-offset="8"`, `collision-padding="12"`).
  - Scroll buttons manuais para listas longas.
  - Formatação e mapeamento de `modelValue` com opção selecionada.
* **Estilos CSS:** ~120 linhas em `theme.css` dedicadas a estilizar o trigger, viewport, hover, foco e scroll buttons do Reka UI.
* **Testes associados:** `desktop/tests/app-select.test.ts` (verifica `role=combobox`, `role=listbox`, navegação por setas `ArrowDown`, seleção via `Enter` e opções desabilitadas).
* **Classificação:** **Substituição direta** por [`ElSelect`](https://element-plus.org/en-US/component/select) e [`ElOption`](https://element-plus.org/en-US/component/select#option-attributes). Com essa substituição, a dependência `reka-ui` pode ser completamente eliminada do projeto.

---

### 2.3 `AppToaster.vue`
* **Caminho:** `desktop/src/components/AppToaster.vue` (25 linhas, 2.462 bytes)
* **Responsabilidade:** Host de renderização dos avisos toast disparados pelo serviço centralizado `desktop/src/notifications.ts`.
* **Onde é utilizado:** Montado na raiz do `App.vue`.
* **Controles HTML / Libs:** `vue-sonner` (`<Toaster>`).
* **Funcionalidades manuais:**
  - **MutationObserver Hack (linhas 5–10):** Monitora a abertura de tags `<dialog open>` nativas do navegador para teleportar o container de toast para dentro do diálogo aberto, contornando a limitação do navegador em que `<dialog>` bloqueia o z-index da camada superior.
* **Acessibilidade:** Possui atalho de teclado `Alt+T` e container com `aria-label`.
* **Testes associados:** `desktop/tests/app-toast.test.ts` e `desktop/tests/toaster-host.test.ts`.
* **Classificação:** **Substituição com adaptação** por [`ElNotification`](https://element-plus.org/en-US/component/notification) / [`ElMessage`](https://element-plus.org/en-US/component/message). Como o Element Plus gerencia z-index dinâmico (z-index manager centralizado em `2000+`), ele flutua naturalmente acima de `ElDialog` e `ElDrawer`, eliminando a necessidade do hack de MutationObserver. O adaptador `notifications.ts` preserva a interface de chamada (`notify.success`, `notify.error`, etc.).

---

### 2.4 `ProjectLibrary.vue`
* **Caminho:** `desktop/src/components/ProjectLibrary.vue` (677 linhas, 20.750 bytes)
* **Responsabilidade:** Biblioteca principal de projetos. Permite buscar por texto, filtrar por status, ordenar, alternar entre grade de cards e lista tabular, ver miniaturas geradas, excluir projetos e acessar a fila global.
* **Controles HTML / Libs:** Inputs de texto nativos, `AppSelect.vue`, `AppButton.vue`, ícones Lucide.
* **Funcionalidades manuais:**
  - Alternador de visualização Grade/Lista feito com botões e classes CSS manuais.
  - Campo de busca manual com debounce e filtragem em memória.
  - Carregamento assíncrono de thumbnails com cache local e detecção de imagem quebrada (`brokenCovers`).
  - Badge pulsante de tarefas ativas em segundo plano.
  - Tabela manual de projetos (linhas 130–210) montada com tags `<table>`, `<tr>`, `<td>` e estilos próprios.
  - Estado vazio (`v-if="!filtered.length"`) desenhado manualmente com SVGs e textos.
* **Classificação:** **Composição híbrida**:
  - Filtros e ordenação: [`ElInput`](https://element-plus.org/en-US/component/input) com prefix-icon e [`ElSelect`](https://element-plus.org/en-US/component/select).
  - Alternador de visão: [`ElSegmented`](https://element-plus.org/en-US/component/segmented).
  - Visualização em lista: [`ElTable`](https://element-plus.org/en-US/component/table) com colunas ordenáveis e tags de status [`ElTag`](https://element-plus.org/en-US/component/tag).
  - Visualização em grade: Preservar card customizado com thumbnail de vídeo 16:9, badges de status e progresso.
  - Estado vazio: [`ElEmpty`](https://element-plus.org/en-US/component/empty).
  - Confirmação de exclusão: [`ElPopconfirm`](https://element-plus.org/en-US/component/popconfirm).

---

### 2.5 `App.vue` (Diálogos Globais & Shell)
* **Caminho:** `desktop/src/App.vue` (757 linhas, 36.466 bytes)
* **Responsabilidade:** Shell principal do aplicativo, cabeçalho de navegação, roteamento de telas (`projects`, `settings`), polling de estado do motor (3s), inicialização, e controle de 3 diálogos principais:
  1. **Criar Novo Projeto (`dialog`):** Importação por arquivo local ou URL do YouTube, validação de link, nome do projeto e resumo do pipeline.
  2. **Analisar com IA (`analysisDialog`):** Ajuste de janela de tokens/segundos e despacho de análise Gemini/OpenRouter.
  3. **Lixeira (`trashDialog`):** Lista de projetos ou cortes excluídos com opção de restauração.
* **Controles HTML / Libs:** `<dialog>` nativo do HTML5 com `.showModal()` e `.close()`, `<details>` para menu do motor, `<input>` nativo, `AppButton.vue`.
* **Funcionalidades manuais:**
  - Gerenciamento de modais nativos com backdrop CSS personalizado (`::backdrop`).
  - Menu suspenso do motor local (`engineMenu`) feito com `<details>` e fechamento por tecla `Escape`.
  - Validador regex de URL do YouTube em tempo real.
  - Seleção nativa de arquivo de vídeo via API local (`api.pick('video')`).
* **Classificação:** **Substituição com adaptação**:
  - Modais: Substituir por [`ElDialog`](https://element-plus.org/en-US/component/dialog) com slots `header`, `default` e `footer`.
  - Menu do motor no cabeçalho: Substituir por [`ElDropdown`](https://element-plus.org/en-US/component/dropdown) ou [`ElPopover`](https://element-plus.org/en-US/component/popover).
  - Formulário de criação: Utilizar [`ElForm`](https://element-plus.org/en-US/component/form) e [`ElFormItem`](https://element-plus.org/en-US/component/form#formitem-attributes) com regras nativas de validação.

---

### 2.6 `OnboardingModal.vue`
* **Caminho:** `desktop/src/components/OnboardingModal.vue` (807 linhas, 19.360 bytes)
* **Responsabilidade:** Assistente inicial de primeiro uso inteligente. Detecta hardware do usuário (CPU, RAM, GPU), recomenda modelo Whisper ideal (Base, Small ou Large-v3-turbo), faz download/extração automática de FFmpeg e Whisper com telemetria visual em tempo real (bytes, velocidade, percentual), e coleta chave de API (Gemini ou OpenRouter).
* **Controles HTML / Libs:** Overlay manual (`.onboarding-overlay`), barra de progresso manual (`.progress-bar-fill`), cards de hardware manuais, rádio de provedor customizado.
* **Funcionalidades manuais:**
  - Controle de 3 etapas com lógica condicional (`diagnosis` -> `downloading` -> `apikey`).
  - Animação de barra de progresso com CSS puro e cálculo de velocidade/tempo restante.
  - Alternância entre provedores de API com botões estilizados como rádio.
* **Classificação:** **Composição híbrida**:
  - Navegação do fluxo: [`ElSteps`](https://element-plus.org/en-US/component/steps) e [`ElStep`](https://element-plus.org/en-US/component/steps#step-attributes) indicando diagnóstico, download e chaves.
  - Progresso mensurável: [`ElProgress`](https://element-plus.org/en-US/component/progress) com status e formatação de percentual.
  - Alertas e diagnósticos: [`ElAlert`](https://element-plus.org/en-US/component/alert) para avisos de hardware ou dependências ausentes.
  - Conclusão: [`ElResult`](https://element-plus.org/en-US/component/result) com ícone de sucesso.
  - Preservar a integração com o endpoint de provisionamento (`/api/system/provision`).

---

### 2.7 `PipelinePanel.vue`
* **Caminho:** `desktop/src/components/PipelinePanel.vue` (972 linhas, 33.180 bytes)
* **Responsabilidade:** Tela de preparação do projeto e orquestração do pipeline de 5 estágios (Importar, Transcrever, Analisar, Selecionar, Gerar, Exportar).
* **Problema identificado:** Apresentação redundante dos estágios; repete informações em cards grandes verticais que duplicam os passos da barra superior. Erros de renderização e falhas de workers ficam soterrados.
* **Controles HTML / Libs:** HTML nativo, `AppButton.vue`, ícones Lucide.
* **Classificação:** **Composição híbrida / Redesign**:
  - Indicador de etapas compacto: [`ElSteps`](https://element-plus.org/en-US/component/steps).
  - Alertas acionáveis de recuperação: [`ElAlert`](https://element-plus.org/en-US/component/alert) com botão de retry contextual.
  - Histórico e detalhes técnicos: [`ElCollapse`](https://element-plus.org/en-US/component/collapse) e [`ElCollapseItem`](https://element-plus.org/en-US/component/collapse#collapse-item-attributes).
  - Metadados do vídeo: [`ElDescriptions`](https://element-plus.org/en-US/component/descriptions) (resolução, duração, palavras transcritas).

---

### 2.8 `AnalysisPanel.vue`
* **Caminho:** `desktop/src/components/AnalysisPanel.vue` (1.579 linhas, 48.071 bytes)
* **Responsabilidade:** Workspace de análise semântica e curadoria de cortes. Navegação por temas/grupos, busca textual, filtro de propostas ativas/descartadas, player HTML5 com visualização sincronizada de intervalos de corte, cálculo e aviso de sobreposição temporal (overlap), seleção múltipla e persistência no backend.
* **Problema identificado:** É o **maior arquivo do projeto (1.579 linhas)**. Mistura reprodução de vídeo, inspeção de argumentos, streaming de pensamento da IA (`AnalysisFeedback.vue`), gestão de propostas descartadas via `localStorage`, atalhos de teclado e barra de ações.
* **Classificação:** **Decomposição arquitetural obrigatória + Composição híbrida**:
  - Deve ser decomposto em submódulos de domínio:
    1. `AnalysisTopicNav.vue` (Navegação de temas/grupos).
    2. `AnalysisCandidateList.vue` (Lista de propostas com busca e filtros).
    3. `AnalysisCandidateCard.vue` (Card individual com badge de elegibilidade e checkbox).
    4. `AnalysisInspector.vue` (Painel com player sincronizado, texto transcrito e justificativa editorial).
    5. `AnalysisSummaryBar.vue` (Barra inferior com total de cortes selecionados, duração e botão de despacho).
  - Componentes Element Plus utilizados internamente:
    - Busca e filtros: [`ElInput`](https://element-plus.org/en-US/component/input) e [`ElSegmented`](https://element-plus.org/en-US/component/segmented) (Ativas / Descartadas / Todas).
    - Rolagem independente: [`ElScrollbar`](https://element-plus.org/en-US/component/scrollbar).
    - Seleção de candidatos: [`ElCheckbox`](https://element-plus.org/en-US/component/checkbox).
    - Badges de elegibilidade e regras: [`ElTag`](https://element-plus.org/en-US/component/tag).
    - Alerta de cota 429 ou retomada de análise: [`ElAlert`](https://element-plus.org/en-US/component/alert).
    - Tooltip para justificativas de bloqueio: [`ElTooltip`](https://element-plus.org/en-US/component/tooltip).
  - **Manter estritamente personalizado:** Player HTML5 com controle de `currentTime`, loop no intervalo do corte (`start_us` a `end_us`), algoritmo de detecção de sobreposição e sincronização de palavras.

---

### 2.9 `AnalysisFeedback.vue`
* **Caminho:** `desktop/src/components/AnalysisFeedback.vue` (80 linhas, 4.656 bytes)
* **Responsabilidade:** Exibe em tempo real o fluxo de pensamento ("thought summaries") emitido pelo modelo de IA (Gemini ou OpenRouter) durante a análise. Possui botão para pausar/retomar auto-scroll e área rolável.
* **Controles HTML / Libs:** HTML nativo, `AppButton.vue`.
* **Classificação:** **Substituição com adaptação**:
  - Container de rolagem: [`ElScrollbar`](https://element-plus.org/en-US/component/scrollbar) com controle programático via `setScrollTop`.
  - Botão de acompanhamento: [`ElButton`](https://element-plus.org/en-US/component/button) com variantes de texto.
  - Tag de origem: [`ElTag`](https://element-plus.org/en-US/component/tag) indicando o provedor de IA.

---

### 2.10 `ReviewPanel.vue`
* **Caminho:** `desktop/src/components/ReviewPanel.vue` (782 linhas, 27.429 bytes)
* **Responsabilidade:** Painel de revisão dos cortes renderizados. Inclui player vertical 9:16 com controles de reprodução, tabela/lista de cortes prontos e em fila, checklist de validação editorial (5 perguntas), ações em lote (excluir múltiplos cortes, exportar múltiplos cortes aprovados), e cópia de título/descrição para publicação.
* **Controles HTML / Libs:** Tags HTML nativas, `<video>`, `AppButton.vue`.
* **Funcionalidades manuais:**
  - Tabela manual de cortes com seleção por checkbox HTML e shift-select.
  - Checklist editorial com botões `[Sim / Não]` customizados.
  - Barra de ações em lote flutuante.
* **Classificação:** **Composição híbrida**:
  - Lista de cortes: [`ElTable`](https://element-plus.org/en-US/component/table) com seleção múltipla nativa (`type="selection"`), ordenação e paginação.
  - Status dos cortes: [`ElTag`](https://element-plus.org/en-US/component/tag) (Pronto, Falha técnica, Aprovado, Rejeitado).
  - Filtros de corte: [`ElSegmented`](https://element-plus.org/en-US/component/segmented).
  - Checklist editorial: [`ElCheckboxGroup`](https://element-plus.org/en-US/component/checkbox#checkboxgroup-attributes) ou botões de rádio estilizados.
  - Detalhes de renderização / QA: [`ElDescriptions`](https://element-plus.org/en-US/component/descriptions) ou [`ElCollapse`](https://element-plus.org/en-US/component/collapse).
  - Drawer para metadados ou histórico: [`ElDrawer`](https://element-plus.org/en-US/component/drawer).
  - **Manter personalizado:** Player vertical 9:16 e controles de reprodução audiovisual.

---

### 2.11 `SettingsPanel.vue`
* **Caminho:** `desktop/src/components/SettingsPanel.vue` (1.134 linhas, 40.001 bytes)
* **Responsabilidade:** Painel de configurações gerais do sistema. Organizado em 3 etapas com navegação por teclado:
  1. Recursos locais (Whisper, FFmpeg, Profiling).
  2. IA e Modelos (Credenciais Gemini e OpenRouter, teste de conexão, seleção de catálogo).
  3. Preferências dos cortes (Durações mínima/máxima, política de pausas, resumos da API).
* **Problema identificado:** **Segundo maior arquivo do sistema (1.134 linhas)**. Mistura validação de campos, chamadas de teste de credencial, mapeamento de catálogo, rádio de provedor e navegação de abas manuais.
* **Classificação:** **Decomposição arquitetural + Substituição direta por componentes de formulário**:
  - Navegação entre seções: [`ElMenu`](https://element-plus.org/en-US/component/menu) vertical ou [`ElTabs`](https://element-plus.org/en-US/component/tabs).
  - Estrutura de formulário: [`ElForm`](https://element-plus.org/en-US/component/form) com validação orientada a schema/regras.
  - Entradas de texto e senha: [`ElInput`](https://element-plus.org/en-US/component/input) com `type="password"` e `show-password`.
  - Seleção de modelo: [`ElSelect`](https://element-plus.org/en-US/component/select) com busca de modelos (`filterable`).
  - Durações numéricas: [`ElInputNumber`](https://element-plus.org/en-US/component/input-number) com controles de min/max/step.
  - Seleção de provedor: [`ElSegmented`](https://element-plus.org/en-US/component/segmented) ou [`ElRadioGroup`](https://element-plus.org/en-US/component/radio).
  - Chaves booleanas: [`ElSwitch`](https://element-plus.org/en-US/component/switch).
  - Alertas de status da chave: [`ElAlert`](https://element-plus.org/en-US/component/alert).

---

### 2.12 `GlobalQueueModal.vue`
* **Caminho:** `desktop/src/components/GlobalQueueModal.vue` (341 linhas, 11.057 bytes)
* **Responsabilidade:** Modal overlay de fila global de tarefas em segundo plano. Permite visualizar tarefas ativas e histórico recente entre todos os projetos locais, com opções de cancelar ou navegar diretamente para o projeto dono da tarefa.
* **Classificação:** **Substituição direta com redesign** por [`ElDrawer`](https://element-plus.org/en-US/component/drawer). A fila é naturalmente um painel lateral retrátil (drawer), permitindo que o usuário acompanhe o processamento de qualquer tela do aplicativo sem perder o contexto visual principal.

---

### 2.13 `GenerationQueue.vue` & `ProjectQueue.vue`
* **Caminhos:** `desktop/src/components/GenerationQueue.vue` (105 linhas, 4.657 bytes) e `desktop/src/components/ProjectQueue.vue` (64 linhas, 1.909 bytes)
* **Responsabilidade:**
  - `GenerationQueue.vue`: Renderiza a fila específica de renderização de cortes dentro do projeto, com status por candidato.
  - `ProjectQueue.vue`: Renderiza a lista compacta de tarefas associadas ao projeto aberto.
* **Classificação:** **Consolidação**:
  - Podem ser unificados ou refatorados com [`ElTimeline`](https://element-plus.org/en-US/component/timeline) ou [`ElTable`](https://element-plus.org/en-US/component/table) compacta, usando [`ElTag`](https://element-plus.org/en-US/component/tag) e [`ElProgress`](https://element-plus.org/en-US/component/progress).

---

### 2.14 `ProjectWorkspace.vue` & `JobPanel.vue`
* **Caminhos:** `desktop/src/components/ProjectWorkspace.vue` (260 linhas, 11.971 bytes) e `desktop/src/components/JobPanel.vue` (50 linhas, 1.897 bytes)
* **Responsabilidade:**
  - `ProjectWorkspace.vue`: Container de abas de trabalho dentro do projeto (`pipeline`, `analysis`, `review`, `transcript`).
  - `JobPanel.vue`: Painel de depuração/inspeção de tarefa individual.
* **Classificação:**
  - `ProjectWorkspace.vue`: Utilizar [`ElTabs`](https://element-plus.org/en-US/component/tabs) (`type="border-card"` ou estilização customizada) para alternar as visualizações do projeto.
  - `JobPanel.vue`: Consolidar no drawer da fila global ou manter como subcomponente de diagnóstico.

---

## 3. Resumo Quantitativo da Classificação

| Classificação | Quantidade | Componentes |
| :--- | :---: | :--- |
| **Substituição Direta** | 4 | `AppButton.vue`, `AppSelect.vue`, `GlobalQueueModal.vue`, `AppToaster.vue` |
| **Composição Híbrida** | 4 | `ProjectLibrary.vue`, `OnboardingModal.vue`, `PipelinePanel.vue`, `ReviewPanel.vue` |
| **Decomposição Arquitetural Obrigatória** | 2 | `AnalysisPanel.vue` (1.579 linhas), `SettingsPanel.vue` (1.134 linhas) |
| **Consolidação / Refatoração** | 3 | `GenerationQueue.vue`, `ProjectQueue.vue`, `JobPanel.vue` |
| **Manter Domínio / Shell** | 3 | `App.vue` (Shell), Players de vídeo (HTML5 / 9:16 vertical), Algoritmos de sincronização/overlap |
