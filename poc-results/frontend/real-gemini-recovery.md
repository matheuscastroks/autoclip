# Validação real da recuperação Gemini — 12/10/2026

Projeto: **O que é corrupção?**, Jones Manoel, 34:57. Modelo: **gemini-2.5-flash**. Somente texto da transcrição; vídeo e áudio não foram enviados.

## Resultado

- Análise concluída: **7/7 janelas**, cobertura de **5.556/5.556 palavras**.
- **19 propostas** registradas; propostas não são aprovação editorial.
- **11 de 28 tentativas autorizadas**, contadas incluindo diagnósticos, retries e reparação.
- Execução concluída utilizou **9 solicitações**, incluindo **2 reparações de JSON**; as 2 solicitações anteriores diagnosticaram truncamento.
- **7 checkpoints** puderam ser reutilizados em uma execução local com função de chamada remota proibida: **0 chamadas novas**. Testes automatizados também cobrem interrupção parcial, retomada com orçamento novo, invalidação por modelo e corrupção.
- Seleção existente continua limitada a 3 candidatos. Os três planos passaram pelo motor sem truncar a fala, com duração de **51,46 s**, **59,34 s** e **100,06 s**. Isso não é revisão humana de coerência ou aprovação de publicação.
- Nenhuma prévia/MP4 foi renderizada; a geração permanece manual. Interface inspecionada: Analisado/Concluído, sem erro antigo, botão Gerar prévias habilitado.

## Causas e correções

O timeout original de 60 segundos encerrava chamadas antes do JSON final. O motor foi atualizado para 180 segundos com cancelamento e política de pensamento finita. O primeiro teste após essa correção revelou MAX_TOKENS, não timeout. A segunda chamada forneceu telemetria: **1.593 tokens de pensamento**, **14.770 tokens de saída** e **19.319 caracteres de JSON parcial**. Nenhuma resposta truncada foi aceita.

O schema permitia listas de evidência e contexto sem tamanho máximo. A resposta compacta usa até 8 IDs por lista e justificativas curtas; o prompt esclarece que start/end definem todo o intervalo de fala e o motor preserva automaticamente cada palavra interna. A primeira janela passou em cerca de **30 segundos**, usando **2.663 tokens de saída**.

Cada janela recebe também a transcrição completa como contexto global. O limite arbitrário de três propostas por janela foi removido do prompt; a seleção final preserva sua configuração existente. Telemetria de truncamento guarda contagens, não JSON parcial. Avisos de falhas anteriores são ocultados quando uma tarefa atual existe; logs técnicos anteriores são preservados internamente.

## Verificação

- **115 testes Python passaram**, 1 teste de geração opt-in ignorado na suíte; a validação real foi executada separadamente com autorização expressa.
- **32 testes Vue passaram**, incluindo aviso antigo durante execução/conclusão.
- TypeScript e Vite build passaram.
- Revisão independente não encontrou defeitos materiais nas correções adicionais. maxItems é suportado pelo SDK; limites de tamanho de strings são também conferidos localmente e solicitados no prompt.

Referências oficiais: [pensamento e orçamento](https://ai.google.dev/gemini-api/docs/generate-content/thinking#thinking-budgets), [saída estruturada e maxItems](https://ai.google.dev/gemini-api/docs/structured-output#json-schema-support).

Evidência estruturada: real-gemini-recovery.json. Credencial e token de sessão não aparecem nos relatórios.
