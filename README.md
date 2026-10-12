# AutoClip Editor — investigação e definição técnica

Aplicação proposta: desktop open source, local-first, para cortes informativos em português brasileiro. Esta entrega contém pesquisa e especificações; não contém a aplicação desktop nem uma PoC de produto validada.

## Documentos

1. [Comparativo dos candidatos](docs/01-investigacao.md): commits, licenças, capacidades, manutenção e matriz de decisão.
2. [Recomendação técnica](docs/02-recomendacao.md): alternativas e decisões condicionais.
3. [PRD](docs/03-prd.md): requisitos, fluxos, prioridades e critérios de aceite.
4. [Arquitetura](docs/04-arquitetura.md): separação dos componentes, retomada e execução local.
5. [Dados e contratos](docs/05-dados-contratos.md): entidades, unidades, invariantes e contratos v1.
6. [Roadmap](docs/06-roadmap.md): etapas com dependências e gates.
7. [Plano de testes e benchmark](docs/07-testes-benchmark.md): vídeo comum, protocolo e rubrica editorial.
8. [Estado de validação](docs/08-validacao.md): verificações executadas e pendências para a PoC.
9. [Configuração Gemini](docs/09-gemini.md): análise por API escolhida pelo usuário, com mídia processada localmente.
10. [Plano detalhado da PoC](docs/superpowers/plans/2026-10-12-poc-openshorts-gemini.md): tarefas, interfaces, testes e aceite para implementação.

## Evidências reproduzíveis

`research/snapshots/*/evidence.json` registra metadados GitHub, commit e consultas de releases/CI. `research/inventory.json` descreve o inventário, sem representar cobertura executada. Snapshots de código, dependências de pesquisa e vídeo ficam ignorados pelo Git; não redistribuir o vídeo junto ao projeto.

Vídeo indicado pelo usuário: [É preciso dialogar com a frustração e raiva das pessoas — Jones Manoel](https://www.youtube.com/watch?v=z0cf-eWBVCo). A importação utiliza uma cópia local comum, identificada por SHA-256. Fonte pública não equivale a licença de redistribuição; este material serve apenas à avaliação local solicitada.

Scripts em `research/` são instrumentos de investigação dos candidatos. Não são implementação do motor proposto. Nenhum serviço de publicação ou interface desktop foi criado.

## Próximo gate

A arquitetura OpenShorts + Gemini foi aprovada pelo usuário em 12/10/2026. O plano detalhado da PoC está preparado para revisão e escolha do método de execução; a implementação ainda não começou. O usuário informou que seu notebook não comporta LLM local e escolheu análise pela API Gemini; transcrição, edição e renderização permanecem locais. O comparativo de qualidade semântica só pode ser concluído com seleção e revisão de cortes reais, usando o protocolo documentado.
