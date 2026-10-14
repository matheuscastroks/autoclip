# Design Spec: AutoClip UI Redesign — Phase 2 (Shell, Project Library & Preparation)

- **Date:** 2026-10-14
- **Branch:** `poc-openshorts-gemini`
- **Target Phase:** PR 2 — Shell, Biblioteca e Preparação
- **Status:** Approved by user

---

## 1. Context & Motivation

A auditoria de UI/UX do AutoClip diagnosticou três problemas estruturais no fluxo inicial do usuário:
1. **Shell e Cabeçalho (`App.vue`):** Destaque excessivo nas barras de navegação e duplicação da fila global em dois lugares (cabeçalho e banner na biblioteca).
2. **Biblioteca de Projetos (`ProjectLibrary.vue`):** Modo grade padrão exibindo cartões carregados de metadados concorrentes com visual de dashboard genérico, e ações destrutivas expostas sem proteção.
3. **Preparação (`PipelinePanel.vue`):** Mistura de stepper horizontal, card de estado hero, métricas e histórico técnico competindo com o player e a ação principal, obscurecendo a resposta para: *o vídeo está pronto para analisar? Se não, o que falta?*

A Fase 2 redesenha a hierarquia desses três pontos mantendo 100% de conformidade com todos os testes automatizados da aplicação.

---

## 2. Shell & Header Simplification (`App.vue`)

1. **Navegação Global e do Projeto:**
   - Reduzir peso visual da barra de navegação global.
   - Separadores sutis utilizando `--color-border-subtle` (`rgba(255, 255, 255, 0.07)`).
   - Abas do projeto (`Preparação`, `Transcrição`, `Análise`, `Cortes`): texto secundário discreto com transição para `--color-text-primary` no hover, e estado ativo indicado por fundo sutil `var(--color-surface-hover)` e contraste tipográfico.
2. **Unificação da Fila de Processamento:**
   - Centralizar a presença da fila global de jobs exclusivamente no indicador discreto do cabeçalho.
   - A abertura do modal/drawer da fila global permite monitorar jobs sem perder a tela atual.
   - Eliminar o banner duplicado da fila na biblioteca.

---

## 3. Project Library Redesign (`ProjectLibrary.vue`)

1. **Modo de Visualização Padrão:**
   - Alterar `viewMode` padrão de `'grid'` para `'list'`.
   - O alternador de visualização permanece disponível para quem prefere thumbnails em grade.
2. **Linha de Projeto Densa e Compacta (Lista):**
   - Miniatura de mídia em proporção estável com ícone de fallback.
   - Colunas essenciais:
     - Identidade: Título do projeto + metadados secundários (palavras transcritas ou nome original).
     - Duração: Duração do vídeo formatada.
     - Estado/Etapa: Status textual com indicador discreto.
     - Cortes: Quantidade de propostas e cortes gerados em texto compacto.
     - Atualização: Data/hora da última alteração.
     - Ações: Botão de ação destrutiva (`data-action="delete-project"`) discreto com proteção de clique acidental.
3. **Grade de Mídia (Quando Selecionada):**
   - Cards com superfícies contínuas `var(--color-surface)`, borda sutil `var(--color-border-subtle)` e hover em `var(--color-border-strong)`.
   - Remoção de bordas grossas decorativas.
4. **Estado Vazio:**
   - Superfície neutra centralizada com ícone e chamada direta para novo projeto (`$emit('create')`).

---

## 4. Preparation View Redesign (`PipelinePanel.vue`)

Organização da tela ao redor dos 3 pilares de decisão:

### Pilar 1: Fonte do Vídeo
- Exibição limpa da origem do projeto: arquivo importado / canal, duração e miniatura/vídeo estável (`.pipeline-video`).
- Preservação da coluna de preview do vídeo sincronizada.

### Pilar 2: Estado Real do Processamento
- Indicador textual direto e confiável:
  - *"Importando vídeo..."* / *"Transcrição em andamento..."* / *"Vídeo pronto para análise"*.
  - Eliminação de qualquer barra com porcentagem arbitrária ou ilustrativa (ex: 75%). Apenas progresso real ou indeterminado contínuo.
- Tratamento de Falhas:
  - Card contextual para falha de importação com ações imediatas: `"retry-import"` e `"replace-source"`.
  - Acesso aos detalhes de erro através do gatilho `"error-details"`.

### Pilar 3: Próxima Ação Clara
- Botão primário contextual único:
  - Se pronto para análise: botão proeminente para iniciar análise (`$emit('analysis')`).
  - Se em processamento: botão discreto para cancelamento (`$emit('cancel', job.id)`).
  - Se concluído com cortes: atalho para revisão (`$emit('review')`).

### Stepper Técnico Integrado e Acessível
- As etapas técnicas estruturadas (`[data-stage=import]`, `[data-stage=transcribe]`, `[data-stage=analyze]`, etc.) e os atributos ARIA permanecem no DOM em uma seção técnica secundária e organizada, garantindo que o usuário tenha visibilidade sob demanda e todos os testes continuem verdes.

---

## 5. Non-Goals (Fases Futuras)

Nesta Fase 2 **não** faremos:
- Fatiamento do `AnalysisPanel.vue` (Fase 3).
- Reestruturação do `ReviewPanel.vue` ou `SettingsPanel.vue` (Fase 4).
- Alteração nos contratos de API do backend.

---

## 6. Verification & Quality Gates

1. **Testes de Workflow e Workspace:** `workflow.test.ts`, `workspace.test.ts` e `desktop-polish.test.ts` passam com 100% de sucesso.
2. **Suíte Completa:** Todos os 20 arquivos de teste (109 testes) continuam passando.
3. **Padrão de Lista:** A biblioteca abre em modo lista por padrão (`viewMode === 'list'`).
4. **Sem Duplicações:** O banner de fila na biblioteca é removido em prol do indicador do cabeçalho.
