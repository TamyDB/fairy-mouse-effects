# Análise de requisitos e arquitetura

Este documento preserva os requisitos e as metas iniciais. O estado vigente está em [contexto atual](../.claude/contexto.md); metas de desempenho não são resultados medidos.

## Escopo do MVP
| ID | Requisito | Critério de aceitação |
| --- | --- | --- |
| RF01 | Rastro durante movimento | Partículas acompanham o cursor real e desaparecem sem deixar resíduos. |
| RF02 | Brilho no clique esquerdo | Efeito aparece no ponto correto e o aplicativo subjacente recebe o clique normalmente. |
| RF03 | Sobreposição transparente | Não rouba foco, não impede arraste, rolagem ou atalhos do Sway. |
| RF04 | Configuração simples | Permite ativar/desativar efeitos e ajustar cor, intensidade e limite de FPS. |
| RF05 | Ciclo de vida | Inicia e encerra sem processos ou temporizadores órfãos; falhas de dependência têm mensagens claras. |
| RF06 | Geometria | Usa dimensões reais; trata escala e mudança de monitor, sem coordenadas fixas. |

Ficam fora do MVP: editor visual, áudio, efeitos complexos, integração com nuvem e suporte universal a compositores.

## Metas iniciais de desempenho
São propostas para medição, não resultados ou garantias: 30 FPS máximos, até 48 partículas vivas, duração de 250–600 ms e brilho de 150–250 ms. Nenhum redesenho periódico quando não houver partículas. Usar tempo monotônico, emissão limitada por distância/tempo e estruturas com tamanho limitado.

Metas provisórias: RSS até 80 MiB e CPU média abaixo de 3% de um núcleo em movimento contínuo. Comparar também consumo total do compositor; uma janela transparente grande pode aumentar trabalho gráfico mesmo com poucas partículas. Revisar limites após escolher hardware de referência e registrar resolução, escala, CPU e GPU.

## Viabilidade no Wayland
O protocolo `wl_pointer` entrega eventos associados à superfície com foco e coordenadas locais. Uma sobreposição com região de entrada vazia permite passagem de eventos, mas não ganha observação global do ponteiro por isso. O layer-shell resolve posicionamento e camada; não é uma API de rastreamento global.

A documentação IPC consultada do Sway não oferece um fluxo genérico de movimento global do cursor. Validar recursos da versão instalada antes de escolher integração. Eventos evdev permitem observar dispositivos com permissão apropriada, mas deltas brutos não reproduzem automaticamente aceleração, transformações e limites aplicados pelo compositor. Não aceitar deriva como implementação final.

A decisão posterior do usuário foi manter o Sway padrão. A implementação atual usa metadados EXT para posição e observação restrita de botão físico para clique. Não retomar proposta de patch no compositor como se ainda fosse o caminho escolhido. Um efeito em posição fixa não satisfaz RF01/RF02.

## Arquitetura e implementação
Separar fonte de eventos (`input`), simulação independente de GUI (`particles`), renderização (`overlay`) e configuração (`config`). A fonte deve fornecer posição lógica, instante e botão; o renderer converte coordenadas para cada saída. Uma superfície por saída, região de entrada vazia, teclado sem foco e zona exclusiva -1 (cobrir a saída inteira, inclusive áreas de painéis). Validar transparência real e comportamento em fullscreen.

A implementação utiliza Python + GTK 4 + Gtk4LayerShell + Cairo; detalhes e módulos estão em INTEGRACAO.md. Não presumir menor consumo por linguagem: medir a aplicação e o compositor. Evitar threads extras, blur em tempo real e recursos gráficos externos enquanto formas simples forem suficientes.

## Validação antes da entrega
1. Provar rastreamento: atravessar bordas, mover lentamente/rapidamente, alterar aceleração, testar mouse e touchpad, escalas e saídas disponíveis.
2. Provar passagem de entrada: clicar, selecionar texto, arrastar e alternar janelas sob a sobreposição.
3. Testar simulação com relógio controlado: expiração, limites, remoção e rajadas de cliques.
4. Medir 60 segundos em repouso, movimento e cliques; registrar RSS, CPU e efeitos no compositor, comparando com a aplicação desligada.
5. Testar desconexão de dispositivo/monitor e encerramento durante animação.

## Fontes técnicas
Consultadas em 2026-10-27; conferir novamente ao implementar contra a versão instalada.
- [Wayland: especificação de wl_pointer e wl_surface](https://wayland.freedesktop.org/docs/html/apa.html).
- [Protocolo wlr-layer-shell](https://github.com/swaywm/wlr-protocols/blob/master/unstable/wlr-layer-shell-unstable-v1.xml).
- [API Gtk4LayerShell](https://wmww.github.io/gtk4-layer-shell/gtk4-layer-shell-GTK4-Layer-Shell.html).
- [Documentação IPC do Sway](https://github.com/swaywm/sway/blob/master/sway/sway-ipc.7.scd).

## Operação em segundo plano
Requisito confirmado pelo usuário: a aplicação final roda em segundo plano na sessão gráfica, sem janela principal. A sobreposição visual deve continuar sem foco e com passagem de cliques. `--demo` não representa a interface operacional final.

Critérios de aceitação adicionais:
- Iniciar manualmente em modo de segundo plano sem abrir janela de controle ou exigir terminal interativo.
- Oferecer inicialização automática opcional junto à sessão Sway, com instruções para desativar.
- Impedir instâncias duplicadas e oferecer uma forma documentada de parar o processo.
- Encerrar corretamente com SIGTERM e ao perder a sessão gráfica, liberando temporizadores e superfícies.
- Manter animação suspensa quando não houver efeitos e emitir diagnóstico útil em falhas de inicialização.

Foi implementada integração via systemd de usuário, com instalação que prepara a unidade desabilitada. O usuário habilitou o início automático posteriormente. Nova sessão/reboot continua sem validação confirmada. Bandeja e painel de configuração não são requisitos neste momento.
