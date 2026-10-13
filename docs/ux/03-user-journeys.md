# 03. Personas e Jornadas do Usuário Ponta a Ponta

## 1. Definição de Personas

### Persona 1: Beatriz (A Criadora Solo / Social Media)
- **Perfil:** 28 anos, produz conteúdo para YouTube/Instagram e gerencia canais de terceiros. Não é editora de vídeo profissional, mas entende de ganchos virais e retenção de público.
- **Hardware:** Laptop intermediário (Intel i5/Ryzen 5, 16GB RAM, tela 1366×768 ou 1920×1080).
- **Objetivo Principal:** Pegar uma entrevista de 45 minutos gravada no YouTube, extrair 3 a 5 cortes verticais envolventes de até 60 segundos com legendas nítidas para postar no TikTok/Reels em menos de 15 minutos de esforço humano.
- **Dores Principais:** Medo de errar configurações de inteligência artificial; frustração com telas cheias de números, tokens e abas confusas; necessidade de saber exatamente se o corte tem início, meio e fim sem precisar assistir ao vídeo inteiro novamente.
- **Comportamento no AutoClip:** Quer colar o link, clicar em um botão óbvio, sair para tomar um café enquanto o app processa e voltar para uma tela limpa com sugestões prontas para escolher.

---

### Persona 2: Lucas (O Editor Recorrente / Podcaster)
- **Perfil:** 34 anos, co-apresentador e editor de um podcast semanal de 2 horas. Produz de 15 a 20 cortes por semana.
- **Hardware:** Desktop com placa de vídeo dedicada ou laptop veloz (32GB RAM).
- **Objetivo Principal:** Processar múltiplos episódios em lote, gerenciar a fila sem travamentos, comparar diferentes momentos com o mesmo tema e ajustar rapidamente o segundo exato de início e fim da fala.
- **Dores Principais:** Perda de tempo ao ter que entrar em cada projeto individual para saber se terminou; ter cortes cortando a frase no meio; sobreposição acidental de trechos já cortados.
- **Comportamento no AutoClip:** Utiliza intensamente a Fila Global, gosta de revisar as transcrições originais e exportar todos os cortes aprovados em lote para uma pasta organizada.

---

### Persona 3: Rodrigo (O Usuário Técnico / Power User)
- **Perfil:** 26 anos, programador e criador técnico. Gosta de saber qual modelo de IA está rodando e configurar parâmetros de sensibilidade de silêncio e modelos Whisper (base, small, medium).
- **Hardware:** Workstation Linux/Windows com GPU potente.
- **Objetivo Principal:** Maximizar a precisão da transcrição e controlar o comportamento semântico do Gemini, com custos mínimos de API e alta velocidade de renderização local.
- **Dores Principais:** Interfaces simplistas demais que escondem opções avançadas ou não permitem customizar caminhos de salvamento e parâmetros de renderização do FFmpeg.
- **Comportamento no AutoClip:** Acessa as Configurações Avançadas, inspeciona os metadados técnicos sob demanda, mas valoriza uma interface primária rápida e desobstruída.

---

## 2. Mapeamento das Jornadas do Usuário (Fluxos A a H)

### Fluxo A: Onboarding e Configuração Inicial
- **Gatilho:** Primeiro lançamento do aplicativo após instalação.
- **Passos:**
  1. Tela de Boas-Vindas com diagnóstico automático de dependências (FFmpeg embutido, verificação de conexão com internet).
  2. Solicitação amigável da Chave de API do Google Gemini (com link direto para o Google AI Studio e indicação de gratuidade na faixa padrão).
  3. Escolha do perfil de hardware (Modo Equilibrado / CPU vs. Modo Alto Desempenho / GPU).
  4. Confirmação com status visual *"Pronto para criar cortes!"*.
- **Touchpoints:** Assistente de Primeiro Uso (*Onboarding Modal*).
- **Fricção a Evitar:** Não jogar o usuário em uma tela vazia sem explicar o que ele precisa fazer antes de criar um projeto.

---

### Fluxo B: Criação de Projeto via URL do YouTube
- **Gatilho:** Criador deseja transformar um vídeo online em cortes.
- **Passos:**
  1. Usuário clica em *"Novo Projeto"* na Biblioteca.
  2. Cola a URL do vídeo no campo dedicado.
  3. **Validação Imediata (Inline Feedback):** O app valida a URL em tempo real, busca a miniatura (*thumbnail*), título e duração do vídeo antes de confirmar.
  4. Usuário clica em *"Criar e Começar"* (com opção de agendar para depois).
  5. O app adiciona o download à fila e direciona para o Hub de Processamento do Projeto.
- **Fricção a Evitar:** Esperar 5 minutos de processamento para descobrir que o link era privado ou inválido.

---

### Fluxo C: Criação de Projeto via Arquivo Local
- **Gatilho:** Criador possui o arquivo MP4/MKV/MOV gravado em seu computador.
- **Passos:**
  1. Clica em *"Novo Projeto"* e seleciona a aba *"Arquivo no Computador"*.
  2. Arrasta o arquivo ou usa o seletor nativo do sistema operacional.
  3. O app exibe o tamanho do arquivo, taxa de quadros e duração estimada de transcrição.
  4. Usuário clica em *"Iniciar Preparação"*.

---

### Fluxo D: Acompanhamento de Processamento Longo (Whisper + Gemini)
- **Gatilho:** Projeto criado; início da esteira pesada em background.
- **Passos:**
  1. **Etapa 1 (Áudio/Vídeo):** Barra de progresso com porcentagem e status *"Extraindo áudio do vídeo"*.
  2. **Etapa 2 (Transcrição Whisper):** Status visível com *"Transcrevendo fala (Parte X de Y)"* e estimativa de tempo realista baseada no hardware.
  3. **Etapa 3 (Análise Semântica):** Status *"Identificando melhores assuntos e argumentos via Gemini (X janelas processadas)"*.
  4. O usuário pode minimizar o aplicativo, navegar na biblioteca ou fechar a janela com a tranquilidade de que será notificado nativamente no desktop ao concluir.
- **Fricção a Evitar:** Bloquear a interface com modais travados ou exibir loops infinitos de animação.

---

### Fluxo E: Curadoria e Seleção Semântica de Cortes
- **Gatilho:** Notificação de análise concluída recebida pelo usuário.
- **Passos:**
  1. Usuário entra no projeto e visualiza a tela de **Curadoria de Cortes**.
  2. À esquerda: Lista de temas encontrados (ex: *"A diferença entre representatividade e identitarismo"*).
  3. No centro: Cards de propostas de cortes gerados para aquele tema, contendo:
     - Título atraente sugerido pela IA.
     - Gancho inicial (*Hook*) destacado.
     - Duração exata (ex: 42s).
     - Raciocínio editorial do porquê aquele momento é relevante.
     - Botão *"Ouvir áudio"* rápido.
     - Checkbox de seleção para geração de prévia.
  4. **Proteção de Sobreposição em Tempo Real:** Se o corte #3 sobrepuser o corte #1 já selecionado, o corte #3 exibe badge amigável *"Conflita no tempo com Corte #1"* e desabilita a seleção simultânea.
  5. Usuário clica no botão primário *"Gerar X Prévias Selecionadas"*.

---

### Fluxo F: Ajuste e Revisão de Prévias Verticais (9:16)
- **Gatilho:** Prévias renderizadas pelo motor FFmpeg com enquadramento vertical e legendas.
- **Passos:**
  1. Usuário é conduzido à tela de **Estúdio de Revisão**.
  2. O player 9:16 ocupa a área central em escala ideal sem empurrar os controles para fora da tela.
  3. Controles intuitivos: Play/Pause via Barra de Espaço, controle de volume e slider de tempo.
  4. Abaixo/ao lado: Texto da legenda sincronizada, com opção de corrigir palavras ou nomes próprios com 1 clique.
  5. Mini-ajustes de corte: Sliders de *"Ajustar início (+/- 2s)"* e *"Ajustar término (+/- 2s)"* para não cortar a respiração do locutor.

---

### Fluxo G: Exportação Individual e em Lote
- **Gatilho:** Criador aprovou os cortes revisados.
- **Passos:**
  1. Usuário clica em *"Exportar Cortes"* (com contagem explícita: *"3 cortes prontos"*).
  2. Modal de exportação com opções claras:
     - Pasta de destino no computador.
     - Formato e qualidade (Padrão 1080×1920 MP4, 30fps).
     - Opção de exportar descrição pronta para postagem (*copiar texto com hashtags*).
  3. Progresso de exportação exibido com barra de conclusão rápida.
  4. Botão final *"Abrir pasta no computador"*.

---

### Fluxo H: Recuperação de Erros e Interrupções
- **Cenário 1 (Erro 429 de Cota no Gemini):**
  - O app pausa suavemente a análise, salva as janelas já calculadas em disco e exibe banner amigável: *"Limite temporário da API atingido. 5 de 9 partes já estão salvas. Você pode aguardar alguns minutos e continuar sem perder nada."*
  - Botão de 1 clique: *"Continuar análise restante"*.
- **Cenário 2 (Falha no Download do YouTube):**
  - Banner explicativo com alternativas imediatas: *"Não foi possível baixar o vídeo via link. Deseja tentar novamente ou selecionar o arquivo do vídeo gravado no seu computador?"*.
- **Cenário 3 (Cancelamento Voluntário de Fila):**
  - Usuário clica em *"Cancelar"* na Fila Global. O processo é finalizado graciosamente sem deixar arquivos temporários corrompidos travando o disco.
