# Integração com o Sway padrão

## Decisão do usuário
Manter o Sway padrão e investigar alternativas, sem patches ou substituição do compositor. A demonstração visual foi aprovada pelo usuário; preservar seu desenho nas próximas etapas.

## Caminho de pesquisa
O Sway local informa versão 1.11. As notas dessa versão incluem suporte a `ext-image-copy-capture-v1` e `ext-image-capture-source-v1`. O primeiro define sessões específicas de cursor com eventos `enter`, `leave`, `position` e `hotspot`. O cliente implementado solicita apenas sessões de metadados do cursor, sem criar buffers ou frames de captura. O diagnóstico já consulta a presença dos gestores necessários no registro Wayland, com limite de tempo, sem criar superfícies ou capturar imagens.

O usuário confirmou via diagnóstico que os dois gestores EXT são anunciados em seu Sway 1.11. O cliente foi testado com servidor simulado e o usuário confirmou o rastro global na sessão real. O evento de posição usa coordenadas de buffer transformado. O cliente usa modo e transformação de `wl_output` para determinar o tamanho físico transformado e converte a posição pelo tamanho lógico da superfície GTK. As coordenadas já chegam transformadas, portanto não se aplica rotação novamente. Validar escala fracionária, rotação e transição entre monitores no desktop real. O protocolo não fornece observação global dos botões. O brilho agora usa leitura opcional e restrita de BTN_LEFT em dispositivos de ponteiro, conforme a seção abaixo, sem acesso exclusivo ou alteração de permissões.

## Sobreposição implementada
`--background` inicia uma aplicação de sessão sem janela de controle. Cada saída identificada pelo GDK recebe uma janela layer-shell transparente: camada overlay, teclado NONE, zona exclusiva -1 (cobrir a saída inteira, inclusive áreas de painéis) e região de entrada vazia. Remontar as superfícies ao adicionar/remover monitores descarta partículas antigas. Alterações de geometria sem adição/remoção e mudanças de escala precisam de validação gráfica.

Um único sistema de partículas compartilha o limite entre todas as saídas. O timer só fica ativo enquanto há efeitos. Posições chegam por uma conexão Wayland dedicada, com leitura bloqueante em thread. Apenas a posição mais recente fica pendente, com entrega ao GTK limitada pelo FPS e sem sondagem periódica. O socket UNIX datagrama privado permanece para eventos sintéticos e controle. Uma trava `flock` impede segunda instância. SIGTERM, SIGINT, fechamento da conexão gráfica e `--stop` solicitam encerramento e limpeza.

## Contrato experimental de eventos v1
Caminho: `$XDG_RUNTIME_DIR/fairy-mouse/events.sock`. Diretório 0700, socket 0600. Cada datagrama contém um objeto JSON de até 1024 bytes:

```json
{"version":1,"type":"motion","output":"eDP-1","x":200,"y":150}
```

`type` aceita `motion` ou `click`; `click` representa pressão do botão esquerdo. `output` é o conector atual do monitor; `x` e `y` são coordenadas lógicas locais à saída. Coordenadas inválidas, fora da superfície ou saídas desconhecidas são descartadas. O instante usado pela simulação é o de recebimento, no relógio monotônico. O produtor deve reduzir a emissão de movimento e evitar filas; este contrato não preserva timestamps de hardware e poderá evoluir.

Para encerramento: `{"version":1,"type":"stop"}`. Não há confirmação de recebimento ou endpoint de status: `--stop` apenas confirma envio. O script `tools/send_event.py` serve para injeção sintética de teste, sem leitura do mouse. O produtor automático de movimento é `CursorClient`, integrado por padrão. `--external-events` o desativa para testes sintéticos. Cliques físicos podem vir do leitor opcional de dispositivos; cliques sintetizados pelo compositor ainda não têm produtor.

## Cliente de metadados
`cursor.py` implementa o subconjunto de mensagens necessário usando socket e estruturas da biblioteca padrão. Inicialização tem limite total de dois segundos. Associa gestores EXT v1, saídas `wl_output` v4 e seats com nome; solicita somente `wl_pointer` no seat escolhido, `seat0` por padrão. Nunca solicita `wl_keyboard`, `wl_shm`, superfícies ou frames de captura. Não precisa compilar componentes nativos ou instalar bindings adicionais.

Uma sessão de cursor é criada por saída nomeada. `enter`/`leave` delimitam validade; posições cujo hotspot esteja fora da saída são descartadas. `hotspot` não desloca a posição recebida, que já representa a ponta do cursor. Mudanças de modo atualizam dimensões; remoção de saída destrói sessão e fonte. Saídas novas recebem novas sessões. A perda do ponteiro selecionado ou do protocolo encerra a aplicação com erro explícito.

O encerramento fecha a conexão dedicada, desbloqueia o leitor e ignora atualizações pendentes. A thread nunca acessa GTK. Não há polling, acúmulo de posições ou gravação de coordenadas em disco. O log informa somente a primeira saída que forneceu posição utilizável, não cada movimento.

## Validação e limites
Testes automatizados cobrem simulação, desenho Cairo sem display, parsing, consulta fragmentada ao registro, negociação de sessões com compositor simulado, transformação/escala, rajadas de posições e bloqueio real de instância com transporte simulado. A sandbox impede criar sockets UNIX, conectar ao display e iniciar o Sway headless. Transporte real, foco, passagem de cliques, mudanças de monitores e aparência do overlay continuam pendentes. A demonstração e, posteriormente, o rastro no overlay foram aprovados pelo usuário em sessão real Sway 1.11. O brilho físico ainda precisa de teste real; os testes locais do leitor usam dispositivos simulados.

## Referências
- [Notas oficiais do Sway](https://github.com/swaywm/sway/releases).
- [Protocolo de captura e metadados do cursor](https://raw.githubusercontent.com/wayland-mirror/wayland-protocols/main/staging/ext-image-copy-capture/ext-image-copy-capture-v1.xml).
- [Fontes de captura](https://raw.githubusercontent.com/wayland-mirror/wayland-protocols/main/staging/ext-image-capture-source/ext-image-capture-source-v1.xml).
- [Região de entrada GDK](https://docs.gtk.org/gdk4/method.Surface.set_input_region.html).
- [Gtk4LayerShell](https://wmww.github.io/gtk4-layer-shell/gtk4-layer-shell-GTK4-Layer-Shell.html).

## Inicialização das bibliotecas gráficas
`gtk_runtime.py` carrega `libgtk4-layer-shell` via ctypes antes de importar GTK/GDK por GI. Essa ordem é necessária porque a biblioteca intercepta chamadas de libwayland; importar GTK primeiro pode inviabilizar a integração mesmo com o protocolo disponível. O modo de segundo plano seleciona explicitamente `GDK_BACKEND=wayland` no próprio processo. Não exige LD_PRELOAD no terminal ou arquivos do usuário.

O diagnóstico informa `layer_shell_preloaded` e `layer_shell_library`. `layer_shell_protocol_version` é o anúncio de `zwlr_layer_shell_v1` no registro: zero indica não anunciado e null indica consulta indisponível. Esses resultados distinguem carga da biblioteca e suporte do compositor. A mensagem de falha funcional inclui o backend efetivamente aberto pelo GDK. Ver [requisito oficial de linking](https://github.com/wmww/gtk4-layer-shell/blob/main/linking.md).


## Clique físico opcional
`clicks.py` usa apenas biblioteca padrão e a ABI de input do kernel Linux (Fedora x86_64/aarch64). Descobre candidatos pelas capacidades em sysfs e confirma capacidades com ioctl antes da leitura. Exige BTN_LEFT e eixos relativos ou absolutos X/Y. Aceita interfaces de mouse que também anunciem teclas extras, pois o filtro obrigatório descarta esses códigos antes da leitura. Teclados comuns sem botão/eixos de ponteiro são excluídos. O Logitech Wireless Mouse desta sessão também anuncia KEY_ENTER; esse detalhe causava exclusão indevida na classificação anterior.

Cada candidato é aberto O_RDONLY|O_NONBLOCK|O_CLOEXEC. EVIOCSMASK restringe os tipos da fila deste descritor e os códigos EV_KEY a BTN_LEFT. Essas máscaras não afetam outros leitores. Não são usados EVIOCGRAB, escrita de eventos, uinput, estimativa de posição ou bindsym. Se a máscara falhar, o leitor é fechado em vez de aceitar leitura sem filtro. Não é exigido pacote Python evdev.

O leitor usa fontes GLib por prontidão de descritor; não cria outra thread ou timer periódico. Pressão física gera um brilho; repetição e liberação não. SYN_DROPPED suspende interpretação até SYN_REPORT, consulta o estado atual e não inventa um clique perdido. Revogação de acesso/desconexão remove o leitor e preserva o rastro. O monitor de `/dev/input` dispara uma varredura curta somente após mudanças.

Para posicionar o brilho, o GTK consulta o snapshot protegido da última coordenada válida recebida pelo cliente Wayland, sem depender do atraso da renderização limitada a FPS. Esse snapshot continua válido em repouso e é invalidado ao sair/remover a saída. Quando a imagem do cursor sobrepõe dois monitores, só posições cujo hotspot esteja dentro da saída podem substituir o snapshot. Não há sincronização temporal exata entre os fluxos evdev e Wayland.

`--no-clicks` desativa a fonte; `--click-device` seleciona caminhos explicitamente e pode ser repetido. Descoberta automática pressupõe `seat0`; seats diferentes exigem seleção explícita. Acesso negado é relatado em `click_detection` no diagnóstico. Não são modificados ACLs, grupos ou regras udev. Toques de touchpad interpretados pelo compositor, remapeamentos e cliques virtuais continuam fora desse backend.

Referências: [códigos de eventos do kernel](https://docs.kernel.org/input/event-codes.html), [implementação e máscaras por cliente no evdev](https://github.com/torvalds/linux/blob/master/drivers/input/evdev.c) e cabeçalho local `/usr/include/linux/input.h`.


## Validação de recepção física
O log distingue `Leitor de clique habilitado` (abertura/configuração concluída) de `Primeiro clique físico recebido` (primeira pressão efetivamente observada). A mensagem de recepção é emitida uma única vez por dispositivo conectado, evitando logging por movimento ou clique contínuo. Nomes dos dispositivos aparecem junto aos caminhos para evitar confusão entre mouse externo e touchpad interno.

## Origem do overlay e painéis
A superfície deve usar zona exclusiva **-1**, ancorada nas quatro bordas e sem margens. Zona 0 permite ao compositor afastá-la de painéis, alterando a origem e a extensão. Como as posições EXT são relativas à saída inteira, redimensioná-las para uma janela reduzida produz erro variável: com uma barra superior, por exemplo, o brilho fica mais baixo perto do topo e converge ao cursor perto do fundo. Cobrir toda a saída mantém a mesma origem para desenho e metadados. Não usar offsets fixos dependentes da configuração de uma barra.
