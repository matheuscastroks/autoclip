# Publicação sem revisão manual

A solicitação do usuário substitui a etapa de aprovação editorial por título, descrição e download direto do corte. Não são gerados registros fictícios de aprovação.

- Cortes completos e tecnicamente válidos ficam disponíveis para download sem `review.json`.
- O download usa o ticket local existente e retorna MP4 como anexo. Confere a validação técnica, identidade da revisão e checksum do render.
- Arquivos incompletos, corrompidos ou na lixeira não podem ser baixados.
- Exportação em lote também não exige aprovação editorial; preserva metadados e legendas editáveis.
- A descrição gerada deve usar um parágrafo curto e 3–5 hashtags temáticas no final. A normalização local remove hashtags do meio do texto e elimina duplicações; descrições antigas sem tags recebem uma dupla genérica, sem inventar o tema.
- Os registros históricos de revisão são preservados nos projetos, mas não bloqueiam o novo fluxo.

Validação: teste do pipeline com vídeo sintético confirmou exportação sem revisão e rejeição de render corrompido. Testes da interface conferem download do corte selecionado e ausência de aprovação.
