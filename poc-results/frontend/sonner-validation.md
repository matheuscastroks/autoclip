# Validação dos avisos globais

Vue Sonner 2.0.9, MIT. Único host top-center, largura desktop420px, erros9s/avisos7s/sucesso4,5s, até3visíveis. Usa os tokens do app, ícones semânticos, fechamento e Alt+T.

47 testes Vue passaram; depois do ajuste do atalho e largura do host, os7testes focados passaram e o build concluiu. A revisão independente encontrou o modificador incorreto do atalho; foi corrigido para altKey/KeyT e verificado por foco real no jsdom.

Inspeção visual com erros controlados, mutações bloqueadas e nenhuma chamada Gemini/download: um host, posição central no topo, nenhum banner `.notice`. Em janela nativa aberta, host contido no dialog, toastTop20px, largura420px em viewport615px, sem overflowhorizontal. Capturas em sonner-top-center.png e sonner-native-dialog.png. A mensagem começa com “Teste visual” para distinguir a fixture de uma falha real.

A sessão principal foi preservada durante a validação. Toasts são frontend; abrir novamente a interface autenticada carrega o novo build sem cancelar o worker. Mudanças de backend do commit anterior ainda exigem reinício do serviço depois da geração ativa.
