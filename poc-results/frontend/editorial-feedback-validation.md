# Duração, pausas e feedback Gemini — 12/10/2026

## Implementado

- Configuração de preferência e máximo de duração, até 180 segundos, refletida no prompt, seleção, EDL, cache e snapshots de trabalhos. O máximo não provoca aparo de palavras; a preferência não força encerrar raciocínio. Mínimo técnico de 20 segundos na seleção original; após reduzir pausas, a exportação pode ficar mais curta.
- Pausas: Silero VAD local e pico de áudio baixo, intersectados com espaços entre palavras. Intervalos silenciosos longos são encurtados com margens; ausência de confirmação mantém áudio contínuo. Verificação vinculada à fonte/áudio, assets VAD incluídos no cache. Fonte intacta, EDL com intervalos removidos, legendas remapeadas e pontos de junção acessíveis na revisão.
- Gemini: streaming dos resumos oficiais `thought`, separados do JSON final. Capacidade consultada em `models.get().thinking`; JSON só publicado após validar schema, IDs e ordem de fronteiras. Resumos são parciais até concluir a análise, nunca aprovação editorial.
- Eventos locais por janela/tentativa, falhas/retries, temas e justificativas validados, tokens quando informados. Histórico paginado, conteúdo mostrado como texto, sem HTML executável. Resumos de tentativas anteriores não aparecem como novos. Resumos ausentes/desativados e cache reaproveitado têm mensagens explícitas.
- Timeout de consulta de capacidade: 5 segundos, uma tentativa; geração com timeout/cancelamento de processo. Retry de timeout entra no orçamento, cancelamento não dispara retry. Requisições de workers antigos sem a nova flag mantêm sua política anterior de pensamento.

## Evidência

- Testes RED → GREEN: argumento de quase 2 minutos, proteção de palavras/áudio e remapeamento de legendas, resumos separados do JSON e segredo redigido, JSONL parcial, configurações e histórico paginado, UI segura, isolamento entre tentativas, feedback parcial no cancelamento e déficit de orçamento.
- Renderização FFmpeg real de dois spans: H.264 vertical, áudio AAC, legendas, duração e decodificação passaram QA. Modelo Silero empacotado verificou PCM quieto localmente, sem download.
- Revisão independente não encontrou perda comprovada de palavras ou erro de remapeamento. Encontrou timeout de processo fora do retry; corrigido com regressão específica.
- Consulta real de metadados confirmou `gemini-2.5-flash` com `thinking=true`. Nenhum conteúdo foi gerado pelo agente. Streaming/resumos e JSON foram verificados com respostas simuladas; seleção semântica real segue pendente de execução/revisão do usuário.
- Suíte final: 106 testes do motor/API passaram, 1 teste de geração real ignorado; 25 testes Vue passaram; TypeScript/Vite compilaram.
- Inspeção visual encontrou etapas pendentes herdando erro terminal da análise. Corrigido com regressão: importação e transcrição concluídas permanecem concluídas; geração ainda não iniciada permanece na fila.
- Interface atualizada aberta no navegador; valores observados: preferência 60s, máximo 180s, redução conservadora e resumos ativados. Limite de chamadas do usuário preservado, sem iniciar novos trabalhos ou alterar esse limite.

## Referências

[Resumos oficiais e streaming Gemini](https://ai.google.dev/gemini-api/docs/generate-content/thinking#thought-summaries) e [JSON estruturado](https://ai.google.dev/gemini-api/docs/structured-output). Uso do SDK `google-genai` já instalado; sem migração obrigatória de provedor nem novas dependências de serviços pagos.
