# Select exclusivo do aplicativo

AppSelect.vue substitui os controles visíveis nativos de estado, ordenação, modelo Gemini e pausas. Usa os primitives do Reka UI com apresentação própria: borda de 2 px, sombra dura, pressão de 3 px, fundo lavanda ao abrir, seleção marcada e navegação destacada em roxo. A lista usa portal, largura do controle, largura mínima de 220 px e posicionamento que respeita as bordas da tela.

Mantém valores exatos, opções desabilitadas, foco e navegação por teclado. Textos longos podem quebrar no menu; o controle fechado usa reticências. Catálogos longos têm rolagem e controles de acesso às opções anteriores/próximas. Reka pode manter um select oculto para integração de formulário; nenhum menu nativo é exposto ao usuário.

Validação em 12/10/2026: 54 testes Vue aprovados, mais 9 testes de feedback reexecutados após refinar a integração de pausas; build TypeScript/Vite aprovado. Testes exercitam abertura por seta, seleção por Enter, opções desabilitadas e preservação de IDs Gemini. No navegador, catálogo real de 45 modelos abriu com rolagem; End alcançou a última opção e Escape devolveu foco ao controle sem alterar o modelo salvo. Foi feita consulta de catálogo, sem geração de conteúdo nem análise de transcrição.

Evidência: poc-results/frontend/brutalist-select.png. Os primitives foram consultados em https://reka-ui.com/docs/components/select e https://www.shadcn-vue.com/docs/components/select. O app conserva seu próprio CSS e não exige Tailwind ou migração para shadcn.
