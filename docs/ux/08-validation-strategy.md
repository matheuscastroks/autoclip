# 08. Estratégia de Validação, Protocolo de Testes de Usabilidade e Métricas de Sucesso

## 1. Objetivos da Validação

A estratégia de validação tem como propósito mensurar empiricamente o impacto das mudanças de UX/UI no AutoClip, garantindo que o produto atinja seu objetivo central:
> **Permitir que qualquer criador transforme um vídeo longo em cortes publicados sem fricção operacional ou confusão conceitual.**

A validação combina:
1. **Testes de Usabilidade Moderados e Remotos** com usuários representativos das 3 Personas.
2. **Métricas Quantitativas Padronizadas da Indústria (SUS, UMUX-Lite, SEQ, Taxa de Sucesso de Tarefa).**
3. **Inspeção de Acessibilidade Automatizada e Manual com Leitores de Tela.**

---

## 2. Protocolo de Testes de Usabilidade (Cenários e Tarefas)

Os testes devem ser realizados com **5 a 8 participantes** (amostra recomendada por Nielsen para identificar ~85% dos problemas de usabilidade), utilizando o método *Think-Aloud* (Pensar em Voz Alta).

### Tarefa 1: Configuração Inicial e Conexão de API (Persona 1 e 3)
- **Cenário:** O participante acabou de instalar o AutoClip e precisa deixá-lo pronto para o primeiro uso.
- **Instrução dada ao usuário:** *"Abra o aplicativo pela primeira vez e conclua a configuração necessária para começar a gerar cortes."*
- **Critério de Sucesso:** Usuário insere a chave da API do Gemini sem sair do fluxo ou expressar dúvida sobre o custo/segurança da chave.
- **Métrica Alvo:** Conclusão em menos de 90 segundos sem intervenção do moderador.

### Tarefa 2: Importação de Vídeo via YouTube (Persona 1 e 2)
- **Cenário:** O participante deseja produzir cortes a partir de uma palestra específica no YouTube.
- **Instrução dada ao usuário:** *"Crie um novo projeto usando o link do YouTube fornecido e inicie o processamento."*
- **Critério de Sucesso:** Usuário identifica o botão de criação, cola a URL, aguarda a validação da miniatura e confirma o início sem hesitação.
- **Métrica Alvo:** Conclusão em menos de 45 segundos.

### Tarefa 3: Monitoramento e Gestão de Espera (Persona 1, 2 e 3)
- **Cenário:** O vídeo está sendo transcrito localmente via Whisper na CPU.
- **Instrução dada ao usuário:** *"Acompanhe o processamento do vídeo e verifique em qual etapa ele está enquanto você realiza outra atividade."*
- **Critério de Sucesso:** Usuário compreende que o processamento ocorre em sua própria máquina, entende o tempo estimado restante e utiliza a Fila Global ou minimiza o aplicativo com confiança.

### Tarefa 4: Curadoria Editorial e Seleção Sem Sobreposição (Persona 1 e 2)
- **Cenário:** A análise semântica foi concluída e o participante precisa escolher 3 momentos relevantes para virar cortes verticais.
- **Instrução dada ao usuário:** *"Examine as propostas encontradas pela inteligência artificial e selecione 3 cortes com temas diferentes, evitando momentos repetidos."*
- **Critério de Sucesso:** Usuário ouve o áudio das propostas, lê o gancho inicial e a nota explicativa da IA, compreende a trava de sobreposição (*no-overlap*) se tentar selecionar trechos conflitantes e aciona a geração de prévias.
- **Métrica Alvo:** Taxa de Sucesso > 90%; Avaliação SEQ ≥ 6/7.

### Tarefa 5: Revisão do Corte 9:16 e Exportação Final (Persona 1 e 2)
- **Cenário:** As prévias verticais foram geradas e precisam ser validadas antes da postagem.
- **Instrução dada ao usuário:** *"Assista à prévia vertical do primeiro corte, verifique se a legenda está correta e exporte o vídeo pronto para a sua pasta de vídeos."*
- **Critério de Sucesso:** Usuário reproduz o vídeo vertical sem rolagem de tela em 1366×768, ajusta o início/fim se necessário e exporta o arquivo MP4 para o disco.
- **Métrica Alvo:** Tempo na tarefa < 3 minutos.

### Tarefa 6: Recuperação de Interrupção por Cota (Simulação de Erro 429)
- **Cenário:** Durante a análise semântica, a API do Gemini atinge o limite de taxa.
- **Instrução dada ao usuário:** *"O aplicativo encontrou um problema durante a análise. Descubra o que aconteceu e resolva o problema."*
- **Critério de Sucesso:** Usuário lê o banner de alerta amigável, entende que as etapas anteriores estão salvas e utiliza o botão contextual *"Continuar análise restante"* com 1 clique, sem reiniciar o projeto do zero.

---

## 3. Métricas Quantitativas de Avaliação de Usabilidade

| Métrica de Usabilidade | Metodologia de Coleta | Benchmark / Meta Aceitável |
| :--- | :--- | :--- |
| **Taxa de Conclusão de Tarefa (Task Completion Rate)** | Proporção de participantes que completam cada tarefa sem auxílio. | **≥ 85%** em todas as tarefas críticas. |
| **Single Ease Question (SEQ)** | Pergunta única de esforço aplicada imediatamente após cada tarefa: *"O quão fácil ou difícil foi completar esta tarefa?"* (Escala de 1 a 7). | **Média ≥ 5.8 / 7.0**. |
| **System Usability Scale (SUS)** | Questionário padrão de 10 perguntas aplicado ao final da sessão de testes. | **Score ≥ 80 / 100** (Classificação Grau A / Excelente). |
| **UMUX-Lite (Usability Metric for User Experience)** | Avaliação rápida de 2 itens: *"As capacidades do AutoClip atendem às minhas necessidades"* e *"O AutoClip é fácil de usar"*. | **Score ≥ 85 / 100**. |
| **Tempo na Tarefa (Time on Task)** | Duração medida em segundos para as etapas de criação, curadoria e exportação. | Redução de pelo menos **40% no tempo de curadoria** em comparação com a interface legada de 3 colunas. |

---

## 4. Avaliação de Acessibilidade Contínua e Ferramental

1. **Testes de Navegação Exclusiva por Teclado:**
   - Navegação completa por todas as telas do aplicativo utilizando apenas as teclas `Tab`, `Shift+Tab`, `Enter`, `Espaço`, `Esc` e setas direcionais.
   - Verificação de anel de foco visível em 100% dos elementos interativos.
2. **Inspeção com Leitor de Tela:**
   - Teste no Windows com **NVDA** e **Narrador do Windows**.
   - Garantir que anúncios de mudanças de estado (término de download, conclusão de transcrição) sejam lidos através de regiões `aria-live="polite"` sem truncar a fala corrente.
3. **Verificação de Contraste e Escala de Resolução:**
   - Auditoria automatizada via script CDP e extensões Axe-Core em resoluções 1366×768, 1920×1080 e 2560×1440.

---

## 5. Canal de Feedback Construtivo Integrado (Privacy-First)

Como o AutoClip é uma ferramenta estritamente *local-first*, não utilizamos telemetria invasiva ou envio de dados privados para servidores externos. Para capturar o feedback dos usuários reais em produção:
- Adicionar um botão discreto no rodapé das Configurações: *"Enviar sugestão ou relatar problema"*.
- O botão abre um diálogo local simples que permite ao usuário exportar um relatório de diagnóstico sem identificadores pessoais ou credenciais (apenas versão do app, modelo de GPU/CPU e mensagens de erro do sistema) para inclusão em uma Issue no GitHub ou formulário anônimo.
