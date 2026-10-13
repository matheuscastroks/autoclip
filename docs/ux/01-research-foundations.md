# 01. Fundamentos Metodológicos, Bibliografia e Benchmark Competitivo

## 1. Visão Geral e Contexto do Estudo

O **AutoClip** é uma aplicação desktop *local-first* construída com Tauri 2 (Rust) e Vue 3 + TypeScript, acoplada a um motor local em Python (FastAPI). Sua missão central é:
> **Permitir que criadores de conteúdo transformem vídeos longos (entrevistas, podcasts, aulas, palestras) em cortes verticais (9:16) coerentes, com legendas sincronizadas e remoção de pausas mortas, prontos para publicação, com o mínimo de atrito operacional.**

Para fundamentar o redesenho de UX/UI com rigor científico e técnico, este documento sintetiza:
1. **Modelos teóricos e metodologias consagradas de IHC e Design de Interação** (Nielsen Norman Group, ISO 9241-210, Carbon Design System, GOV.UK, WCAG 2.2 AA).
2. **Benchmark competitivo estruturado** analisando produtos líderes de mercado (*OpusClip, Descript, CapCut Desktop, VEED.IO, Riverside.fm*).
3. **10 Princípios Norteadores de Produto e Design** aplicados estritamente à realidade de processamento em máquina local e limitações de hardware/cota.

---

## 2. Modelos Teóricos e Metodologias de Referência

### 2.1. Nielsen Norman Group (NN/g): Heurísticas e Tempos de Resposta

#### A. Os Três Limites de Tempo de Resposta (Jakob Nielsen)
*Fonte: [NN/g - Response Times: The 3 Important Limits](https://www.nngroup.com/articles/response-times-3-important-limits/)*
- **0,1 segundo (100 ms):** Limite para que o usuário sinta manipulação direta. O sistema parece reagir instantaneamente.
  *Aplicação no AutoClip:* Alternância de abas, seleção/desmarcação de checkbox de proposta, scrubber de áudio/vídeo, filtros de busca.
- **1,0 segundo (1000 ms):** Limite para fluxo contínuo de pensamento. O usuário percebe um breve atraso, mas não perde o foco.
  *Aplicação no AutoClip:* Carregamento da transcrição, expansão de detalhes de proposta, alternância de projeto na biblioteca.
- **10 segundos:** Limite absoluto para atenção sustentada em uma única tela. Após 10 segundos, o usuário busca outra tarefa ou presume congelamento.
  *Aplicação no AutoClip:* Transcrição via Whisper em CPU pode levar de 3 a 15 minutos; renderização de prévia pode levar 45 a 120 segundos. **Obrigatório:** fornecer indicadores de progresso determinados (porcentagem e tempo estimado), feedback contínuo de logs de alto nível e liberdade para minimizar o app ou navegar em outros projetos em background.

#### B. Gestão de Esperas e Interrupções (*Designing for Waits and Interruptions*)
*Fonte: [NN/g - Designing for Long Waits and Interruptions](https://www.nngroup.com/articles/designing-for-waits-and-interruptions/)*
- **Determinada vs. Indeterminada:** Spinners infinitos são proibidos para tarefas que duram mais de 5 segundos. Quando o cálculo exato de tempo não estiver disponível (ex: análise semântica por janelas), o sistema deve decompor a tarefa em etapas visíveis (ex: *"Janela 3 de 9 analisada"*).
- **Tratamento de Interrupção / Retomada:** Operações interrompidas (queda de energia, limite de taxa 429 da API Gemini, encerramento do processo) devem preservar checkpoints em disco e apresentar opções de retomada com 1 clique (*Resume*), sem perda do trabalho previamente concluído.

#### C. Divulgação Progressiva (*Progressive Disclosure*)
*Fonte: [NN/g - Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)*
- Separar informações primárias essenciais (título do corte, frase de impacto, duração, botão de gerar/ouvir) de detalhes técnicos secundários (janela de tempo exata em milissegundos, modelo do Gemini, contagem de tokens, argumentos de linha de comando FFmpeg).
- Padrão recomendado: Superfície limpa por padrão com gatilhos contextuais acessíveis (*"Ver contexto completo"*, *"Ajustes avançados"*).

#### D. Wireflows e Task Analysis
*Fontes: [NN/g - Wireflows](https://www.nngroup.com/articles/wireflows/) e [NN/g - Task Analysis](https://www.nngroup.com/articles/task-analysis/)*
- Wireflows unem a arquitetura de informação e as rotas de navegação aos esboços de tela, tornando explícitos os nós de decisão e estados de erro/recuperação antes da escrita de código.

---

### 2.2. Padrões de Design de Sistemas Governamentais e Corporativos

#### A. Carbon Design System — Progress Indicators
*Fonte: [Carbon Design System - Progress Indicator](https://carbondesignsystem.com/components/progress-indicator/usage/)*
- **Distinção conceitual:** 
  - *Progress Indicator:* Mapeia um fluxo linear de 3 ou mais etapas sequenciais onde o usuário avança conceitualmente.
  - *Progress Bar:* Mede a porcentagem de conclusão de uma operação técnica única (ex: upload, download, render).
  - *Loading / Spinner:* Operação assíncrona transitória de curta duração (< 4s).
- **Navegabilidade:** Etapas já concluídas tornam-se âncoras navegáveis para revisão. Etapas futuras bloqueadas não devem permitir salto acidental sem cumprimento dos pré-requisitos.

#### B. GOV.UK Design System — Padrão Task List
*Fonte: [GOV.UK - Task List Pattern](https://design-system.service.gov.uk/patterns/task-list-pages/)*
- Em fluxos multifacetados, a página principal do projeto funciona como um *Hub de Tarefas* central. Cada tarefa exibe:
  - Título baseado em verbo (*"Importar vídeo"*, *"Revisar temas"*, *"Gerar cortes"*).
  - Tag de status semântica clara (*Concluído*, *Em andamento*, *Pendente*, *Falha*).
  - Permite ao usuário retornar à visão geral a qualquer momento sem perder o contexto.

---

### 2.3. Acessibilidade Digital (WCAG 2.2 AA Desktop)
*Fonte: [W3C - Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/)*

Critérios prioritários identificados para o AutoClip Desktop:
1. **SC 1.4.3 Contraste Mínimo (4.5:1 para texto normal, 3:1 para texto grande):** Textos auxiliares e timestamps não podem usar cinzas desbotados sobre fundos escuros/claros.
2. **SC 1.4.11 Contraste de Elementos Não-Textuais (3:1):** Bordas de inputs, checkboxes de seleção de proposta e controles de player devem manter distinção visual nítida.
3. **SC 2.1.1 Teclado (Operável por Teclado):** Toda a aplicação deve ser navegável sem mouse. **Auditoria identificou:** atualmente, 789 botões de timestamp na transcrição criam uma barreira intransponível de navegação (*keyboard fatigue*). Necessário agrupar parágrafos em blocos semânticos e virtualizar linhas.
4. **SC 2.4.7 Foco Visível & SC 2.4.11 Foco Não Encoberto (WCAG 2.2):** O anel de foco (*focus-ring*) deve ter espessura mínima de 2px com contraste de 3:1 e nunca ficar sob painéis flutuantes ou cabeçalhos fixos.
5. **SC 2.5.8 Tamanho do Alvo Mínimo (WCAG 2.2):** Alvos interativos devem medir pelo menos 24×24px ou possuir espaçamento equivalente. **Auditoria identificou alvos de 17px a 21px** que violam esta diretriz.
6. **SC 4.1.3 Mensagens de Status (Aria-Live):** Quando um job de renderização termina ou uma análise falha em background, leitores de tela devem ser notificados via regiões `aria-live="polite"` sem interromper o foco ativo.

---

## 3. Benchmark Competitivo Estruturado

A análise baseia-se na documentação oficial e fluxos públicos documentados de 5 soluções líderes:

| Produto | Entrada e Configuração | Modelo de Curadoria de Cortes | Comunicação de Progresso | Revisão e Edição | Lições para o AutoClip |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OpusClip** *(Verificado em opus.pro)* | URL YouTube ou upload local. Opção de intervalo de tempo. | **Virality Score (1-100)** baseado em Gancho (Hook), Fluxo, Valor e Tendência. Propostas em grid vertical com tags de assunto. | Barra de progresso com porcentagem e tempo estimado de fila em nuvem. | Player vertical 9:16 com edição de legendas em linha e re-enquadramento facial. | **Adaptar:** Pontuação de coerência e destaque explícito do "Gancho/Hook". **Evitar:** Transformar pontuação em verdade absoluta; manter curadoria humana evidente. |
| **Descript** *(Verificado em descript.com)* | Gravação direta ou upload. Transcrição imediata. | **Underlord (Create Clips):** Gera composições isoladas a partir da transcrição. | Painel lateral de status com notificações no app. | Edição por texto (deletar texto corta o vídeo). Linha do tempo multipista avançada. | **Adaptar:** Inspeção de trecho alinhada com o texto original da transcrição. **Evitar:** Complexidade de linha do tempo multipista (NLE completo), que sobrecarrega criadores não-editores. |
| **CapCut Desktop** *(Verificado em capcut.com)* | Importação local tradicional ou ferramenta *"Long Video to Shorts"*. | Detecção de fala, silêncios e marcações de tempo em lote. | Barra de carregamento e importação em modal. | Timeline profissional completa com trilhas, efeitos e transições pesadas. | **Adaptar:** Remoção automática e configurável de silêncios longos. **Evitar:** Poluição de painéis de efeitos e timeline densa para o caso de uso de corte rápido. |
| **VEED.IO** *(Verificado em veed.io)* | Upload no navegador ou URL. | **Magic Cut / AI Clips:** Remove silêncios e gera listas de destaques com sugestões de títulos. | Indicador percentual com passos de pipeline claros. | Player com legendas dinâmicas palavra por palavra (*karaokê*). | **Adaptar:** Estilos claros de legenda dinâmica e títulos persuasivos pré-sugeridos. **Evitar:** Dependência de conexão ininterrupta e lentidão de render via WebGL. |
| **Riverside.fm** *(Verificado em riverside.fm)* | Gravação em estúdio ou upload na nuvem. | **Magic Clips (Made for You):** Agrupamento por tópico e orador. | Geração em background assíncrona; cartão de notificação no projeto. | Trim de início/fim e ajuste de crop do orador em 9:16. | **Adaptar:** Notificações não-bloqueantes de conclusão e foco no orador. **Evitar:** Geração cega automática antes da revisão de transcrição (evita erros em nomes e termos). |

---

## 4. 10 Princípios Norteadores de UX para o AutoClip

1. **Visibilidade de Estado Sem Jargão:** O usuário deve saber em qual etapa o vídeo se encontra (*"Extraindo áudio"*, *"Transcrevendo fala"*, *"Identificando temas"*) sem precisar ler logs de FFmpeg ou tokens de LLM.
2. **Processamento Assíncrono Desacoplado:** O processamento em CPU/API nunca deve travar a navegação. O usuário pode criar novos projetos, inspecionar a transcrição ou fechar telas secundárias enquanto o motor executa.
3. **Resiliência e Recuperação com 1 Clique:** Falhas de cota ou interrupções parciais não invalidam o progresso anterior. Botão contextual de retomar e recuperação automática.
4. **Sem Sobreposição (No-Overlap By Design):** Propostas com conflito temporal devem ser bloqueadas na UI com explicação imediata (*"Conflita com Corte #2 selecionado"*), evitando cortes redundantes.
5. **Legibilidade e Contenção de Densidade:** Em resoluções padrão desktop (1366×768), o player vertical 9:16 e o texto do corte devem coexistir sem barras de rolagem triplas ou colunas colapsadas.
6. **Alvos Interativos Confortáveis (WCAG 2.5.8):** Nenhum botão ou link de ação com altura inferior a 24px (ideal 32px a 40px para ações de curadoria).
7. **Navegação por Teclado Amigável (Zero Keyboard Fatigue):** Substituir centenas de micro-botões de timestamp por blocos agrupados com atalhos de reprodução rápidos (Espaço para Play/Pause, J/K/L para navegação).
8. **Curadoria Assistida, Não Automação Cega:** A IA propõe títulos, notas de coerência e janelas de corte; o criador humano valida, ajusta início/fim e decide o que exportar.
9. **Microcópia Construtiva e Sem Culpa:** Mensagens de erro informam a causa, o impacto e a ação de correção concreta, sem desculpas vazias ou códigos numéricos opacos.
10. **Local-First & Privacidade Explicada:** Clareza absoluta de que o vídeo original permanece localmente na máquina e apenas trechos de texto transcrito trafegam para a API do Gemini.
