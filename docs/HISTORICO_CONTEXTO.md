# Contexto do Fairy Mouse

## Confirmação mais recente — início automático habilitado
O usuário consultou is-enabled e recebeu disabled; em seguida executou `systemctl --user enable fairy-mouse.service` e confirmou sucesso. O início automático está habilitado por ação do usuário. Não confundir essa configuração com validação de novo login/reboot, ainda adiada. Funcionamento atual em segundo plano foi relatado; rastro, clique, alinhamento e reconexão seguem validados.

O usuário pediu README com abertura acessível a leigos e passo a passo para ativar o mouse. README foi reescrito com compatibilidade, diagnóstico, permissão do Logitech, instalação, start, enable, diferenças entre active/enabled, controle diário, ajuda, atualização e remoção. Detalhes técnicos ficam ao final e em docs/. Não orientar apenas instalar como se isso habilitasse o serviço: instalação nova prepara unidade desativada; enable é uma ação separada.

## Etapa atual — instalação por usuário e serviço opcional (2026-10-28)
Usuário pediu continuar sem aguardar o teste de reboot. Essa validação e as medições ficam adiadas, sem bloquear o desenvolvimento. Recepção de clique, alinhamento e reconexão física seguem validados.

Preparados `tools/install-user.py` e `packaging/systemd/fairy-mouse.service.in`: cópia independente em ~/.local/share/fairy-mouse, launcher ~/.local/bin/fairy-mouse e unidade em XDG_CONFIG_HOME/systemd/user. Instalar sem sudo. Instalador não inicia/habilita serviço ou altera udev. Unidade usa sway-session.target (presente no Fedora e integrado pela configuração padrão), PartOf também da sessão gráfica, Restart=no, parada via SIGTERM e caminho estável do mouse. Nada foi instalado no usuário pela sandbox.

Próxima validação: usuário instalar e iniciar manualmente via systemctl --user, conferir logs e parar; autostart só habilitar por escolha explícita. Instruções em docs/INSTALACAO.md. A importação de ambiente gráfico é necessária no gerente systemd; Fedora Sway padrão já cuida disso nas próximas sessões. Não adicionar After=sway-session.target, pois pode criar ciclo com o WantedBy do target.

Testes: 53 encontrados, 51 passaram, 2 ignorados por sockets bloqueados. Launcher da cópia instalada foi executado fora do repositório em staging temporário, incluindo caminho com espaços. systemd-analyze --user verify foi bloqueado pela sandbox em operações de socket; verificar unidade no host antes de tratar serviço como validado. Nenhuma mudança nos efeitos.

## Estado atual — recepção do clique com acesso persistente
O usuário confirmou que recebeu o clique após a investigação da regra persistente. A recepção e a reconexão física estão validadas pelo usuário: desconectou e reconectou o mouse e o funcionamento voltou. Reboot ainda não foi confirmado. O caminho adotado é `/dev/input/fairy-mouse-logitech`, independente de eventN, com regra específica instalada e tag uaccess confirmada no banco udev.

Não foi determinada uma nova causa de código para a ausência transitória anterior; não atribuir a correção ao diagnóstico, que é somente inspeção. O diagnóstico agora tenta abrir/configurar o caminho fixo e informa erros reais. Próximo passo: validar novo boot sem setfacl. Não repetir o teste de reconexão como pendência já resolvida. Consumo continua adiado por orientação do usuário; autostart não instalado.

## Prioridade atual — 2026-10-28

Usuário pediu adiar medições e resolver acesso persistente ao Logitech. Preparada regra `packaging/udev/71-fairy-mouse-logitech.rules` com nome + input vendor 046d/product 4054 + classificação mouse, excluindo interface teclado. Não confundir input product 4054 com receptor USB c534. `uaccess` é aplicado antes de 73-seat-late, com ACL para a sessão local ativa. ACL padrão logind é rw; aplicação continua O_RDONLY. Autorização é por usuário e interface, não por aplicativo. Não prometer revogação de descritor já aberto.

Caminho estável: `/dev/input/fairy-mouse-logitech`. Instalador revisável `sudo bash tools/install-mouse-access.sh`; remoção com `--remove`. Arquivos fora do projeto não foram instalados pela sandbox. Próxima etapa é usuário instalar, confirmar diagnóstico, reconectar receptor e testar após reboot sem setfacl. Comando da app: `/usr/bin/python3 -m fairy_mouse --background --click-device /dev/input/fairy-mouse-logitech`. Medições e autostart continuam pendentes.

Corrigido ciclo do leitor para comparar identidade do nó com o descritor aberto e reabrir quando um caminho estável for reutilizado. Diagnóstico inclui `persistent_mouse_access`. Sintaxe udev e shell verificadas; testes de substituição/remoção do alias adicionados. Instruções completas em `docs/ACESSO_MOUSE.md`. Nenhuma ACL manual anterior foi removida, nenhum grupo alterado e nenhum autostart instalado.

O checkpoint abaixo preserva o estado funcional validado ontem; para prioridade de hoje prevalece esta seção.

## Retomada — encerramento em 2026-10-27

**Checkpoint histórico de 2026-10-27. As seções mais recentes no topo descrevem o estado atual.** O usuário encerrou o trabalho por hoje. Não há implementação em andamento que precise ser concluída durante esta pausa.

### Objetivo e decisões mantidas
Fairy Mouse para Fedora com Sway padrão, voltado a máquinas antigas: rastro de fada e brilho no clique, discretos e leves. Usuário aprovou o visual; preservar esse desenho. Aplicação deve rodar em segundo plano, sem janela principal. Não modificar o compositor. Autostart será opcional; não está instalado.

### O que já funciona e foi confirmado pelo usuário
- Rastro global sobre outras aplicações, via metadados EXT do cursor no Sway 1.11.
- Brilho no botão esquerdo físico do Logitech Wireless Mouse.
- Posição do efeito na ponta do cursor, corrigida pela zona exclusiva **-1**, com quatro âncoras.
- Execução do overlay sem janela de controle. A janela `--demo` serve apenas para testes.

Ambiente confirmado: Fedora 44 Sway; GTK 4, Gtk4LayerShell, Cairo; layer-shell v4 e gestores EXT v1. Usar `/usr/bin/python3`: o `python3` do PATH pode apontar para outro projeto.

### Executar e encerrar
Na raiz `/home/tamy/Projetos/fairy-mouse`:

```bash
/usr/bin/python3 -m fairy_mouse --diagnose
/usr/bin/python3 -m fairy_mouse --background --click-device /dev/input/event6
/usr/bin/python3 -m fairy_mouse --stop
```

`event6` era o Logitech nesta sessão; conferir nome no diagnóstico antes de reutilizar, pois a numeração pode mudar. O usuário concedeu ACL de leitura manualmente ao event6; anteriormente também a event3/event4, interfaces ELAN internas. Essa permissão é temporária e pode desaparecer após reboot/recriação dos nós. Falta de acesso impede apenas o brilho físico; o rastro continua. Não executar GUI como root nem conceder acesso amplo ao grupo input. Nenhuma regra persistente de acesso foi instalada.

### Arquitetura e correções que não devem regredir
- `gtk_runtime.py`: carregar biblioteca nativa Gtk4LayerShell **antes** de GTK/GDK por GI; backend Wayland no modo de segundo plano.
- `cursor.py`: conexão dedicada a metadados, sem imagens; leitor bloqueante em thread, posição pendente única e snapshot para clique mesmo em repouso. Posição já representa hotspot e já está transformada: não subtrair hotspot nem rotacionar novamente.
- `background.py`: superfície transparente por saída, região de entrada vazia, teclado sem foco, zona exclusiva **-1**. Zona 0 deslocava/comprimia desenho por causa de painéis.
- `clicks.py`: aceitar BTN_LEFT + eixos X/Y, inclusive interfaces compostas. O Logitech anuncia KEY_ENTER; rejeitar esse código na classificação fazia o mouse desaparecer. Aplicar máscara obrigatória por descritor antes de ler: somente BTN_LEFT e sincronização; O_RDONLY, sem grab ou reinjeção.
- `particles.py`/`rendering.py`: desenho compartilhado; padrão 48 partículas totais e 30 FPS, animação desativada em repouso. São limites configurados, não medições de consumo.

### Validação e próximos passos
Última suíte: **47 testes encontrados; 45 passaram e 2 ignorados** por bloqueio de sockets na sandbox. Compilação Python passou. O usuário validou rastro, brilho e alinhamento no desktop real. A sandbox não acessa display nem `/dev/input`; não confundir testes simulados com validação física. Nenhum commit foi criado nesta sessão.

Para amanhã, priorizar medições de CPU/memória e impacto no compositor; depois preparar instalação/autostart opcional e acesso persistente restrito ao mouse. Ainda faltam testes reais de vários monitores, escalas e hotplug. Tap-to-click, gestos, remapeamentos e cliques virtuais não são cobertos pelo backend físico. Não há benchmark concluído, autostart instalado ou decisão final de empacotamento.

Teste automatizado: `/usr/bin/python3 -m unittest discover -s tests -v`. Detalhes técnicos em `docs/INTEGRACAO.md`; histórico em `docs/PROCESSO.md`; comandos completos em `README.md`.

## Notas históricas da sessão

As seções abaixo preservam o raciocínio e os problemas encontrados. Para o estado vigente, prevalece o ponto de retomada acima.

## Objetivo e público
Ferramenta para Fedora com Sway/Wayland que desenha um rastro de fada no movimento do cursor e um brilho breve no clique. Prioridade: computadores antigos e com poucos recursos. Animações simples, discretas e configuráveis.

## Estado observado em 2026-10-27
O diretório contém `.venv/` e diretórios de ambiente, mas não contém código Python, manifesto de dependências ou testes. `main.py` e `AGENTS.md`, vistos anteriormente nesta conversa, estão ausentes. Não foram restaurados automaticamente. As variáveis da sessão indicam Wayland e Sway; isso não comprova acesso funcional ao compositor pelo ambiente de execução.

O protótipo histórico usava Python, GTK 4, Gtk4LayerShell, Cairo e evdev. Tinha `find_mouse()` indefinido, janela de 1366×768, clique desenhado em (960, 540), e nenhum rastro. Esses dados são históricos, não uma inspeção de código presente.

## Decisões
- Fedora + Sway são o alvo inicial; não prometer compatibilidade com outros compositores.
- Validar posição global e cliques antes de implementar a experiência visual completa.
- Não considerar integração de deltas evdev uma fonte precisa de posição global.
- Aplicação visual sem foco, sem capturar cliques e sem execução como root.
- Limitar partículas e encerrar o temporizador quando os efeitos terminarem.
- Python/GTK/Cairo são candidatos para prototipagem; a escolha final depende de medições.
- Não criar captura de tela contínua para localizar o cursor.

## Pendências prioritárias
1. Confirmar versão de Fedora/Sway, monitores, escalas e máquina de referência.
2. Recuperar ou recriar conscientemente a base de código.
3. Validar um mecanismo de rastreamento compatível com o Sway instalado.
4. Medir consumo antes de decidir a tecnologia final e o empacotamento.

## Continuidade
Leia `docs/ANALISE.md` antes de implementar. Atualize este arquivo quando mudar uma decisão ou surgir uma restrição. Registre trabalho e validações em `docs/PROCESSO.md`. Diferencie hipótese, implementação e resultado medido.

## Implementação inicial — 2026-10-27
Base recriada em `fairy_mouse/` com entrada `main.py`. Há demonstração interativa local (`/usr/bin/python3 -m fairy_mouse --demo`) e diagnóstico (`--diagnose`). Simulação limitada a 48 partículas por padrão; 30 FPS; timer desativado sem partículas. Configuração por argumentos de linha de comando. Sem dependências Python externas para os testes da simulação.

Ambiente identificado: Fedora 44 Sway, GTK 4, Gtk4LayerShell e Cairo disponíveis no Python do sistema. O socket IPC e o display não ficaram acessíveis nesta execução. Não usar o `python3` genérico como referência de dependências: o PATH aponta para um ambiente de outro projeto. Preferir `/usr/bin/python3`.

Seis testes passaram. A tentativa de abertura gráfica confirmou indisponibilidade do display; o tratamento foi corrigido para encerrar claramente com código 1. Aparência, consumo e integração desktop continuam sem validação. RF01/RF02 estão demonstrados apenas em janela própria, não atendidos globalmente. Próxima prioridade permanece obter uma fonte real de posição/cliques no Sway. Nenhum patch de compositor, serviço ou permissão de dispositivo foi instalado.

## Requisito confirmado — execução em segundo plano
A versão final deve funcionar como aplicativo de sessão em segundo plano, sem janela principal e sem roubar foco. A janela `--demo` permanece uma ferramenta de desenvolvimento e validação visual. Inicialização automática junto ao Sway deve ser opcional; não instalar ou ativar autostart durante o desenvolvimento sem solicitação. O processo deve permanecer no usuário da sessão, permitir encerramento limpo e impedir instâncias duplicadas. Não usar daemonização por fork: manter um processo supervisionável pelo mecanismo de sessão escolhido. Escolher entre configuração do Sway e serviço systemd de usuário após validar ambiente gráfico, dependências e encerramento com a sessão.

## Continuação — visual aprovado e Sway padrão
O usuário testou e aprovou a demonstração visual. Preservar o desenho. Escolheu explicitamente manter o Sway padrão e investigar alternativas; não desenvolver/aplicar patches do compositor como solução atual.

Implementado `--background` como sobreposição experimental por saída, sem foco e com região de entrada vazia; `--stop`, instância única, socket privado, limpeza e tratamento de sinais. Ainda exige produtor externo de eventos. Renderização compartilhada com a demo; limite de partículas é global entre saídas. Há ferramenta de eventos sintéticos em `tools/send_event.py`.

Descoberta: binário local Sway 1.11; essa versão adicionou protocolos de captura EXT com sessão específica de cursor. Investigar eventos de posição sem captura contínua da tela. Consulta ao registro já integra `--diagnose`; presença dos protocolos é apenas indicação de candidato, não prova de rastreamento. Converter coordenadas de buffer transformado para lógicas; cliques precisam de investigação separada. Ver `docs/INTEGRACAO.md`.

Estado de validação: testes de simulação, Cairo sem display, protocolo, registro Wayland e trava de instância; sockets reais bloqueados na sandbox. Overlay sem validação gráfica. Não ativar autostart até existir fonte de eventos real e validar ciclo de vida. As pendências históricas acima devem ser lidas junto deste estado mais recente: a base já foi recriada e o visual da demo foi aprovado.

## Cliente de posição implementado — 2026-10-27
O usuário executou o diagnóstico fora da sandbox e confirmou Sway 1.11, conexão IPC/Wayland e os dois protocolos EXT v1 presentes. Isso valida anúncio de capacidades, ainda não o rastro real.

`fairy_mouse/cursor.py` implementa sessões de metadados por saída, usando biblioteca padrão e conexão Wayland dedicada. Não cria frames/buffers de captura, não lê imagens, teclado ou evdev. `--background` agora inicia esse cliente automaticamente; `--background --external-events` preserva o modo de testes sintéticos. `--seat` seleciona seat, padrão `seat0`.

Conversão: posições recebidas já estão em coordenadas de buffer transformado; usar modo físico transformado de wl_output e dimensões lógicas reais do DrawingArea. Não rotacionar novamente nem subtrair hotspot. Descartar ponta fora da saída. Saídas devem oferecer wl_output v4 para nomes de conectores.

Leitor bloqueante em thread, uma única posição pendente e entrega limitada pelo FPS; GTK permanece na thread principal. Fechar conexão desbloqueia leitor; erro de protocolo encerra com código de falha. Limite de inicialização de dois segundos. Sem fallback para deltas estimados. Cliques globais ainda pendentes; brilho continua disponível na demo e em testes sintéticos.

Validação: 28 testes encontrados, 26 passaram e 2 ignorados por bloqueio de sockets na sandbox. O protocolo foi testado com compositor simulado em memória, não com o compositor real. Próximo passo: usuário testar `--background` sobre aplicações e confirmar alinhamento, transparência e passagem de cliques; depois investigar fonte de cliques e medir consumo. Visual da demo permanece aprovado, autostart não instalado.

## Correção da inicialização Gtk4LayerShell — 2026-10-27
O primeiro teste real de `--background` parou em `Layer.is_supported()`, antes do cliente de cursor. O código carregava GTK/GDK via GI antes da biblioteca nativa de layer-shell; faltava o preload exigido pelo upstream. A falha observada é compatível com esse problema ou backend X11, não prova ausência do protocolo no Sway.

Criado `gtk_runtime.py`: carregar a biblioteca nativa (SONAME encontrado no sistema, fallback `.so.0`) com símbolos globais antes de qualquer import GI de GTK; manter referência e selecionar `GDK_BACKEND=wayland` apenas para o modo de segundo plano. Diagnóstico também faz preload antes dos imports GI e informa `layer_shell_preloaded`, biblioteca, backend solicitado pelo ambiente e versão do protocolo no registro. Não há necessidade de configurar LD_PRELOAD manualmente.

Quatro testes novos cobrem ordem, backend, cache e erro da biblioteca; um deles carrega as bibliotecas reais em processo novo sem display. Total: 32 testes, 30 passaram, 2 ignorados por sockets. Correção gráfica ainda precisa de novo teste real; não afirmar que o rastro funcionou. Referência: https://github.com/wmww/gtk4-layer-shell/blob/main/linking.md.

## Rastro global validado e clique físico integrado — 2026-10-27
O usuário confirmou: `--background` rodou e o trail funcionou perfeitamente. Registrar o rastro global como validado nessa sessão Sway 1.11; preservar desenho e integração. O efeito de clique ainda não existia fora da demo, portanto a ausência relatada não era falha do rastro.

Implementado `clicks.py`: descoberta por capacidades de sysfs, leitura O_RDONLY de ponteiros, filtro EVIOCSMASK por descritor para BTN_LEFT, fontes GLib de prontidão, sem grab/reinjeção ou dependência evdev. Não alterar ACLs/grupos/udev automaticamente e não executar como root. Acesso ausente deixa o rastro funcionando com aviso e relatório `click_detection` em `--diagnose`. Hotplug usa monitor de diretório, sem polling. Fonte opcional: `--no-clicks` e `--click-device` repetível. Outro seat exige caminho explícito.

O brilho consulta o snapshot mais recente do cliente Wayland, antes de eventual entrega limitada a FPS. Snapshot permanece válido em repouso, é invalidado em leave/remoção e não é substituído por coordenada cujo hotspot esteja fora do monitor. Não há correlação exata de timestamps entre input físico e posição do compositor.

Escopo: botão físico esquerdo; tap-to-click e cliques sintetizados/remapeados pelo compositor não suportados. Validação real do brilho depende de dispositivo legível e ainda está pendente. Sandbox não expõe /dev/input; testes usam entrada simulada. Próxima etapa: testar clique físico na sessão real e, se necessário, examinar apenas o acesso do mouse identificado em click_detection. Autostart permanece pendente.

## Diagnóstico real do clique — acesso negado
O usuário confirmou que o rastro permanece funcionando, mas o novo leitor de cliques não abre nenhum dispositivo: EACCES em `/dev/input/event3` e `/dev/input/event4`. Portanto ainda não há validação real do clique e não é falha do efeito visual.

Metadados sysfs atuais: event3 = `ELAN06FA:00 04F3:31BE Mouse`; event4 = `ELAN06FA:00 04F3:31BE Touchpad`. São interfaces de ponteiro do dispositivo ELAN. Os números podem mudar após reboot. Necessário acesso de leitura específico para esses nós na sessão do usuário; a sandbox não permite concedê-lo. Não adicionar usuário ao grupo input nem executar GUI com sudo. Para teste manual, ACL temporária de leitura nesses nós; documentado em README. Isso não implementa tap-to-click: testar pressão física do botão.

Melhoria: o diagnóstico agora inclui nome e indicador `permission_denied`, distinguindo erro de permissão de dispositivo ausente. Nenhuma permissão real foi alterada pelo agente.

## Correção: mouse externo Logitech omitido da descoberta
O usuário aplicou ACL a event3/event4 e os leitores abriram, mas nenhum brilho ocorreu. Esclareceu que estava usando o mouse externo. Inventário sysfs identificou `event6 = Logitech Wireless Mouse`, com BTN_LEFT, REL_X/REL_Y e também KEY_ENTER (28). A classificação antiga descartava qualquer ponteiro com teclas de digitação: bug reproduzido na descoberta. Event5 é teclado Logitech sem BTN_LEFT; continua excluído.

Corrigida classificação para BTN_LEFT + eixos X/Y, aceitando interfaces compostas. O filtro obrigatório EVIOCSMASK continua aplicado antes da leitura, limitando eventos recebidos a BTN_LEFT e sincronização. Nenhuma tecla extra é habilitada no filtro. Teste de regressão específico para o Logitech adicionado. Não se deve remover esse suporte com heurística baseada em KEY_ENTER.

A orientação anterior liberou o ELAN interno e não o mouse usado. Atualizado README para ACL manual restrita ao event6, após conferir nome; nenhuma ACL foi executada pelo agente. Acrescentados nome no log de abertura e uma única mensagem na primeira pressão recebida, para separar inicialização de validação funcional. Total: 47 testes, 45 passaram e 2 ignorados. Clique real ainda pendente de teste com o Logitech corrigido e legível.

## Clique validado; correção de alinhamento com painéis
O usuário confirmou funcionamento do brilho após correção da descoberta do Logitech e acesso ao event6. Relatou deslocamento dependente da posição na tela: efeito mais abaixo quando cursor está mais acima. Isso não é ausência de eventos físicos.

Encontrado erro de geometria no overlay: `set_exclusive_zone(window, 0)` solicita ao compositor evitar áreas reservadas por painéis. A janela pode começar abaixo de uma barra e ter altura menor, mas as coordenadas EXT cobrem a saída inteira. Converter a altura total para essa janela reduzida causa deslocamento variável. Corrigido para zona -1, com âncoras nas quatro bordas, para cobrir a saída inteira e compartilhar origem/extensão com o cursor. Não compensar com offset fixo nem subtrair hotspot da imagem.

Correção fundamentada no protocolo wlr-layer-shell, seção set_exclusive_zone. A geometria efetiva ainda precisa de confirmação visual pelo usuário; sem sessão gráfica acessível na sandbox. Visual e limites de partículas preservados.

## Marco validado pelo usuário — efeitos globais e alinhamento
O usuário confirmou que a posição foi resolvida e o efeito de clique funciona. Na sessão real Fedora/Sway 1.11, estão validados: rastro global, brilho ao pressionar botão esquerdo físico do Logitech Wireless Mouse, alinhamento da sobreposição após zona exclusiva -1 e execução sem janela principal. O dispositivo de teste foi event6, com ACL de leitura aplicada manualmente pelo usuário; esse número e a permissão não são garantidos após reinicialização.

Preservar esse comportamento nas próximas alterações. Pendências: medir CPU/memória e custo no compositor em hardware de referência; definir instalação/início automático opcional e acesso restrito ao dispositivo que sobreviva ao ciclo da sessão; validar múltiplos monitores/escalas e hotplug reais. Tap-to-click permanece fora do backend atual. Nenhum autostart ou acesso persistente foi instalado. Não confundir aprovação funcional nessa sessão com benchmark ou validação completa de todos os cenários.
