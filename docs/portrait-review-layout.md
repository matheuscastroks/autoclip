# Player vertical e sessão na sidebar — 12/10/2026

A revisão apresenta lista de cortes, player com largura intrínseca 9:16 e coluna de informações. Título, texto de publicação, justificativa, original e revisão editorial ficam à direita do player. A fila de geração permanece na sidebar direita do workspace.

A moldura usa borda preta e sombra dura. O player usa object-fit: cover; não reserva uma coluna horizontal para barras laterais. Nenhum arquivo MP4 foi alterado.

A barra superior foi retirada. Contexto da tela, sessão/conexão e botão Atualizar projetos foram movidos para a parte inferior da sidebar, acima de Motor local. O controle de atualização continua usando o fluxo existente.

Validação no navegador em 1366×768: vídeo 213,75×380 px (razão 0,5625); moldura 216,95 px de largura, incluindo bordas; informação começa à direita, em x=656,95 px. Altura total da página 768 px, sem overflow horizontal. Captura: poc-results/frontend/portrait-review-sidebar-session.png.

Testes Vue verificam que título/revisão ficam fora da coluna do player e que atualizar pela sidebar continua consultando os projetos. Build TypeScript/Vite aprovado. A renderização já em andamento foi preservada; não houve reinício do motor ou nova chamada de geração iniciada por esta validação.
