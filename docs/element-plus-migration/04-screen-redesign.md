# Proposta de Redesign Estrutural das Telas do AutoClip

> **Documento:** `docs/element-plus-migration/04-screen-redesign.md`  
> **Status:** Concluído / Arquitetura de Interface e UX  
> **Referência Oficial:** [https://element-plus.org/en-US/component/overview](https://element-plus.org/en-US/component/overview)

---

## 1. Princípios de Redesign

A adoção do Element Plus no AutoClip não é uma mera troca de tags HTML. O objetivo central é **reduzir a sobrecarga cognitiva do editor de vídeo**, oferecendo uma interface profissional com alta densidade de informação sem parecer congestionada.

```
+-----------------------------------------------------------------------------------+
|  DIRETRIZ MESTRA DE UX: O Vídeo e as Decisões Editoriais são os Protagonistas    |
|  O Element Plus fornece o sistema de controles, formulários e navegação;          |
|  o AutoClip fornece os players de vídeo, sincronização de corte e curadoria de IA.|
+-----------------------------------------------------------------------------------+
```

---

## 2. Análise e Redesign Tela por Tela

---

### 5.1 Biblioteca de Projetos (`ProjectLibrary.vue`)

#### 1. Diagnóstico Atual
A tela exibe uma barra de ferramentas no topo (busca, filtro de status, ordenação e alternador grade/lista) e, no corpo, cards de projetos com miniatura 16:9 ou uma tabela HTML crua sem ordenação interativa.

#### 2. Problemas de UX Identificados
* O alternador de visualização (Grade/Lista) é feito com botões soltos que parecem desconectados.
* A visualização em tabela atual (`<table>` manual) não permite clicar nos cabeçalhos para ordenar (por exemplo, ordenar por "Última modificação" ou "Número de palavras").
* Projetos que falharam ou precisam de atenção ficam misturados com os concluídos sem destaque semântico.
* O estado vazio é básico e não incentiva a ação imediata.

#### 3. Componentes Element Plus Indicados
* [`ElSegmented`](https://element-plus.org/en-US/component/segmented): Alternador tátil entre Grade e Lista.
* [`ElInput`](https://element-plus.org/en-US/component/input) com `prefix-icon="Search"` e `clearable`.
* [`ElSelect`](https://element-plus.org/en-US/component/select) para filtro de status e ordenação.
* [`ElTable`](https://element-plus.org/en-US/component/table) com colunas ordenáveis (`sortable`) para a visão em lista.
* [`ElTag`](https://element-plus.org/en-US/component/tag) para os status dos projetos (Pronto, Falha, Transcrevendo).
* [`ElEmpty`](https://element-plus.org/en-US/component/empty) com botão de CTA no estado sem projetos.
* [`ElPopconfirm`](https://element-plus.org/en-US/component/popconfirm) para exclusão de projetos com segurança.

#### 4. Componentes Próprios a Preservar
* Card de projeto na visualização em grade (thumbnail 16:9, indicador de duração e badge pulsante de renderização).

#### 5. Proposta de Wireframe da Biblioteca
```
+----------------------------------------------------------------------------------------------------+
|  [🔍 Buscar projetos...   ]  [Todos os Estados ▼]  [Ordenar por Data ▼]      [ ▦ Grade | ☷ Lista ] |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [+ NOVO PROJETO]  [ 🎬 Thumbnail 16:9 ]   [ 🎬 Thumbnail 16:9 ]   [ 🎬 Thumbnail 16:9 ]           |
|  (Card de Ação)    Entrevista Educação     Podcast Tecnologia      Aula Magistral                  |
|                    00:45:12 · 8 cortes     01:12:00 · 14 cortes    00:30:15 · Transcrevendo        |
|                    [Pronto] [Abrir]        [Pronto] [Abrir]        [Processando 65%]               |
+----------------------------------------------------------------------------------------------------+
```

---

### 5.2 Criação de Projeto (Modal de Criação em `App.vue`)

#### 1. Diagnóstico Atual
Modal nativo `<dialog>` com campos de texto para nome, alternador de entrada (Arquivo Local vs. URL YouTube) e um resumo estático das configurações do motor.

#### 2. Problemas de UX Identificados
* Não há validação visual em tempo real: o usuário só descobre erros ao tentar clicar em "Criar".
* Ao colar uma URL do YouTube, a validação é exibida em textos soltos com cores inline.
* Não existe suporte visual claro a drag-and-drop de arquivos locais.

#### 3. Componentes Element Plus Indicados
* [`ElDialog`](https://element-plus.org/en-US/component/dialog) com tamanho controlado (`width="580px"`).
* [`ElForm`](https://element-plus.org/en-US/component/form) e [`ElFormItem`](https://element-plus.org/en-US/component/form#formitem-attributes) com regras declarativas de validação (`rules`).
* [`ElSegmented`](https://element-plus.org/en-US/component/segmented): Alternar entre `Arquivo no Computador` e `Link do YouTube`.
* [`ElInput`](https://element-plus.org/en-US/component/input) com botão anexado de navegação local.
* [`ElAlert`](https://element-plus.org/en-US/component/alert) destacando se alguma dependência essencial (ex: FFmpeg) está pendente.
* [`ElButton`](https://element-plus.org/en-US/component/button) com `:loading="busy"` para evitar múltiplos cliques no envio.

#### 4. Componentes Próprios a Preservar
* Ação nativa `api.pick('video')` para abrir a janela do Windows Explorer sem conversão HTTP.

#### 5. Proposta de Wireframe de Criação
```
+---------------------------------------------------------------+
|  Criar Novo Projeto                                       [X] |
+---------------------------------------------------------------+
|  Origem do Vídeo:                                             |
|  [ 📁 Arquivo Local  |  🔴 Link do YouTube ]                 |
|                                                               |
|  Caminho do Arquivo:                                          |
|  [ C:\Videos\entrevista_bruta.mp4            ] [Procurar...] |
|                                                               |
|  Nome do Projeto:                                             |
|  [ Entrevista sobre Educação e Tecnologia                    ] |
|                                                               |
|  ℹ️ Fluxo Automático Ativo:                                    |
|     Importar -> Transcrever (Whisper) -> Analisar (Gemini)   |
+---------------------------------------------------------------+
|                                       [Cancelar] [Criar Projeto]
+---------------------------------------------------------------+
```

---

### 5.3 Onboarding Inteligente (`OnboardingModal.vue`)

#### 1. Diagnóstico Atual
Modal de primeiro uso com 3 etapas: Diagnóstico de Hardware, Download de Dependências e Configuração de Chave de IA. Utiliza barras manuais de progresso e botões personalizados.

#### 2. Problemas de UX Identificados
* As etapas são indicadas por botões soltos no topo que não deixam claro o fluxo sequencial.
* Durante o download de centenas de megabytes (FFmpeg e Whisper), o usuário precisa de um feedback de progresso sólido, com velocidade e percentual claros.

#### 3. Componentes Element Plus Indicados
* [`ElSteps`](https://element-plus.org/en-US/component/steps) e [`ElStep`](https://element-plus.org/en-US/component/steps#step-attributes) com ícones e status (`finish`, `process`, `wait`).
* [`ElProgress`](https://element-plus.org/en-US/component/progress) com `:percentage="provisionStatus.percent"` e `:status="progressStatus"`.
* [`ElAlert`](https://element-plus.org/en-US/component/alert) destacando a recomendação de modelo para a CPU/GPU do usuário.
* [`ElSegmented`](https://element-plus.org/en-US/component/segmented) para alternar entre as chaves Google Gemini e OpenRouter.
* [`ElResult`](https://element-plus.org/en-US/component/result) para a tela final de conclusão com sucesso.

#### 4. Proposta de Wireframe de Onboarding
```
+---------------------------------------------------------------------+
|  Configuração Inicial do AutoClip                               [X] |
+---------------------------------------------------------------------+
|   (1) Diagnóstico  ======>  (2) Instalação  ======>  (3) Chaves IA  |
|                                                                     |
|  Baixando Componentes do Sistema...                                 |
|  [===========================>-----------------] 62%               |
|  Baixando Whisper Small (285 MB / 460 MB) · 12.4 MB/s · ETA: 14s   |
|                                                                     |
|  ℹ️ O FFmpeg já foi instalado com sucesso.                          |
+---------------------------------------------------------------------+
|                                                          [Aguarde...]
+---------------------------------------------------------------------+
```

---

### 5.4 Preparação do Projeto (`PipelinePanel.vue`) — **Redesign Estrutural**

#### 1. Diagnóstico Atual
A tela atual possui 972 linhas e exibe uma lista vertical de cards gigantescos repetindo cada uma das 5 etapas do pipeline. Erros de renderização ou de API ficam perdidos no meio de textos repetidos.

#### 2. Problemas de UX Identificados
* **Redundância:** A tela repete os mesmos nomes das etapas (Importar, Transcrever, Analisar, Selecionar, Gerar) em 3 locais diferentes.
* **Falta de Foco:** O usuário não sabe de imediato qual é a *única* ação que ele deve tomar agora.
* **Erros Ocultos:** Se uma prévia falhar ou se o Gemini atingir a cota 429, a mensagem aparece sem destaque de ação de recuperação.

#### 3. Nova Proposta: **Dashboard Contextual Focado na Próxima Ação**
Transformar a tela em um painel limpo dividido em três áreas funcionais:
1. **Topo Compacto:** `ElSteps` horizontal indicando o status geral do projeto.
2. **Centro em Destaque (Hero Action):** Um card proeminente mostrando exclusivamente o que está acontecendo agora ou qual é a próxima ação humana necessária.
3. **Histórico Técnico (Expansível):** `ElCollapse` contendo os detalhes técnicos e logs, disponíveis sem poluir a visão do editor.

#### 4. Componentes Element Plus Indicados
* [`ElSteps`](https://element-plus.org/en-US/component/steps) com `align-center` e status por etapa.
* [`ElAlert`](https://element-plus.org/en-US/component/alert) com botão de ação para falhas de renderização ou limite de cota.
* [`ElDescriptions`](https://element-plus.org/en-US/component/descriptions) para metadados do vídeo (formato, resolução, FPS, total de palavras).
* [`ElCollapse`](https://element-plus.org/en-US/component/collapse) para histórico detalhado das etapas concluídas.

#### 5. Proposta de Wireframe da Preparação
```
+-----------------------------------------------------------------------------------+
|  [✓ Importado] ---> [✓ Transcrito] ---> [✓ Analisado] ---> [ ⏳ Seleção ] ---> [ ]|
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |  🎯 PRÓXIMA ETAPA: Revisar Propostas e Selecionar Cortes                    |  |
|  |  A IA identificou 18 momentos com alto potencial de engajamento no vídeo.  |  |
|  |                                                                             |  |
|  |  [ IR PARA A ABA ANÁLISE ]      [ Executar Análise Novamente ]             |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  ▸ Metadados do Vídeo Original (1080p · 29.97 fps · 4.820 palavras)              |
|  ▸ Histórico Técnico e Logs de Processamento                                      |
+-----------------------------------------------------------------------------------+
```

---

### 5.5 Transcrição (Visualização do Texto e Sincronização)

#### 1. Diagnóstico Atual
Exibe o player do vídeo e o texto contínuo transcrito pelo Whisper.

#### 2. Problemas de UX Identificados
* Transcrições longas de palestras (1 a 2 horas) geram milhares de palavras, provocando rolagem vertical excessiva que oculta o player de vídeo.
* Falta um campo rápido para pesquisar palavras-chave no texto falado.

#### 3. Componentes Element Plus Indicados
* [`ElInput`](https://element-plus.org/en-US/component/input) com busca e realce de termos encontrados.
* [`ElScrollbar`](https://element-plus.org/en-US/component/scrollbar) para permitir que a lista de transcrição role independentemente do player de vídeo.
* [`ElTag`](https://element-plus.org/en-US/component/tag) para exibir timestamps de início e fim dos blocos de fala.

---

### 5.6 Análise e Seleção de Cortes (`AnalysisPanel.vue`) — **Redesign Principal**

#### 1. Diagnóstico Atual
Monolito com 1.579 linhas. Apresenta lista de tópicos em botões, cards de propostas com checklist de elegibilidade, player do trecho com visualização de intervalo e barra de resumo inferior.

#### 2. Problemas de UX Identificados
* **Interface congestionada:** O player de vídeo original disputa espaço com a lista de argumentos em telas menores (laptops 1366x768).
* **Filtros limitados:** Alternar entre propostas ativas e descartadas usa botões simples.
* **Perda de contexto:** A seleção de propostas entre múltiplos temas precisa ser mantida sem atrito.

#### 3. Decomposição Arquitetural em 5 Subcomponentes
Para solucionar o tamanho e a complexidade do arquivo, dividiremos `AnalysisPanel.vue` em:
1. `AnalysisTopicNav.vue`: Navegação horizontal por tópicos/temas identificados.
2. `AnalysisCandidateList.vue`: Lista filtrável de propostas de corte.
3. `AnalysisCandidateCard.vue`: Card com duração, pontuação e checkbox.
4. `AnalysisInspector.vue`: Painel direito com player do intervalo e texto do argumento.
5. `AnalysisSummaryBar.vue`: Barra inferior fixa com ações de despacho.

#### 4. Componentes Element Plus Indicados
* [`ElScrollbar`](https://element-plus.org/en-US/component/scrollbar) na lista de propostas e na navegação de temas.
* [`ElSegmented`](https://element-plus.org/en-US/component/segmented) para filtro de estado: `Ativas (12)` | `Descartadas (3)` | `Todas (15)`.
* [`ElCheckbox`](https://element-plus.org/en-US/component/checkbox) com suporte a atalhos de teclado e seleção acessível.
* [`ElTag`](https://element-plus.org/en-US/component/tag) coloridas (`success`, `warning`, `info`) para elegibilidade e pausas.
* [`ElTooltip`](https://element-plus.org/en-US/component/tooltip) para exibir o motivo de eventuais bloqueios editoriais.
* [`ElAlert`](https://element-plus.org/en-US/component/alert) no topo quando a análise for parcial, com botão 1-clique para continuar.

#### 5. Proposta de Wireframe do Workspace de Análise
```
+----------------------------------------------------------------------------------------------------+
|  Temas: [Todos (18)]  [#1 Inteligência Artificial (6)]  [#2 Produtividade (5)]  [#3 Carreira (7)]  |
+----------------------------------------------------------------------------------------------------+
|  [🔍 Filtrar propostas...      ] [ Ativas (15) | Descartadas (3) ] | INSPEÇÃO DO CORTE SELECIONADO |
|                                                                    |                               |
|  [x] Proposta #01 · 00:02:15 - 00:04:10 (1m 55s) [Elegível]        |  +-------------------------+  |
|      "O impacto da IA nos empregos nos próximos 5 anos"            |  |  PLAYER VÍDEO ORIGINAL  |  |
|      Apresenta tese clara e gancho forte.                          |  |  [ 02:15 ========= 04:10] |  |
|                                                                    |  +-------------------------+  |
|  [ ] Proposta #02 · 00:10:00 - 00:12:30 (2m 30s) [Elegível]        |  Transcrição do Trecho:       |
|      "Como organizar sua rotina matinal"                           |  "Nós estamos vivendo uma     |
|      Explicação passo a passo.                                     |   transformação sem precedentes|
|                                                                    |   no mercado..."              |
|  [ ] Proposta #03 · 00:15:20 - 00:16:40 (1m 20s) [Sobreposição]   |                               |
|      "Dica rápida de software" (conflita com corte #01)            |  [ Descartar ]  [ Selecionar] |
+--------------------------------------------------------------------+-------------------------------+
|  RESUMO: 2 cortes selecionados · 04m 25s no total                  | [LIMPAR] [GERAR CORTES (2) >] |
+--------------------------------------------------------------------+-------------------------------+
```

---

### 5.7 Revisão de Cortes (`ReviewPanel.vue`)

#### 1. Diagnóstico Atual
Exibe o player vertical 9:16 para conferir os cortes codificados com legendas e enquadramento facial, lista de cortes prontos e checklist editorial de 5 perguntas.

#### 2. Problemas de UX Identificados
* A tabela manual de cortes não permite seleção múltipla conveniente para download em lote ou exclusão em massa.
* O checklist editorial de 5 perguntas ocupa muito espaço vertical.

#### 3. Componentes Element Plus Indicados
* [`ElTable`](https://element-plus.org/en-US/component/table) com seleção por checkbox na primeira coluna (`type="selection"`).
* [`ElTag`](https://element-plus.org/en-US/component/tag) para exibir o resultado da validação técnica de áudio/vídeo (`Aprovado`, `Falha no Áudio`).
* [`ElButton`](https://element-plus.org/en-US/component/button) para ações rápidas de cópia de título/descrição e exportação.
* [`ElDrawer`](https://element-plus.org/en-US/component/drawer) opcional para inspecionar os detalhes técnicos de renderização do corte.

#### 4. Componentes Próprios a Preservar
* **Player Vertical 9:16:** Central para a avaliação do formato Short/Reels/TikTok.

---

### 5.8 Fila Global de Tarefas (`GlobalQueueModal.vue`) — **Redesign para Drawer**

#### 1. Diagnóstico Atual
Modal centralizado que escurece e bloqueia toda a tela para ver a fila de renderização.

#### 2. Redesign: **Painel Lateral Retrátil (`ElDrawer`)**
Substituir o modal por um [`ElDrawer`](https://element-plus.org/en-US/component/drawer) que desliza da direita:
* O usuário pode abrir a fila de tarefas enquanto navega em qualquer projeto ou tela de configurações.
* Exibe a lista de tarefas com [`ElTimeline`](https://element-plus.org/en-US/component/timeline) ou lista compacta, contendo nome do projeto, etapa corrente, botão de cancelar e indicador de progresso.

---

### 5.9 Configurações do Sistema (`SettingsPanel.vue`) — **Redesign Estrutural**

#### 1. Diagnóstico Atual
1.134 linhas misturando navegação por teclado manual e 3 categorias de formulários extensos.

#### 2. Redesign com `ElMenu` e `ElForm`
* Navegação lateral utilizando [`ElMenu`](https://element-plus.org/en-US/component/menu) vertical:
  1. `Recursos Locais` (FFmpeg, Whisper, Profiling de Hardware).
  2. `Inteligência Artificial` (Google Gemini e OpenRouter).
  3. `Regras Editoriais` (Duração mínima, máxima, modo de corte e pausas).
* Formulários padronizados com [`ElForm`](https://element-plus.org/en-US/component/form) e validação nativa.
* Inputs de senha seguros com [`ElInput`](https://element-plus.org/en-US/component/input) (`show-password`).
* Controles numéricos precisos com [`ElInputNumber`](https://element-plus.org/en-US/component/input-number) (ex: janela de 60 a 300 segundos com step de 15s).
