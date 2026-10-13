# 07. Roteiro de Implementação em Fases, Reuso de Componentes e Análise de Riscos

## 1. Estratégia de Não-Regressão e Preservação de Contratos

O objetivo desta transição é elevar drasticamente a usabilidade do AutoClip sem reescrever o motor de processamento Python e sem quebrar os contratos de API existentes.

### Contratos de Backend Preservados Integralmente:
- `GET /api/v1/projects`: Listagem de projetos com metadados e status.
- `POST /api/v1/projects`: Criação de projeto via URL ou arquivo local.
- `GET /api/v1/projects/{id}`: Detalhes do projeto e arquivos em disco.
- `GET /api/v1/projects/{id}/transcription`: Segmentos do Whisper e texto bruto.
- `POST /api/v1/projects/{id}/analysis`: Disparo de análise semântica Gemini (com preservação de janelas).
- `GET /api/v1/projects/{id}/analysis`: Tópicos, argumentos e propostas de cortes.
- `POST /api/v1/projects/{id}/cuts/generate`: Renderização FFmpeg dos cortes selecionados em 9:16.
- `GET /api/v1/projects/{id}/cuts`: Lista de cortes gerados, caminhos de vídeo e legendas.
- `GET /api/v1/queue`: Monitoramento da fila global de tarefas ativas e pendentes.
- `POST /api/v1/system/jobs/{job_id}/cancel`: Cancelamento gracioso de processos.

---

## 2. Mapa de Reuso e Refatoração de Componentes Frontend

| Componente Atual (`desktop/src/components/`) | Destino na Nova Arquitetura | Estratégia de Modificação |
| :--- | :--- | :--- |
| `ProjectLibrary.vue` | Mantido e Polido como `ProjectLibrary.vue` | Expandir área de clique dos cards para o container inteiro; adicionar estado vazio acolhedor; aplicar novos tokens de cor; integrar atalho para Fila Global. |
| `GlobalQueueModal.vue` | Mantido como `GlobalQueueDrawer.vue` | Transformar em gaveta lateral ou modal leve; melhorar responsividade de títulos longos; garantir alvos mínimos de botão de 32px. |
| `ProjectCreationDialog.vue` | Mantido e Polido | Adicionar validação de URL em tempo de digitação; simplificar abas; ocultar opções técnicas avançadas sob disclosure. |
| `PipelinePanel.vue` | Refatorado para `ProjectHub.vue` | Substituir a visão poluída por esteira semântica de 4 nós (Carbon Stepper); converter cards soltos em Call-to-Action contextual único; eliminar rolagem vertical excessiva em 768px. |
| `TranscriptViewer.vue` | Mantido como gaveta/drawer contextual | Resolver a barreira dos 789 botões interativos removendo `tabindex` individual dos timestamps; agrupar falas por parágrafos; adicionar busca rápida de termos. |
| `AnalysisPanel.vue` | Refatorado para `CurationWorkspace.vue` | Abandonar o layout de 3 colunas espremidas; implementar layout de 2 colunas amplas (Filtro de Temas à esquerda | Cards de Propostas no centro/direita); integrar player de áudio direto de 36px; manter a trava de sobreposição (*no-overlap*) existente. |
| `CutsPanel.vue` | Refatorado para `ReviewStudio.vue` | Calibrar o player vertical para 480px de altura máxima (eliminar rolagem de página em 768px); colocar lista de cortes à esquerda e painel de ajustes finos (legendas e trimmer) à direita. |
| `SettingsModal.vue` | Mantido e Organizado | Reagrupar em 3 abas limpas com microcópia em linguagem natural; ocultar parâmetros matemáticos de LLM em gaveta avançada. |

---

## 3. Roteiro de Implementação em Fases (Fases 0 a 7)

### Fase 0: Preparação de Infraestrutura e Tokens Visuais
- **Atividades:**
  - Definir e registrar os tokens CSS da nova paleta Dark Studio (`--color-canvas`, `--color-surface`, `--color-accent`, etc.) em `desktop/src/style.css`.
  - Configurar classes utilitárias de foco acessível (`focus-visible:ring-2 focus-visible:ring-amber-500`).
  - Atualizar testes de regressão básica de estilo.
- **Critério de Aceite:** Tokens carregam sem conflito com Reka UI e sem quebrar estilos existentes.

### Fase 1: Biblioteca e Modal de Novo Projeto
- **Atividades:**
  - Atualizar os cards de projeto na `ProjectLibrary.vue` para preenchimento de container clicável.
  - Criar componente de estado vazio (*Empty State*) quando a biblioteca estiver zerada.
  - Refinar o `ProjectCreationDialog.vue` com validação prévia de URLs do YouTube.
- **Critério de Aceite:** Criação de projeto fluida, com mensagens de erro imediatas antes do disparo de requisições.

### Fase 2: O Novo Hub do Projeto (`ProjectHub.vue`)
- **Atividades:**
  - Desenvolver o componente `ProjectStepper.vue` com os 4 nós semânticos discretos.
  - Estruturar a visão inicial do projeto com o CTA primário contextual que direciona para a etapa ativa.
  - Garantir altura total contida dentro do viewport de 768px (zero overflow vertical).
- **Critério de Aceite:** O usuário entende o status de qualquer projeto em menos de 3 segundos sem precisar rolar a página.

### Fase 3: Workspace de Curadoria de Cortes (`CurationWorkspace.vue`)
- **Atividades:**
  - Reestruturar `AnalysisPanel.vue` de 3 para 2 colunas.
  - Implementar o novo `ProposalCard.vue` com destaque visual do Gancho (*Hook*), nota editorial e player de áudio integrado.
  - Preservar integralmente a lógica de bloqueio de sobreposição (*no-overlap*) com o badge visual de alerta.
  - Criar a barra flutuante inferior de ação com contagem de cortes selecionados e botão primário de geração de prévias.
- **Critério de Aceite:** Seleção de propostas confortável em telas 1366×768 sem quebra de texto comprimido.

### Fase 4: Estúdio de Revisão e Player 9:16 (`ReviewStudio.vue`)
- **Atividades:**
  - Redimensionar o container do player vertical para 480px de altura máxima.
  - Integrar a lista de cortes prontos com miniaturas verticais à esquerda.
  - Adicionar controles rápidos de ajuste fino de tempo (+/- 0.5s no início e término).
  - Incluir editor simples de texto de legendas em linha.
- **Critério de Aceite:** O player 9:16 e todos os botões de ação cabem em uma única tela em 1366×768 sem rolagem dupla.

### Fase 5: Otimização da Transcrição e Fila Global
- **Atividades:**
  - Virtualizar ou agrupar os segmentos de texto em `TranscriptViewer.vue`, eliminando os 789 tab stops individuais.
  - Refinar o `GlobalQueueDrawer.vue` para exibição fluida em gaveta lateral responsiva.
  - Ajustar todos os alvos clicáveis menores de 24px para no mínimo 32px de altura.
- **Critério de Aceite:** Navegação por teclado fluida com Tab em todas as telas; conformidade estrita com WCAG 2.5.8.

### Fase 6: Configurações e Microcópia
- **Atividades:**
  - Aplicar o guia de microcópia em todos os textos da aplicação (remover termos internos da API).
  - Reorganizar `SettingsModal.vue` com a gaveta de ajustes avançados.
  - Adicionar tooltips acessíveis em termos técnicos.
- **Critério de Aceite:** Usuários novatos conseguem configurar o aplicativo sem dúvidas sobre modelos ou parâmetros.

### Fase 7: Homologação, Testes Automatizados e Benchmark Final
- **Atividades:**
  - Rodar suíte completa de testes unitários frontend com Vitest (`npm test`).
  - Validar compilação TypeScript com `vue-tsc --noEmit`.
  - Executar suíte de testes backend com Pytest (`pytest`).
  - Executar nova auditoria visual via CDP em 1366×768 confirmando ausência de regressões e conformidade de layout.
- **Critério de Aceite:** 100% dos testes passando; zero erros de compilação; relatório de métricas sem violações críticas.

---

## 4. Registro de Riscos e Estratégias de Mitigação

| Risco Identificado | Severidade | Probabilidade | Estratégia de Mitigação |
| :--- | :--- | :--- | :--- |
| **Risco 1: Conflito de estilos ao alterar tokens globais** | Média | Baixa | Utilizar escopo CSS bem definido e tokens mapeados compatíveis com as variáveis já consumidas pelo Reka UI e Tailwind. |
| **Risco 2: Perda de estado de seleção de propostas ao transitar de tela** | Alta | Média | O estado de seleção continuará persistido na store do Pinia / composables existentes (`useProjectStore`), garantindo que alternar entre telas não zere as seleções. |
| **Risco 3: Sobrecarga de memória ao renderizar áudio inline de múltiplas propostas** | Média | Baixa | Instanciar um único elemento de áudio compartilhado no workspace de curadoria, carregando apenas a faixa de áudio sob demanda via streaming da API. |
| **Risco 4: Quebra de testes de integração existentes** | Alta | Baixa | Atualizar os seletores de teste com atributos `data-testid` estáveis em vez de depender de classes visuais ou texto estático suscetível a mudanças de microcópia. |
