# Fluxo automático e gerenciamento — 12/10/2026

## Comportamento

- Novos vídeos usam um worker independente para importar, transcrever e analisar em sequência. O formulário registra autorização de envio de texto, modelo e limite de chamadas; renderização permanece explícita.
- Cancelamento/falha interrompem a sequência. Retomada de análise/preparação exige um novo orçamento confirmado; etapas locais preservam seu fluxo de retomada.
- Sidebar por etapa com barras de atividade, estados, erros, cancelamento e retomada. Sem percentuais especulativos. Vídeo/transcrição carregam quando surgem, inclusive se a análise terminar com falha.
- Capas reais extraídas por FFmpeg, cache por hash do original, fallback quando a imagem não está disponível.
- Projetos excluídos ficam ocultos no registro, sem remover arquivos e sem reaparecer pela descoberta automática. Cortes têm marca de exclusão com metadados de restauração e continuam restauráveis após nova análise. Cortes excluídos são ignorados pelas novas exportações; pacotes anteriores permanecem preservados.

## Evidência

- Resultado final: 94 testes Python passaram e 1 teste de geração real foi ignorado; 18 testes Vue passaram; TypeScript e Vite compilaram. Servidor final aberto no navegador, com um worker de transcrição preservado.

- Testes observaram RED antes de implementação: encadeamento, interrupção na transcrição, autorização, lixeira, bloqueio de exclusão com tarefa ativa, capas, sidebar e atualização intermediária de mídia.
- Revisão independente encontrou e corrigiu, com regressões: restauração de cortes após nova análise, disponibilidade de artefatos durante processamento e animação após cancelamento forçado.
- Inspeção real: capas carregadas na biblioteca; vídeo original e barra de transcrição visíveis na sidebar em 1366×768; nenhuma atividade abaixo do vídeo. O worker de transcrição existente permaneceu com mesmo PID/data de criação após atualizar o servidor.
- Nenhum trabalho de análise Gemini foi iniciado pelo agente nesta entrega; testes usam fixtures. A seleção semântica real permanece pendente de execução e revisão editorial.
- Uma execução de teste encontrou WinError 5 em `os.replace`; teste isolado passou e a suíte posterior passou. Resultado final automatizado no XML da suíte Python.
