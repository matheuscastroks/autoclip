# Especificação de Design: Redesenho da Aba Preparação (Central de Setup & Raio-X do Vídeo)

**Data**: 2026-10-17  
**Status**: Proposto  
**Escopo**: `desktop/src/components/PipelinePanel.vue`, `desktop/src/components/pipeline/*`, `desktop/src/components/ProjectWorkspace.vue`, `desktop/src/composables/usePipelinePresentation.ts`

---

## 1. Contexto e Objetivos

Atualmente, a aba de **Preparação** (`PipelinePanel.vue`) do AutoClip atua essencialmente como uma tela de depuração e telemetria de baixo nível do motor local Python. Nela são exibidos:
- Identificadores de jobs internos em hash (`job-6df9a...`).
- Nomes técnicos de estágios internos do backend (`probe_media`, `extract_audio`, `silero_vad`, `edl_builder`).
- Detalhes de paralelismo e lotes de janelas da IA que geram ruído para o criador de conteúdo.

### Objetivo
Transformar a aba **Preparação** em uma **Central de Setup & Raio-X do Vídeo**, focada exclusivamente em informações e ações que interessam ao editor/criador de conteúdo:
1. **Conferência da Mídia Original**: Player de vídeo 16:9 integrado e metadados úteis em formato humano (duração, resolução, taxa de quadros, contagem de palavras faladas).
2. **Raio-X do Conteúdo**: Após a transcrição e análise, exibir os principais temas/tópicos detectados pela IA e o volume potencial de cortes virais.
3. **Diretrizes de Saída dos Cortes**: Configuração visual prévia dos cortes gerados (escolha do estilo de legenda, velocidade/ritmo de fala e formato 9:16 vertical).
4. **Funil & Ação Primária Clara**: Stepper simples de 4 passos orientados ao usuário (`Mídia Importada` ➔ `Transcrição` ➔ `Análise & Ganchos` ➔ `Cortes Prontos`) e botão evidente para a próxima ação.
5. **Telemetria Opcional/Discreta**: Detalhes técnicos, IDs de jobs e fases de baixo nível movidos para um painel retrátil de diagnóstico, acessível sob demanda ou em caso de erro.

---

## 2. Arquitetura da Interface

A tela é organizada em uma estrutura limpa e balanceada em **2 colunas**:

```
+---------------------------------------------------------------------------------------------------+
|  [STEPPER DO PROJETO]  (1) Mídia Importada  --->  (2) Transcrição  --->  (3) Análise IA  --->  (4) Cortes  |
+---------------------------------------------------------------------------------------------------+
|                                                 |                                                 |
|  COLUNA ESQUERDA: MÍDIA & RAIO-X                |  COLUNA DIREITA: SETUP DOS CORTES & AÇÃO        |
|                                                 |                                                 |
|  [ Card 1: Vídeo Original ]                     |  [ Card 3: Diretrizes de Saída dos Shorts ]    |
|  - Player 16:9 integrado para conferência       |  - Seletor dos 4 estilos de legenda oficiais    |
|  - Metadados humanos em chips:                  |    [Karaoke Amarelo] [Clean White]              |
|    * Duração (ex: 42:15)                        |    [Boxed Contrast]  [Neon Cyan]                |
|    * Resolução & FPS (ex: 1080p 60fps)          |  - Velocidade do Áudio:                         |
|    * Volume de fala (ex: 5.840 palavras)        |    (•) 1.0x Normal  ( ) 1.1x Dinâmico ( ) 1.15x |
|                                                 |  - Formato: Vertical 9:16 (Face Tracking Ativo) |
|  [ Card 2: Raio-X do Conteúdo ]                 |                                                 |
|  - Tags dos temas detectados no vídeo           |  [ Card 4: Ação Principal & Status ]            |
|  - Estimativa de aproveitamento:                |  - Botão de ação evidente (Iniciar/Avançar)     |
|    "X temas identificados · Y cortes em pauta"  |  - Progresso amigável se houver job em execução |
|  - Atalho: "Ver Transcrição Completa"           |  - Link discreto: "Ver diagnóstico técnico"     |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Especificação dos Componentes

### 3.1 Stepper de Macro-Etapas (`PipelineMilestoneStepper.vue`)
Substitui a lista de fases do motor por um indicador visual horizontal no topo:
- **Etapa 1: Mídia**: Importada e pronta para processamento.
- **Etapa 2: Transcrição**: Áudio convertido em texto temporal.
- **Etapa 3: Análise**: Ganchos e tópicos mapeados pela IA.
- **Etapa 4: Cortes**: Clipes verticais prontos para curadoria.
- Cada etapa exibe status: `Pendente`, `Em andamento`, `Concluído` ou `Erro`.

### 3.2 Card 1: Vídeo Original (`SourceMediaCard.vue`)
- Exibe o elemento `<video>` nativo com o arquivo original (`sourceUrl`), permitindo conferir áudio e imagem.
- Grade de chips de metadados:
  - ⏱️ **Duração**: formatada em minutos e segundos (ex: `42 min 18 s`).
  - 🎬 **Resolução**: `1920×1080 · 60 fps` (ou resolução real do probe).
  - 🗣️ **Volume de fala**: total de palavras da transcrição (`project.word_count`).
  - 📁 **Origem**: Arquivo local ou URL importada.

### 3.3 Card 2: Raio-X do Conteúdo (`ContentXRayCard.vue`)
- **Estado 1 (Sem transcrição)**:
  - Mensagem explicativa de que a IA analisará o ritmo e os tópicos assim que a transcrição for iniciada.
- **Estado 2 (Transcrito ou Analisado)**:
  - Nuvem/lista de chips com os **Tópicos Identificados** (`analysis.topics` ou títulos das propostas).
  - Métrica de volume: *"X propostas de cortes identificadas"*.
  - Botão de navegação rápida: *"Abrir Transcrição"* (muda a aba ativa para `transcript`).

### 3.4 Card 3: Diretrizes de Saída dos Shorts (`OutputGuidelinesCard.vue`)
Permite ao usuário definir como os cortes serão renderizados:
- **Estilo de Legenda**: Grade com miniaturas/chips dos 4 estilos validados:
  - `karaoke-yellow-v1` (Padrão viral com destaque amarelo)
  - `clean-white-v1` (Editorial minimalista)
  - `boxed-contrast-v1` (Tarja de alto contraste)
  - `neon-cyan-v1` (Estilo tecnológico/gamer)
- **Ritmo de Fala**:
  - `1.0x` (Original)
  - `1.1x` (Levemente acelerado / Dinâmico)
  - `1.15x` (Rápido)
- **Enquadramento**:
  - Indicador visual do formato `1080×1920` (9:16 vertical) com inteligência de corte facial (*Face Tracking*) ativada.

### 3.5 Card 4: Ação Principal & Status do Job (`PrimaryActionCard.vue`)
- **Ação Contextual**:
  - Se `project.status === 'imported'`: Botão *"Iniciar Transcrição"*.
  - Se `project.status === 'transcribed'`: Botão *"Buscar Cortes com IA"*.
  - Se `project.status === 'analyzed'`: Botão *"Revisar Cortes Sugeridos"*.
  - Se `project.status === 'completed'`: Botão *"Ver Central de Cortes"*.
- **Em Execução**:
  - Exibe barra de progresso suave com percentual e descrição em linguagem natural (ex: *"Transcrevendo áudio localmente..."*, *"Analisando ganchos com IA..."*).
  - Botão de cancelamento seguro.
- **Diagnóstico Técnico**:
  - Link discreto no rodapé: *"Ver detalhes técnicos do motor"*.
  - Ao clicar, abre um Drawer/Modal lateral contendo o `PipelineStepList` técnico com os estágios do ffmpeg/whisper para quem desejar suporte ou depuração.

---

## 4. Estratégia de Implementação e Não-Regressão

1. **Aproveitamento de Composables**:
   - `usePipelinePresentation.ts` continua fornecendo as ações do pipeline (`transcribe`, `analyze`, `render`, `cancel`, `resume`).
   - Os eventos e callbacks existentes entre `ProjectWorkspace.vue` e `PipelinePanel.vue` permanecem 100% preservados.
2. **Preservação de Ações Críticas**:
   - Cancelamento, recuperação de erro, reprocessamento e substituição de mídia continuarão operacionais através do `PrimaryActionCard` e do drawer de diagnóstico.
3. **Design System & Acessibilidade**:
   - Respeita os tokens de cores, tipografia e tema claro/escuro já consolidados no projeto.
   - Navegação completa por teclado e atributos `aria-*` em todos os controles interativos.

---

## 5. Critérios de Aceitação e Testes

- [ ] A aba **Preparação** exibe o Stepper de 4 fases humanas no topo.
- [ ] O Card 1 exibe o player do vídeo original e os metadados humanos sem tecnicalidades vazias.
- [ ] O Card 2 exibe as tags de tópicos do vídeo quando a análise estiver disponível.
- [ ] O Card 3 permite visualizar e selecionar os estilos de legenda e o ritmo dos cortes.
- [ ] O Card 4 exibe a ação primária correta para cada estado do projeto e permite dispará-la.
- [ ] Os testes unitários existentes e testes de integração do frontend continuam passando com 100% de sucesso.
