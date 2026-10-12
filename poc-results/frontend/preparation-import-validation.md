# Recuperação de importação e visão geral

Causa observada nos logs reais: YouTube retornou HTTP429 e confirmação de acesso (“not a bot”) em três importações do vídeo z0cf-eWBVCo. O worker ocultava a causa em SOURCE_UNAVAILABLE. A biblioteca ignorava a tarefa quando não havia source.json; a miniatura afirmava importação ativa e o painel de preparação não oferecia retry sem transcrição.

Mudanças: erros específicos sanitizados, compatibilidade com falhas antigas, estado derivado da última tarefa, retry com fonte original ou arquivo local, publicação da fonte após probe, vídeo compacto no cabeçalho e sete etapas divididas em dois grupos.

Validação: 47 testes API/importação, 5 testes de fonte/probe e 40 testes Vue passaram; build concluído. A revisão independente não encontrou problemas importantes. O cancelamento do seletor teve sua falsa mensagem de sucesso corrigida.

Inspeção visual em sessão isolada: botões de retry e arquivo local habilitados após carregamento; desktop com sete etapas e miniatura à direita; tela de 390px sem overflow horizontal (scrollWidth375) e sete etapas presentes. Capturas: preparation-import-recovery.png e preparation-import-mobile.png. A fonte real local foi usada como referência visual; o projeto bloqueado foi uma fixture explicitamente identificada. Não foi realizado novo download remoto ou chamada Gemini para esta validação.

A sessão principal mantém uma geração de 11 cortes ativa; não foi encerrada nem reiniciada. O serviço principal precisa recarregar o backend após a tarefa terminar para aplicar as novas rotas e projeção de status.

Referência: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#http-error-429-too-many-requests-or-402-payment-required
