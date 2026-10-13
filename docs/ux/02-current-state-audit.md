# 02. Auditoria Heurística Profunda e Diagnóstico do Estado Atual

## 1. Metodologia da Auditoria e Setup Técnico

A auditoria foi realizada no ambiente de execução real do AutoClip:
- **Repositório:** `matheuscastroks/autoclip`
- **Branch Ativa:** `poc-openshorts-gemini` (commit `ae530f5`)
- **Resolução de Teste:** 1366×768 pixels (padrão de referência para laptops compactos e telas de entrada desktop)
- **Engine Ativa:** FastAPI local (`http://127.0.0.1:58057/`) com projetos reais em disco:
  1. `0f70cc83-...` ("teste"): Falha na importação de vídeo.
  2. `57ad6505-...` ("Voto-identidade-e-SnapYT.App"): 8 propostas, 3 selecionadas, 2 cortes gerados.
  3. `6bd08ddb-...` ("O que é corrupção?"): 7 propostas, 4 selecionadas, 22 revisões geradas.
- **Instrumentação:** Capturas de tela full-page via CDP (Chrome DevTools Protocol) e extração de métricas de DOM (`metrics-1366x768.json`).

---

## 2. Inventário de Telas e Análise de Layout (1366×768)

| Tela / Estado | Viewport vs. Altura Real (`scrollHeight`) | Elementos Focáveis / Botões | Violações de Alvo Mínimo (<24px) | Problemas Críticos Observados |
| :--- | :--- | :--- | :--- | :--- |
| **01. Biblioteca de Projetos (`ProjectLibrary.vue`)** | 768px / 768px | 20 focáveis / 17 botões | Input busca: 802×17px; Títulos de card: ~18px alt. | Lista limpa, mas cards possuem áreas clicáveis reduzidas. O botão primário "Novo projeto" fica no header e não há atalho na área central vazia. |
| **02. Fila Global de Tarefas (`GlobalQueueModal.vue`)** | 768px / 768px | 26 focáveis / 23 botões | Botão "Abrir este projeto": 223×21px alt. | Modal centralizado; resolve a visualização multi-projeto, mas títulos longos de jobs comprimem as barras de progresso e botões de cancelar. |
| **03. Modal Novo Projeto (`ProjectCreationDialog.vue`)** | 768px / 768px | 27 focáveis / 23 botões | - | Campos de URL e Arquivo Local funcionam bem, mas validação de URL só ocorre após submissão. Opções avançadas expostas sem contexto. |
| **04. Configurações (`SettingsModal.vue`)** | 768px / 768px | 18 a 21 focáveis | Botões de accordions: 467×21px e 1002×21px alt. | Dividido em 3 abas ("Processamento local", "Chave Gemini", "Coerência e pausas"). Excesso de jargão técnico (temperatura, overlap ratio, chunk size). |
| **05. Visão Geral / Preparação (`PipelinePanel.vue`)** | 768px / 1115px (Overflow vertical de 347px) | 22 a 26 focáveis / 21 botões | "Ver motivo da falha": 114×17px; "Fechar aviso": 20×20px; "Detalhes técnicos": 237×21px. | **Overflow severo.** Em telas 1366×768, o usuário é obrigado a rolar verticalmente para ver o stepper completo. Saltos de cabeçalho (H1 -> H3 direto). |
| **06. Transcrição (`TranscriptViewer.vue`)** | 768px / 768px (scroll interno) | **791 focáveis / 789 botões interativos** | - | **Barreira de acessibilidade severa:** Cada frase/segmento de tempo é um botão de foco. Navegar por Tab exige 789 toques para ultrapassar a transcrição. |
| **07. Análise e Propostas (`AnalysisPanel.vue`)** | 768px / 768px (scroll interno) | 55 focáveis / 40 botões | "Buscar": 441×17px; "Frase de abertura": 532×21px; "Fala e contexto": 532×22px; "Pausar": 149×17px. | **Sobrecarga cognitiva extrema:** Layout dividido em 3 colunas estreitas (Tópicos | Lista de Propostas | Detalhes do Trecho). Em 1366px de largura, o texto quebra a cada 4 palavras. |
| **08. Revisão e Cortes (`CutsPanel.vue`)** | 768px / 1312px (Overflow vertical de 544px) | 34 focáveis / 23 botões | "Detalhes técnicos": 1030×21px. | **Conflito de espaço 9:16:** O player vertical ocupa altura excessiva, empurrando a tabela de propostas e botões de exportação para fora da primeira dobra da tela. Barra de rolagem dupla aninhada. |

---

## 3. Avaliação Segundo as 10 Heurísticas de Nielsen

### Heurística 1: Visibilidade do Status do Sistema
- **Status:** *Parcialmente atendida (Severidade 2 - Menor)*
- **Diagnóstico:** A inclusão da esteira de etapas e da fila global melhorou o diagnóstico imediato. No entanto, quando um job do Whisper inicia em CPU, a estimativa de tempo restante oscila ou desaparece, deixando o usuário em dúvida se a máquina travou. Na análise do Gemini, falhas de cota exibem mensagens genéricas de erro antes que o usuário clique em "Ver motivo da falha".

### Heurística 2: Correspondência entre o Sistema e o Mundo Real
- **Status:** *Violação Moderada (Severidade 3 - Grave)*
- **Diagnóstico:** A terminologia atual reflete a arquitetura do código ao invés do modelo mental do criador de conteúdo:
  - *"Janelas validadas (9/9)"* -> O usuário não pensa em janelas de tokenização, pensa em *"Partes do vídeo analisadas"*.
  - *"Propostas"* vs. *"Candidatos"* vs. *"Cortes"* -> Três termos usados alternadamente na UI para o mesmo conceito.
  - *"Revisões"* -> Termo interno da API que confunde o usuário (ele espera ver *"Versões geradas"* ou *"Prévia vertical"*).

### Heurística 3: Controle e Liberdade do Usuário
- **Status:** *Atendida com Ressalvas (Severidade 2)*
- **Diagnóstico:** O cancelamento de jobs na fila global foi implementado com sucesso. No entanto, na tela de Cortes, não há botão direto para desfazer uma exclusão de corte ou reverter uma alteração de legenda/título sem recarregar o projeto.

### Heurística 4: Consistência e Padrões
- **Status:** *Violação Moderada (Severidade 2)*
- **Diagnóstico:**
  - Inconsistência na hierarquia tipográfica: Em `PipelinePanel.vue`, há títulos `<h3>` sem pais `<h2>`.
  - Disparidade nos botões de ação: O botão de "Gerar prévias" aparece com estilo primário no header da aba, no stepper de progresso e na lista de propostas, gerando ambiguidade sobre qual ação tem escopo global ou local.

### Heurística 5: Prevenção de Erros
- **Status:** *Atendida Recentemente (Severidade 1)*
- **Diagnóstico:** A recente implementação de trava contra trechos sobrepostos (*No-overlap*) evitou seleções duplicadas de trechos temporais adjacentes. Entretanto, no modal de novo projeto, links inválidos do YouTube ou arquivos de formato incompatível não são detectados em tempo real de digitação (*onInput blur*), apenas quando o job falha minutos depois.

### Heurística 6: Reconhecimento em Vez de Memorização
- **Status:** *Violação Grave (Severidade 3)*
- **Diagnóstico:** Ao avaliar uma proposta na aba "Análise", o usuário precisa memorizar a transcrição original ou alternar entre a aba "Transcrição" e a aba "Análise", pois o contexto amplo de áudio não fica visível lado a lado com o player.

### Heurística 7: Flexibilidade e Eficiência de Uso
- **Status:** *Violação Crítica (Severidade 4)*
- **Diagnóstico:** A ausência de atalhos de teclado globais para reprodução (ex: barra de espaço para Play/Pause ao inspecionar áudio ou vídeo) força o usuário a usar o mouse constantemente. Além disso, a navegação via Tab no teclado fica bloqueada pelos 789 botões da transcrição.

### Heurística 8: Estética e Design Minimalista
- **Status:** *Violação Moderada (Severidade 3)*
- **Diagnóstico:** O painel de análise com 3 colunas paralelas tenta exibir tudo simultaneamente (tópicos, cards e detalhes), resultando em caixas de texto de largura inferior a 250px. Isso força quebras de linha desagradáveis e cansaço visual. Menos densidade e navegação mestre-detalhe progressiva trariam maior clareza.

### Heurística 9: Ajudar os Usuários a Reconhecer, Diagnosticar e Recuperar-se de Erros
- **Status:** *Atendida com Ressalvas (Severidade 2)*
- **Diagnóstico:** O botão de "Continuar análise das janelas restantes" adicionado recentemente mitigou os erros de cota 429. Contudo, em falhas de importação de vídeo (ex: erro de SSL ou formato de áudio corrompido), a mensagem fica escondida atrás de um link de 17px (*"Ver motivo da falha"*), sem orientação clara de como corrigir (ex: *"Reinstale o yt-dlp"* ou *"Selecione o arquivo local MP4"*).

### Heurística 10: Ajuda e Documentação
- **Status:** *Violação Leve (Severidade 2)*
- **Diagnóstico:** Não há tooltips contextuais explicativos sobre o que significam métricas como "Coerência de Raciocínio", "Tratamento de Pausas" ou como as legendas automáticas foram geradas.

---

## 4. Violações Específicas de Acessibilidade (WCAG 2.2 AA)

1. **SC 2.5.8 Target Size (Minimum 24×24px):**
   - Vários links secundários e botões de fechamento de banner medem entre 17px e 21px de altura (`metrics-1366x768.json`). Devem ser aumentados para no mínimo 32px ou possuir área de clique expandida com padding invisível.
2. **SC 2.1.1 Keyboard Navigation & SC 2.4.7 Focus Visible:**
   - 789 elementos interativos individuais na transcrição precisam ser desativados do tab-order sequencial (`tabindex="-1"`) e substituídos por um container único navegável com setas direcionais e barra de espaço.
3. **SC 1.4.3 Minimum Contrast (4.5:1):**
   - Subtítulos e metadados secundários renderizados em cinza claro com opacidade baixa violam o contraste em temas escuros.

---

## 5. Conclusão do Diagnóstico

O motor técnico do AutoClip é robusto e possui dados ricos gerados pela IA e pelo Whisper. Contudo, **a interface atual expõe os encanamentos técnicos diretamente ao usuário**, fragmentando uma jornada que deveria ser fluida em abas desconexas, sobrecarregando telas de 1366×768 e gerando esforço cognitivo desnecessário. O redesenho deve adotar uma estrutura linear orientada a objetivos (*Goal-Directed Design*).
