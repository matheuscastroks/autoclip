# Experiência de análise e preparação de cortes

Status: proposta de melhoria para revisão. Não implementada nesta entrega.
Data: 12/10/2026.

## Objetivo

Permitir compreender o conteúdo identificado, escolher os trechos que merecem uma prévia e acompanhar cada etapa até a exportação, sem depender de um loading genérico. O modelo sugere; o usuário decide o que gerar e aprova o que publicar.

## Diagnóstico confirmado no código

- ProjectWorkspace.vue possui Visão geral, Transcrição e Cortes; não existe uma área de análise de temas/propostas.
- analysis.json contém temas, evidências, motivos e limites de candidatos. A API oferece transcrição/revisões e eventos técnicos, mas não uma visão de produto desses resultados.
- AnalysisFeedback mostra o resumo da janela atual e uma parcela dos resultados dessa janela; não é um catálogo completo da análise do vídeo.
- PipelinePanel combina geração e revisão em Gerar e revisar. São trabalhos diferentes: processamento do motor e decisão humana.
- O backend reporta principalmente render em execução/concluído. Preparação da edição, pausas, legendas, renderização e verificação existem no pipeline, mas não têm acompanhamento granular de produto.
- No exemplo real: 7 janelas, 5.556 palavras e 19 propostas. A seleção existente ainda limita a 3 candidatos; essa redução não fica clara antes da geração.
- Temas são registros por janela. Não se pode chamar a contagem bruta de quantidade de temas únicos.
- A mensagem vazia de Cortes sugere que basta concluir a análise; na prática, a prévia precisa ser gerada antes de aparecer para revisão.

## Organização recomendada

Quatro abas principais: **Visão geral | Transcrição | Análise | Cortes**.

| Aba | Responsabilidade | Ação principal |
|---|---|---|
| Visão geral | Original, estado geral, etapa atual e próximo passo | Ver análise / Continuar análise / Acompanhar geração |
| Transcrição | Ler e conferir a fala original com navegação por tempo | Reproduzir trecho no original |
| Análise | Temas, argumentos, propostas, contexto e escolha do que gerar | Gerar N prévias selecionadas |
| Cortes | Fila de geração, prévias prontas, revisão e exportação | Revisar prévia / Exportar aprovados |

A Visão geral mantém a divisão 50/50 aprovada, com resumo compacto do processamento e links para a área correspondente. A aba Análise recebe os detalhes e os resumos Gemini; evita-se duplicar o texto longo em duas superfícies. Trocar de aba não inicia nem cancela tarefas, nem faz chamadas ao Gemini.

## Aba Análise

- Cabeçalho com estado, janelas concluídas/total, propostas recebidas e selecionadas. Contar unidades concluídas, não porcentagem de tempo gasto.
- Lista de temas à esquerda; painel de propostas/detalhe e player do original ao lado. Em notebook menor, lista de temas vira filtro e conteúdo empilha.
- Cada tema: nome, resumo curto, ocorrências e quantidade de propostas associadas. Agrupar inicialmente apenas rótulos iguais após normalização conservadora; manter todos os IDs/proveniências originais. Não unir argumentos diferentes por palavras parecidas ou eliminar negações.
- Cada proposta: título, duração real, intervalo original, justificativa breve, condição de integridade/contexto e controle de seleção.
- Detalhe expandido: argumento completo, trecho textual, ressalvas, evidências e reprodução do original com contexto antes/depois. IDs de palavra e parâmetros técnicos ficam nos detalhes avançados.
- Não renderizar um MP4 para ouvir uma sugestão: navegar ao intervalo no vídeo original e delimitar a reprodução.
- Estados de proposta: disponível, requer atenção, incompatível com os limites, selecionada, em geração, prévia disponível.
- Propostas incompatíveis com limites/boundaries ou flags editoriais atuais não podem ser geradas silenciosamente. Explicar o motivo. A primeira versão preserva as regras atuais de integridade; edição/override editorial explícito fica para uma evolução posterior.
- Sobreposição é informada ao comparar propostas. Para seleção manual de variantes tecnicamente elegíveis, o usuário pode escolher ambas; o sistema não deve descartá-las silenciosamente como se fossem inválidas.
- Seleção é persistida por projeto e hash da análise. Nova análise/configuração incompatível torna a seleção anterior desatualizada, sem reutilizar IDs de outro resultado.
- A interface não impõe o limite silencioso de 3. Gerar somente a seleção explícita, exibindo seu tamanho. Se existir limite técnico de lote, mostrá-lo antes de iniciar e dividir em lotes preservando a escolha.
- Resultado parcial aparece conforme janelas forem validadas. Receber um resumo não adiciona um tema/proposta validada. Na primeira versão, geração é habilitada somente após análise completa.
- Sem histórico de tentativas antigas ou seletor de trabalhos; apenas resultado/processo atual e seus estados. Logs técnicos continuam internos.

## Etapas distintas

**Importar → Transcrever → Analisar → Escolher trechos → Gerar prévias → Revisar → Exportar.**

Importação, transcrição e análise continuam automáticas. Escolha/geração são ações do usuário; revisão é uma decisão humana. Exportar exige prévias aprovadas para a revisão atual. A aplicação não deve mostrar Aguardando o motor quando está aguardando o usuário.

A sidebar mostra a etapa atual e a próxima ação. Itens concluídos podem ficar compactos; detalhes da etapa atual ficam visíveis. Não é necessário manter sete cards grandes ou criar uma aba para cada processo.

## Geração observável

Mostrar uma fila por corte: aguardando, preparando edição, verificando pausas, preparando legendas/enquadramento, renderizando, verificando resultado, pronto para revisar ou falhou. Usar apenas etapas realmente implementadas. Não anunciar acompanhamento facial onde o motor só utiliza composição central.

Exemplos de mensagens (valores ilustrativos, não estimativas):

- Analisando janela 4 de 7; 9 propostas recebidas.
- Você selecionou 6 trechos. Gere as prévias para revisá-los.
- Corte 2 de 6: preparando legendas.
- Corte 2 de 6: renderizando 18 de 59 segundos de saída.
- 4 prévias prontas, 1 em processamento, 1 aguardando.
- Corte 3 falhou na verificação; os demais resultados foram preservados.
- Geração concluída. Há 6 prévias aguardando sua revisão.

Durante renderização, progresso pode vir de out_time_us do FFmpeg dividido pela duração real da EDL, limitado ao intervalo válido. O fim da codificação não significa fim da verificação técnica. Sem percentual/ETA inventado em etapas sem medição. Tempo decorrido e atividade real são alternativas melhores.

Cancelamento preserva prévias/checkpoints válidos. Retomar processa apenas itens pendentes/falhos; não repete análise Gemini para renderizar. Uma nova geração não apaga cortes de lotes anteriores nem altera aprovações de revisões que não mudaram.

## Estados, leitura e acessibilidade

- Estados vazios explicam o que falta e apontam a ação: Sem transcrição, Análise em andamento, Nenhuma proposta elegível, Nenhum trecho selecionado, Prévias ainda não geradas.
- Resultados já disponíveis continuam consultáveis enquanto outro item processa. Falha localizada não substitui a tela toda por erro.
- Não trocar a aba nem roubar foco quando um trabalho termina; oferecer ação para ver o resultado.
- Resumos Gemini preservam autoscroll pausável e scrollbar oculta; teclado continua disponível.
- Status acessível via role=status/live region apenas para mudanças relevantes. Não anunciar cada token do modelo. Progresso medido e progresso indeterminado devem ser distintos.
- Preservar posição de leitura, filtro, tema e proposta selecionada durante atualização. Sem reordenar a lista a cada chunk.
- Nenhuma nova dependência de UI é necessária; manter Vue, CSS/tokens e estilo existentes.

## Limites desta melhoria

Sem editor de timeline completo, métricas de viralidade, nova análise paga para categorizar temas, rastreamento facial novo, histórico visível, renderização automática sem escolha ou alteração automática da chave/modelo. A análise existente é suficiente para construir a primeira experiência.

## Referências

- [NN/g: visibilidade do estado](https://www.nngroup.com/articles/visibility-system-status/).
- [NN/g: esperas e interrupções em aplicações complexas](https://www.nngroup.com/articles/designing-for-waits-and-interruptions/).
- [NN/g: divulgação progressiva de complexidade](https://www.nngroup.com/articles/progressive-disclosure/).
- [W3C: status de progresso acessível](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA25).

Aplicação ao projeto: tornar ações/processamento distintos, resultados acessíveis antes da renderização e detalhes técnicos secundários. As referências orientam princípios; o desenho 50/50 e a aba Análise são decisões para este produto.
