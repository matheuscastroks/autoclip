# Títulos e abertura para redes sociais

O Gemini sugere dois textos distintos para cada corte: um título de publicação simples e direto (até 80 caracteres) e uma frase de abertura relacionada ao argumento do trecho (até 72 caracteres). O prompt pede linguagem cotidiana e interesse sem inventar fatos, remover ressalvas ou prometer algo que o corte não explica.

A abertura aparece no alto do vídeo durante os primeiros 7 segundos, limitada à duração do corte. O contrato de configuração aceita de 5 a 10 segundos. Ela usa a fonte das legendas, maiúsculas, branco e contorno preto. As legendas da fala continuam na parte inferior com destaque amarelo da palavra atual. A abertura é texto editorial, separado da transcrição e do SRT; consta no ASS e nos metadados de exportação.

A análise apresenta a frase antes da geração. A revisão apresenta o texto efetivamente renderizado e sua duração. Estes campos são informativos; esta entrega não inclui um editor de abertura na interface.

Projetos existentes preservam a identidade da análise e as seleções quando não possuem o novo campo. Em novas gerações com análises antigas, um título completo de até 100 caracteres pode servir de abertura. Títulos maiores não são truncados: uma nova análise pode produzir uma frase própria. Prévias já renderizadas não são alteradas automaticamente.

## Validação em 12/10/2026

- Suíte Python completa anterior aos ajustes finais: 141 passaram, 1 teste de provedor opcional ignorado.
- Suíte unitária final: 81 passaram; interface final: 48 passaram.
- Resposta Gemini simulada verifica propagação da frase sem alterar limites por palavra.
- Testes verificam tempo da abertura, separação do SRT, neutralização de comandos ASS e fallback para título quando a frase está vazia.
- Hash de uma análise real salva e sua seleção foram comparados antes/depois da leitura com o contrato atualizado e preservados.
- Amostra técnica local de 8 segundos renderizada e verificada, com abertura escolhida manualmente: `poc-results/frontend/social-opening-validation.json`. Quadros aos 1 e 7,5 segundos demonstram aparecimento e remoção da abertura. A amostra não valida a seleção editorial de um corte completo.
- Nenhuma chamada real ao Gemini nesta entrega. A qualidade editorial das novas sugestões precisa ser avaliada na próxima análise real.

Uma renderização existente foi detectada em andamento. O serviço não foi reiniciado para interrompê-la; as alterações de API exigem recarregamento do serviço após sua conclusão.
