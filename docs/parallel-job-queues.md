# Filas persistentes e concorrência local

Implementação autorizada pelo pedido de melhorar as filas; executar no projeto atual.

- SQLite mantém jobs pendentes, em execução e resultados. O despacho ocorre no motor, independentemente da tela aberta.
- Limite inicial: duas tarefas simultâneas, em projetos distintos; no máximo um job de análise por vez e um lock cancelável entre processos para serializar as chamadas ao provedor, inclusive durante a preparação automática. Uma tarefa ativa por projeto protege seus artefatos.
- Jobs pendentes sobrevivem ao reinício; jobs que estavam executando e perderam o processo ficam interrompidos, com retomada explícita.
- Cancelamento de pendência remove a entrada sem criar processo. Falha de um job libera capacidade para os outros.
- Geração filtra candidatos já prontos com receita compatível e candidatos já presentes em jobs ativos com a mesma análise/receita. Retornar contagens de ignorados e enfileirar somente o restante.
- Interface permanece navegável entre projetos e mostra estado, posição e motivo de espera. Não redesenhar as telas nesta etapa.
- Validar concorrência, ordem por projeto, limites, deduplicação, reinício, cancelamento e isolamento de falhas com workers simulados. Não iniciar chamadas reais à IA para testes.

## Validação e ativação

- Suíte de API: 66 testes aprovados; verificações adicionais de retomada, streaming e lock do provedor também passaram.
- Suíte completa da interface: 74 testes aprovados; após refinamento da prioridade visual, 16 testes direcionados passaram, incluindo um novo caso para execução versus espera.
- Build Vue/TypeScript concluído.
- Testes usam processos simulados e não chamam o Gemini.
- Motor atualizado e sessão autenticada aberta após confirmar ausência de tarefas ativas; health local retornou `ok` e 49 registros de jobs foram preservados.
- Despacho automático ocorre a cada 500ms e consulta apenas jobs ativos, sem reprocessar todo o histórico de resultados a cada ciclo.
- Jobs antigos sem receita explícita só são deduplicados quando configuração e datas dos arquivos de implementação comprovam compatibilidade. Arquivos prontos são conferidos por checksum antes de serem ignorados.
