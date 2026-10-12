# AutoClip Editor — investigação e definição técnica

Projeto desktop open source, local-first, para cortes informativos em português brasileiro. A pesquisa, especificações, PoC do motor e primeira interface Vue de gerenciamento estão implementadas. O launcher Windows abre por duplo clique, sem terminal; encapsulamento Tauri/instalador continua no roadmap. Aprovação editorial dos cortes reais permanece humana.

## Usar no notebook

Abra **AutoClip.lnk** ou **Abrir AutoClip.vbs** nesta pasta. Biblioteca, importação, configurações, transcrição, tarefas e revisão são administradas pela interface local. [Guia da interface](docs/frontend-runbook.md). O vídeo já transcrito mantém seus artefatos; esta etapa não fez chamadas reais Gemini.

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
11. [Executar e revisar a PoC](docs/poc-runbook.md): instalação, credencial local, retomada, revisão e exportação.
12. [Registro de execução e decisões](docs/poc-progress.md): testes, revisão independente e limites observados.
13. [Interface e launcher](docs/frontend-runbook.md) e [validação do frontend](docs/frontend-progress.md).

## Evidências reproduzíveis

`research/snapshots/*/evidence.json` registra metadados GitHub, commit e consultas de releases/CI. `research/inventory.json` descreve o inventário, sem representar cobertura executada. Snapshots de código, dependências de pesquisa e vídeo ficam ignorados pelo Git; não redistribuir o vídeo junto ao projeto.

Vídeo indicado pelo usuário: [É preciso dialogar com a frustração e raiva das pessoas — Jones Manoel](https://www.youtube.com/watch?v=z0cf-eWBVCo). A importação utiliza uma cópia local comum, identificada por SHA-256. Fonte pública não equivale a licença de redistribuição; este material serve apenas à avaliação local solicitada.

Scripts em `research/` são instrumentos de investigação dos candidatos. Não são implementação do motor proposto. Nenhum serviço de publicação ou interface desktop foi criado.

## Próximo gate

A arquitetura e o plano OpenShorts + Gemini foram aprovados e implementados. Transcrição, edição e renderização permanecem locais. O vídeo integral produziu 5.414 palavras em CPU; o teste remoto usa Gemini 2.5 Flash, somente texto, com até 20 tentativas autorizadas. Consulte o estado de validação para o resultado atual. O comparativo editorial dos cinco projetos ainda exige a rubrica humana documentada.
