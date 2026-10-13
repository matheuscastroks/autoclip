# 05. Especificação de Telas, Wireframes ASCII e Guia de Microcópia

## 1. Princípios de Layout para 1366×768

A resolução de referência adotada é **1366×768 pixels**, que impõe restrições severas de altura útil (cerca de 680px descontando a barra do sistema operacional e o cabeçalho da janela).
- **Proibição de Rolagem Dupla:** O layout nunca deve conter uma barra de rolagem externa da página competindo com uma barra interna de componente.
- **Área Reservada para o Player 9:16:** Em 768px de altura, o player vertical vertical não pode exceder 520px de altura (gerando ~292px de largura em proporção 9:16), garantindo que os controles de reprodução e botões de exportação fiquem 100% visíveis acima da dobra (*above the fold*).
- **Adequação de Colunas:** A divisão anterior em 3 colunas paralelas na Análise é substituída por uma arquitetura de 2 colunas flexíveis (*Mestre-Detalhe Limpo*), garantindo largura mínima de linha de 55 caracteres.

---

## 2. Especificação Detalhada e Wireframes ASCII

### Tela 1: Biblioteca de Projetos (`ProjectLibrary`)

```text
+----------------------------------------------------------------------------------------------------+
|  [AutoClip Logo]                    [Fila Global (2)]  [Configurações]         [+ Novo Projeto (Prim)] |
+----------------------------------------------------------------------------------------------------+
|  Seus Projetos                                                                                      |
|  Transforme vídeos longos em cortes curtos prontos para publicação                                 |
|                                                                                                    |
|  [ Q Buscar por título ou data... ]                   Filtros: [Todos (3)] [Em andamento] [Prontos] |
|                                                                                                    |
|  +---------------------------+  +---------------------------+  +---------------------------+       |
|  | [ Thumbnail ]     45:12   |  | [ Thumbnail ]     18:30   |  | [ Thumbnail ]     05:10   |       |
|  | O que é corrupção?        |  | Voto e Identidade         |  | Podcast Episódio 4        |       |
|  | [Status: 4 cortes prontos]|  | [Status: 2 cortes prontos]|  | [Status: Transcrevendo 62%|       |
|  | Atualizado há 2 horas     |  | Atualizado ontem          |  | Iniciado há 5 minutos     |       |
|  | [Abrir Projeto]           |  | [Abrir Projeto]           |  | [Ver Progresso]           |       |
|  +---------------------------+  +---------------------------+  +---------------------------+       |
+----------------------------------------------------------------------------------------------------+
```

#### Regras de Interação:
- **Clique no Card Inteiro:** Clicar em qualquer ponto do card abre o projeto (área de clique expandida para conforto).
- **Estado Vazio (Empty State):** Caso não haja projetos, exibe ilustração minimalista, texto acolhedor e botão central de destaque *"Criar meu primeiro projeto"*.

---

### Tela 2: Modal / Drawer da Fila Global (`GlobalQueueDrawer`)

```text
+----------------------------------------------------------------------------------------------------+
|                                                                    FILA GLOBAL DE TAREFAS  [ X ]    |
|                                                                                                    |
|  TAREFAS EM ANDAMENTO (1)                                                                          |
|  +----------------------------------------------------------------------------------------------+  |
|  | [Ícone] Transcrevendo áudio via Whisper (CPU)                                                |  |
|  | Projeto: "Podcast Episódio 4" · Etapa 2 de 3                                                  |  |
|  | [==================================== 62% =========================] Estimativa: ~2 min     |  |
|  | [Abrir Projeto]                                                       [Cancelar Tarefa]      |  |
|  +----------------------------------------------------------------------------------------------+  |
|                                                                                                    |
|  TAREFAS CONCLUÍDAS RECENTEMENTE (2)                                                                |
|  +----------------------------------------------------------------------------------------------+  |
|  | [✓] Análise Semântica concluída · "O que é corrupção?" · 7 propostas encontradas             |  |
|  | [✓] Renderização de 2 prévias concluída · "Voto e Identidade"                                |  |
|  +----------------------------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------------------------+
```

---

### Tela 3: Hub do Projeto (`ProjectHub`)

```text
+----------------------------------------------------------------------------------------------------+
|  [← Voltar à Biblioteca]  /  O que é corrupção?                [Fila Global]  [Configurações]       |
+----------------------------------------------------------------------------------------------------+
|  ESTEIRA DE PREPARAÇÃO                                                                             |
|  (1) Importação [✓]  ->  (2) Transcrição [✓]  ->  (3) Análise de Temas [✓]  ->  (4) Revisão [3 Cortes] |
|                                                                                                    |
|  +----------------------------------------------------------------------------------------------+  |
|  | ETAPA ATUAL: Curadoria Editorial Pronta                                                      |  |
|  | A IA encontrou 7 propostas de cortes relevantes e 3 temas principais neste vídeo.             |  |
|  |                                                                                              |  |
|  | [ ABRIR CURADORIA E ESCOLHER CORTES (Primário) ]            [ Ver Transcrição Completa ]      |  |
|  +----------------------------------------------------------------------------------------------+  |
|                                                                                                    |
|  RESUMO DO VÍDEO ORIGINAL                                                                          |
|  • Duração: 22m 45s  • Qualidade: 1080p  • Arquivo: local_corrupcao.mp4  • Cortes gerados: 3        |
+----------------------------------------------------------------------------------------------------+
```

---

### Tela 4: Workspace de Curadoria de Cortes (`CurationWorkspace`)

```text
+----------------------------------------------------------------------------------------------------+
|  [← Voltar ao Hub]  /  Curadoria de Cortes: "O que é corrupção?"       [Ajuda]  [Ver Transcrição]  |
+----------------------------------------------------------------------------------------------------+
|  TEMAS IDENTIFICADOS (Filtros)       |  PROPOSTAS DE CORTES (7 encontradas)                         |
|                                      |                                                              |
|  [•] Todos os temas (7)              |  [✓] Corte #1 · 00:42 às 01:25 (43 segundos)                |
|  [ ] Conceito filosófico (3)         |  TÍTULO: "Por que a corrupção começa antes da lei?"        |
|  [ ] Exemplos práticos (2)           |  GANCHO: "Todo mundo acha que corrupção é só dinheiro..."   |
|  [ ] Conclusão e impacto (2)         |  POR QUE FUNCIONA: Apresenta quebra de expectativa nos      |
|                                      |  primeiros 5 segundos com alta retenção.                     |
|                                      |  [ ▶ Ouvir Trecho (Áudio) ]        [Conflitos: Nenhum]       |
|                                      |  ----------------------------------------------------------  |
|                                      |  [X] Corte #2 · 01:10 às 01:50 (40 segundos) (BLOQUEADO)    |
|                                      |  TÍTULO: "A linha tênue entre jeitinho e crime"              |
|                                      |  [ ⚠ Conflita no tempo com o Corte #1 já selecionado ]       |
|                                      |  [ ▶ Ouvir Trecho (Áudio) ]                                  |
|                                      |                                                              |
+--------------------------------------+--------------------------------------------------------------+
|  BARRA FLUTUANTE DE AÇÃO:  3 cortes selecionados (Total: 2m 15s)      [ GERAR 3 PRÉVIAS VERTICAIS ] |
+----------------------------------------------------------------------------------------------------+
```

---

### Tela 5: Estúdio de Revisão e Prévia 9:16 (`ReviewStudio`)

```text
+----------------------------------------------------------------------------------------------------+
|  [← Voltar à Curadoria]  /  Revisão dos Cortes                     [Exportar Todos os Cortes (3)]   |
+----------------------------------------------------------------------------------------------------+
|  SEUS CORTES (3)     |           PLAYER VERTICAL 9:16            |  AJUSTES DO CORTE SELECIONADO    |
|                      |                                           |                                  |
|  [•] Corte 1 [Pronto]|               +-----------------+         |  TÍTULO DO VÍDEO                 |
|      43s · Filosofia |               |                 |         |  [Por que a corrupção começa?]   |
|                      |               |   [ VÍDEO       |         |                                  |
|  [ ] Corte 2 [Pronto]|               |     VERTICAL    |         |  AJUSTE FINO DE TEMPO            |
|      38s · Exemplo   |               |     9:16 ]      |         |  Início: [- 0.5s] 00:42.0 [+ 0.5s|
|                      |               |                 |         |  Término:[- 0.5s] 01:25.0 [+ 0.5s|
|  [ ] Corte 3 [Pronto]|               |  "Todo mundo    |         |                                  |
|      55s · Conclusão |               |   acha que..."  |         |  EDITOR DE LEGENDAS              |
|                      |               |                 |         |  [ "Todo mundo acha que a..." ]  |
|                      |               +-----------------+         |  [Corrigir palavras em linha]    |
|                      |            [ ▶ ]  00:15 / 00:43  [ 🔊 ]   |                                  |
|                      |                                           |  [ BAIXAR ESTE VÍDEO (MP4) ]     |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Guia de Microcópia e Comunicação com o Usuário

### Regras Gerais:
1. **Verbos de Ação Direta:** Botões devem informar exatamente o que acontece quando clicados (*"Gerar 3 prévias"*, *"Baixar vídeo MP4"*, *"Continuar análise"* em vez de *"OK"*, *"Avançar"* ou *"Submit"*).
2. **Eliminação de Jargão Técnico:**
   - Trocar *"Janelas validadas"* por *"Partes analisadas"*.
   - Trocar *"Overlap detectado"* por *"Conflito de horário com outro corte"*.
   - Trocar *"Erro 429 Quota Exceeded"* por *"Limite temporário da API do Gemini atingido"*.
   - Trocar *"Revisões"* por *"Cortes gerados"*.
3. **Padrão de Mensagens de Erro Construtivas:**

| Situação | Mensagem Atual (Ruim) | Nova Mensagem (Padrão Recomendado) |
| :--- | :--- | :--- |
| Falha no download do YouTube | `Error: yt-dlp returned code 1` | **Não foi possível baixar o vídeo via link.** O vídeo pode ser privado ou exigir confirmação. Tente novamente ou use o arquivo baixado em seu computador. |
| Limite de taxa da API | `Gemini API 429: Rate limit reached` | **Limite temporário de requisições atingido.** 5 de 9 partes já foram salvas em disco. Aguarde 2 minutos e clique em "Continuar análise restante". |
| Conflito de sobreposição | Checkbox simplesmente desabilitada | **Este trecho coincide com o Corte #1.** Para selecionar este corte, desmarque o Corte #1 primeiro. |
| Transcrição demorada em CPU | Spinner parado sem texto | **Transcrevendo fala usando o processador da sua máquina.** Isso pode levar alguns minutos. Você pode navegar normalmente enquanto concluímos. |
