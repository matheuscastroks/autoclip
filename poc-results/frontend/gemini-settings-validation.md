# Configuração dinâmica Gemini — 12/10/2026

- API: valida a chave candidata antes de substituir a credencial. Respostas do provedor são sanitizadas; catálogo em memória vinculado à credencial ativa.
- Interface: salvar e validar, estados de conexão, horário do teste, atualização explícita e seleção pelos IDs reais do catálogo. Modelo ausente exige escolha explícita.
- Automação: 84 testes Python passaram e 1 de geração real foi ignorado; 14 testes Vue passaram; TypeScript e Vite compilaram.
- Consulta real autorizada: somente `models.list`; credencial válida, 45 modelos para geração, `gemini-2.5-flash` presente. Nenhum conteúdo foi gerado.
- A instância aberta estava transcrevendo. Reinício retornou HTTP 409; tarefa preservada. Validação visual da versão nova na instância aberta permanece pendente. Após terminar a tarefa, encerre o serviço pela interface e reabra pelo atalho para carregar o backend atualizado.
