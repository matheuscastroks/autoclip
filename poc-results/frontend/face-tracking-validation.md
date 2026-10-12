# Validação do acompanhamento facial

MediaPipe 0.10.33 / BlazeFace short-range float16 v1, delegado CPU. Modelo e licença Apache 2.0 incluídos no pacote.

- Trecho real local de 3,36 s: 7/7 amostras detectadas; centro horizontal normalizado de 0,5102 a 0,5211.
- Render 1080×1920 a 30 fps: QA técnico aprovado; legenda Montserrat ExtraBold mantida.
- Teste de pixels: trajetória sintética esquerda → direita percorre as faixas vermelha e azul, sem blur; recorte central continua válido.
- Suavização, perda/reaquisição, escolha por proximidade, limite de movimento, spans curtos, origem temporal e cancelamento cobertos.
- Suite completa: 130 aprovados e 1 teste real de provedor ignorado; depois dos ajustes temporais, 8 testes focados aprovados. Vue: 39 aprovados; build concluído. Revisão independente sem problemas importantes restantes.
- Nenhuma chamada ao Gemini. O exemplo curto não valida todos os cortes nem situações com múltiplos participantes; revisão visual permanece necessária.

Evidência estruturada em `face-tracking-validation.json` e quadro em `face-tracking-frame.jpg`.
