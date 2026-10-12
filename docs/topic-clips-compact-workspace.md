# Cortes por tópico e espaço de revisão

Cabeçalho do projeto em uma linha, com voltar acessível, título truncável, canal, duração e estado. A revisão permite scroll da página. A sidebar de renderização contém somente pendências e falhas; desaparece quando não existe trabalho pendente. Cortes prontos permanecem na aba Cortes.

Novas análises iniciadas pela API ou CLI usam mínimo de 60 segundos, preferência de 180 e máximo de 300. O prompt pede tópicos completos e até dez propostas relevantes. A consolidação técnica valida duração, integridade declarada, sobreposição e repetição de rótulos. A transcrição inteira continua sendo coberta mesmo se nenhuma proposta for aproveitável. O limite é global ao vídeo, não por janela. As janelas usam sobreposição de até cinco minutos para reduzir cortes de argumentos entre solicitações; limites de texto ainda podem impedir uma proposta longa, que deve ser descartada em vez de truncada.

A política mínima é armazenada no artefato de análise. Artefatos antigos mantêm o mínimo de 20 segundos e a serialização anterior, preservando hashes de seleção. A configuração salva migra uma vez para a política de 1–5 minutos. Novas regras não editam arquivos renderizados nem iniciam chamadas ao Gemini automaticamente neste ajuste.

Se a remoção de pausas reduzir o trecho abaixo do mínimo, as pausas são preservadas. Completude semântica ainda exige revisão humana; flags e duração não provam preservação de sentido. A deduplicação por rótulo normalizado não identifica todas as equivalências semânticas.
