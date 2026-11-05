# Registro do processo

## 2026-10-27 — Levantamento inicial
- Pedido: analisar requisitos antes de implementar e preservar contexto durante o desenvolvimento.
- Inspeção: diretório sem `main.py` e sem `AGENTS.md`; há ambiente `.venv/`. Nenhum código da aplicação foi executado ou alterado.
- Sessão: variáveis de Wayland e Sway presentes; conexão gráfica não foi testada.
- Pesquisa: consultadas fontes primárias de Wayland, Sway e Gtk4LayerShell para distinguir renderização de observação global de entrada.
- Resultado: requisitos e critérios de aceitação em `ANALISE.md`; decisões e pendências em `../CONTEXTO.md`.
- Risco principal: obter posição e cliques reais sem interceptar entrada e sem estimar posição com deltas brutos.
- Validação realizada: conferência da existência e conteúdo dos documentos. Sem testes de desempenho, GUI ou funcionalidades, pois não há implementação presente.
- Próxima etapa: prova técnica de rastreamento no Sway e recuperação/recriação explícita da base, antes de desenvolver partículas e brilho.

## Como registrar novas etapas
Para cada mudança, registrar data, objetivo, decisão, arquivos afetados, comandos/testes executados, resultados e pendências. Não apresentar metas como medições nem protótipos como funcionalidades concluídas.

## 2026-10-27 — Base executável e demonstração
- Autorização: usuário autorizou começar a implementação após a análise.
- Ambiente: Fedora 44 Sway; Python do sistema importa GTK 4, Gtk4LayerShell e Cairo. `swaymsg -t get_version` e `get_seats` falharam por conexão indisponível.
- Pesquisa adicional: documentação IPC e código de entrada do Sway consultados. Não foi identificada API IPC padrão para movimento global; não se implementou estimativa evdev como substituto.
- Criados: pacote `fairy_mouse`, entrada `main.py`, testes, README e exclusões de arquivos gerados em `.gitignore`.
- Implementados: partículas com duração variável e limite rígido, brilho radial de 220 ms, emissão limitada por tempo/distância, temporizador ocioso desativado, CLI de configuração e diagnóstico somente de leitura.
- Verificação: `/usr/bin/python3 -m unittest discover -s tests -v` — seis testes passaram, incluindo rajada de mil cliques. Compilação dos módulos passou. Diagnóstico executado e dependências confirmadas.
- Abertura da demonstração: display inacessível. A primeira tentativa revelou erro GTK e retorno enganoso de sucesso; adicionada verificação de `Gdk.Display.get_default()` e versão explícita de Gdk. Nova tentativa retornou mensagem clara; teste separado confirma código 1.
- Limites: sem validação visual ou medição de consumo; sem overlay global. Não foram alteradas configurações do sistema ou do Sway.
- Referências adicionais: https://github.com/swaywm/sway/blob/master/sway/input/cursor.c e https://github.com/swaywm/sway/blob/master/sway/sway-ipc.7.scd.

## 2026-10-27 — Requisito de execução em segundo plano
- Usuário reforçou que a versão final deve executar em segundo plano.
- Atualizados contexto e análise com operação sem janela principal, autostart opcional, instância única e encerramento ligado à sessão.
- A demonstração local permanece ferramenta de desenvolvimento. Nenhum autostart ou serviço foi instalado; código executável não foi alterado.

## 2026-10-27 — Sobreposição e investigação no Sway padrão
- Usuário aprovou a aparência da demo e autorizou continuar. Confirmou preferência pelo Sway padrão, sem patches.
- Compartilhado renderer para preservar o visual. Adicionado identificador de saída às partículas sem alterar o comportamento da demonstração.
- Implementados overlay experimental por monitor, passagem de entrada declarada via GDK, limite global, loop sob demanda, SIGINT/SIGTERM, fechamento do display, `--stop`, trava e socket privado. Nenhum autostart instalado.
- Adicionados parser de eventos e injetor sintético de teste. Não há captura global automática de mouse/cliques.
- Identificado Sway 1.11. Pesquisa nas notas oficiais e especificações EXT encontrou sessão de cursor com metadados de posição. Implementada apenas consulta de capacidades pelo registro Wayland; cliente de rastreamento continua pendente.
- Tentativa de Sway headless em diretório temporário falhou ao abrir socket Wayland. Sockets UNIX são bloqueados na sandbox. Não houve alteração da sessão do usuário.
- Testes: 20 encontrados, 18 passaram, 2 ignorados por falta de permissão de sockets. Lock real também validado separadamente com transporte simulado. Cairo validado sem display. Compilação dos módulos passou; diagnóstico relata explicitamente ausência de acesso ao registro.
- Documentação: README atualizado e `INTEGRACAO.md` criado com contrato, fontes e limites. Próxima etapa: cliente de metadados do cursor, conversão de coordenadas e descoberta de fonte de cliques compatível com Sway padrão.

## 2026-10-27 — Cliente de metadados integrado
- Entrada do usuário: diagnóstico real confirma Sway 1.11, IPC e registro Wayland conectados, gestores EXT v1 anunciados.
- Conferidas definições primárias de `ext-image-copy-capture-v1` e `ext-image-capture-source-v1`; implementado cliente mínimo usando biblioteca padrão, sem buffers de imagem ou leitura de entrada bruta.
- Arquivos: novo `cursor.py`, novos testes de cursor, alterações em `background.py`, CLI, diagnóstico e documentação.
- Funcionalidade: `--background` solicita posições automaticamente; modo sintético agora exige `--external-events`. Seat selecionável, negociação limitada a dois segundos, mapeamento físico/lógico por saída, tratamento de rotação, hotplug e encerramento.
- Desempenho estrutural: somente última posição pendente, entrega ao GTK limitada pelo FPS, leitura bloqueante sem polling e sem acesso GTK pela thread leitora.
- Verificação: 28 testes encontrados; 26 passaram, 2 ignorados por sockets bloqueados. Servidor simulado valida handshake, sessões sem pedidos de frames, posições, monitor adicionado/removido, mudança de modo, ausência de protocolo e perda de ponteiro. Compilação dos módulos e CLI verificadas.
- Limites: não foi possível conectar à sessão gráfica na sandbox; teste real do rastro permanece pendente. Ainda sem clique global, benchmark ou autostart instalado. Não se afirma que anúncio dos protocolos garante funcionamento da sessão de cursor.

## 2026-10-27 — Falha de layer-shell no primeiro teste real
- Usuário relatou falha na verificação de suporte a layer-shell. O cliente de cursor não chegou a iniciar.
- Inspeção e documentação upstream identificaram requisito ausente: carregar Gtk4LayerShell nativo antes de GTK/libwayland. O exemplo Python oficial usa preload explícito com ctypes.
- Implementado bootstrap dedicado, com biblioteca versionada descoberta no sistema, símbolos globais, cache e backend Wayland para a sobreposição. Atualizados diagnóstico e mensagem de erro; removida pontuação duplicada do erro CLI.
- Validação: 32 testes, 30 passaram e 2 ignorados pela sandbox. Novo teste em subprocesso confirma carregamento real sem importar GTK antes do preload. Compilação verificada e ausência de display continua retornando código 1 sem traceback.
- Limite: suporte gráfico ainda sem comprovação local por falta de acesso ao display; aguardar novo teste real. Nenhuma configuração do sistema, compositor ou início automático foi alterada.

## 2026-10-27 — Rastro aprovado e observação do clique físico
- Usuário confirmou rastro global funcionando perfeitamente após correção de preload; faltava o brilho no clique, ainda sem fonte global na versão anterior.
- Conferidas documentação do kernel e API evdev. Implementado leitor com biblioteca padrão, sem instalar dependências, alterar permissões, capturar entrada exclusiva ou criar bindings no Sway.
- Novo `clicks.py`: capacidades sysfs/ioctl, abertura estritamente O_RDONLY, filtro de tipos e BTN_LEFT por cliente, parser nativo, estado de botão, recuperação SYN_DROPPED, leitor GLib, encerramento e diagnóstico de acesso. Ligado à sobreposição com `--no-clicks`/`--click-device` e monitor de hotplug.
- Cursor: adicionado snapshot protegido e invalidação de saída para clique mesmo em repouso; posições fora dos limites do hotspot não substituem a posição válida ao cruzar saídas.
- Testes: 44 encontrados, 42 passaram e 2 ignorados por sockets bloqueados. Novos testes cobrem clique sem repetição, perda de sincronização, classificação de ponteiros, máscaras, abertura somente leitura, permissão negada, desconexão, snapshot e bordas.
- Conferida ABI com programa C temporário compilado contra linux/input.h: EVIOCSMASK, EVIOCGBIT e tamanho de input_event correspondem ao código Python. Nenhum binário de produção foi introduzido.
- Limites: sem /dev/input exposto nesta sandbox; clique físico e hotplug real precisam de validação pelo usuário. Tap-to-click e remapeamento do botão primário não são reproduzidos. README, integração e contexto atualizados.

## 2026-10-27 — Clique bloqueado por EACCES
- Usuário enviou diagnóstico real: protocolos e layer-shell funcionais; leitores de event3/event4 recusados por permissão, por isso nenhum clique foi observado.
- Identificados nomes via sysfs: interfaces Mouse e Touchpad do ELAN06FA:00 04F3:31BE.
- Acrescentados nome do dispositivo e `permission_denied` ao diagnóstico, com testes para diferenciar EACCES e ENOENT.
- Preparadas instruções de ACL temporária restrita aos dois ponteiros, aplicáveis pelo usuário no terminal; nenhuma alteração de ACL, grupo ou udev executada.
- Limitação mantida: é necessário testar botão físico; tap-to-click não é gerado por esse backend.

## 2026-10-27 — Correção de descoberta do Logitech
- Após ACL em event3/event4, log confirmou abertura de leitores, mas usuário não viu brilho. Usuário esclareceu que usava mouse externo.
- Inspeção de capacidades sysfs: event3/event4 são ELAN; event6 é Logitech Wireless Mouse com BTN_LEFT, eixos relativos X/Y e KEY_ENTER. A heurística anterior descartava essa interface por KEY_ENTER, explicando por que o mouse usado nunca recebia leitor.
- Corrigida classificação de ponteiros compostos, preservando filtro EVIOCSMASK obrigatório aplicado antes de ler eventos. Teclado comum Logitech event5 permanece excluído.
- Acrescentados testes de descoberta do mouse composto, exclusão do teclado e ordem de aplicação da máscara antes de qualquer leitura. Agora 47 testes, 45 aprovados e 2 ignorados pela sandbox.
- Log passa a incluir nome do dispositivo na abertura e mensagem única na primeira pressão física efetivamente recebida. README corrige orientação de ACL para o dispositivo externo após conferir nome. Nenhuma permissão do sistema alterada pelo agente.
- Validação real do clique depende de novo teste no event6; não tratar abertura de descritor como confirmação de clique recebido.

## 2026-10-27 — Alinhamento do clique e área reservada por painéis
- Usuário confirmou clique funcionando, com brilho deslocado conforme posição vertical do cursor.
- Inspeção identificou zona exclusiva 0 no overlay. O protocolo determina que esse valor respeita reservas de outros painéis, podendo deslocar e reduzir a superfície; isso contradiz a conversão de posição baseada na saída inteira.
- Alterado para zona -1, mantendo âncoras nas quatro bordas. A sobreposição passa a solicitar toda a saída, sem reservar espaço para si. Nenhum ajuste arbitrário de coordenadas foi introduzido.
- Atualizadas análise e integração com a geometria correta; contexto registra clique já validado e alinhamento em teste.
- Validação: suíte existente e compilação executadas; confirmação gráfica pendente na sessão real.
- Fonte: https://github.com/swaywm/wlr-protocols/blob/master/unstable/wlr-layer-shell-unstable-v1.xml, set_exclusive_zone.

## 2026-10-27 — Confirmação do alinhamento e do brilho
- Usuário confirmou: posição resolvida e efeito de clique funcionando.
- Marco funcional: rastro global, clique físico e alinhamento validados na sessão Sway 1.11, após correção de descoberta do Logitech e geometria do overlay.
- Registrada a configuração validada em CONTEXTO.md. Código não alterado nesta etapa; sem novos testes, pois a mudança é documental.
- Permanecem pendentes: medições, integração opcional com inicialização de sessão, persistência de acesso restrito e cenários com vários monitores/hotplug.

## 2026-10-27 — Encerramento do dia
- Usuário solicitou encerrar e preservar contexto para a próxima sessão.
- Consolidado ponto de retomada no início de CONTEXTO.md: funcionalidades aprovadas, configuração e permissões temporárias, comandos, arquitetura, correções que não devem regredir, testes e próximos passos.
- Notas anteriores marcadas como históricas para evitar interpretar problemas já resolvidos como pendências atuais.
- Somente documentação alterada. Nenhum processo encerrado, autostart ativado, permissão alterada ou commit criado nesta etapa. Sem nova execução de testes por se tratar exclusivamente de documentação.

## 2026-10-28 — Acesso persistente ao Logitech
- Usuário adiou medições e priorizou solução persistente de acesso.
- Inspecionados atributos de input e propriedades udev reais: Logitech Wireless Mouse, input vendor 046d/product 4054, receptor USB c534, interface mouse separada do teclado.
- Preparada regra específica com uaccess e link estável, instalador/remover idempotente que recusa substituir arquivos divergentes e documentação do escopo de ACL e validação física. Nada instalado fora do projeto.
- Melhorado hotplug: descritores obsoletos são removidos antes de reabrir um alias que passou a apontar a outro nó; callbacks tardios de dispositivos removidos são ignorados.
- Diagnóstico agora informa regra presente, caminho estável e acesso de leitura. Testes de substituição e remoção de alias adicionados.
- Validação: udevadm verify aprovou a regra; bash -n aprovou instalador; 49 testes, 47 passaram e 2 ignorados pela sandbox. Instalação, ACL da sessão ativa, reconexão e reboot ainda dependem da execução no host pelo usuário.

## 2026-10-28 — Investigação após instalação persistente
- Usuário relatou ausência do clique após usar a solução persistente; ainda sem saída de inicialização/diagnóstico dessa tentativa.
- Inspeção somente de leitura confirma regra instalada idêntica ao projeto e banco udev do Logitech contendo DEVLINKS=/dev/input/fairy-mouse-logitech e tags uaccess/seat. Portanto o match da regra ocorreu. A sandbox não expõe /dev/input nem permite consultar o bus de logind; não concluir que link/ACL estejam ausentes no host com base nisso.
- Diagnóstico do caminho persistente melhorado: tenta abrir/configurar de verdade o leitor, informa nome, erro e permission_denied; substitui teste superficial de os.access.
- Solicitadas ao usuário saída de --diagnose e mensagens do --background com o caminho estável para localizar a etapa da falha. Não ampliar permissões nem trocar a regra sem evidência.
- Suíte existente: 49 testes, 47 passaram e 2 ignorados. Nenhuma nova configuração de sistema aplicada.

## 2026-10-28 — Recepção confirmada no acesso persistente
- Usuário confirmou: recebeu o clique.
- Registrada recepção funcional na sessão atual. Não houve nova modificação de regra ou de leitura após a investigação; a melhoria do diagnóstico não altera permissões nem entrega de eventos.
- Permanecem sem confirmação: reconexão física e reboot sem ACL manual. Não declarar toda a persistência validada antes desses testes.
- Somente contexto e processo atualizados nesta etapa.

## 2026-10-28 — Reconexão física validada
- Usuário desconectou e reconectou o mouse e confirmou que voltou a funcionar.
- Recepção e recuperação após reconexão estão validadas na sessão real. Falta confirmar funcionamento após reinicialização sem setfacl.
- Atualizado o estado vigente em CONTEXTO.md; nenhuma mudança de implementação nesta etapa.

## 2026-10-28 — Instalação por usuário e integração opcional com sessão
- Usuário adiou o teste após reboot e autorizou continuar. Medições também permanecem adiadas.
- Confirmada integração nativa Fedora Sway: sway-session.target e script que importa ambiente e encerra targets ao sair do compositor.
- Criados instalador Python sem sudo e template de unidade de usuário. Copia pacote/launcher para ~/.local, prepara unidade desativada, recusa arquivos alheios e remoção de unidade habilitada. Não executa systemctl, não inicia GUI nem altera regra udev.
- Unidade vincula parada à sessão, usa caminho estável do Logitech e não reinicia automaticamente. Fluxos de instalar, iniciar, consultar logs, habilitar opcionalmente, desativar, atualizar e remover documentados.
- Testes: 53 encontrados; 51 passaram, 2 ignorados. Cópia instalada executa --help fora do repositório, suporta espaços no caminho e reinstalação/remoção em staging temporário. Nenhum teste gráfico novo foi realizado.
- Verificação systemd-analyze --user verify bloqueada pela sandbox em operações de socket, não declarada aprovada. Validação de serviço real e ciclo de sessão ficam para o host.
- Nada instalado/habilitado no usuário; código do rastro e brilho preservado.

## 2026-10-28 — Execução em segundo plano observada
- Usuário relatou que está rodando sem precisar ativar manualmente agora.
- Registrado funcionamento observado, sem atribuir habilitação automática ou validação de reboot ainda não confirmadas. Nenhuma instância adicional criada ou serviço habilitado pelo agente.
- Apenas documentação alterada; sem novos testes.

## 2026-10-28 — README para usuários iniciantes e autostart confirmado
- Usuário informou disabled, recebeu instrução de enable e confirmou sucesso. Registrada habilitação por ação do usuário, sem presumir teste de reboot.
- Por solicitação do usuário, reescrito README com linguagem simples e fluxo completo: diagnóstico, acesso ao Logitech, instalação, execução em segundo plano e habilitação opcional. Explicada diferença entre active e enabled e incluídos comandos diários, ajuda, atualização e remoção.
- Removidas repetições e afirmações desatualizadas de que o início automático ainda não havia sido habilitado. Limites de compatibilidade e pendências ficam explícitos; detalhes técnicos ao final e em documentos de apoio.
- Revisão documental: conferidos comandos contra instaladores e unidade existentes e verificados links locais. Código executável não alterado; testes não repetidos.

## 2026-10-28 — Preparação do primeiro envio ao GitHub
- Usuário solicitou criar repositório ainda inexistente, com nome fairy-mouse-effects, e enviar a versão atual.
- GitHub não está conectado nesta sessão; gh não está instalado e .git do workspace é vazio/somente leitura. Repositório remoto ainda não criado e nenhum push realizado.
- Preparado snapshot e commit em repositório temporário independente para não modificar o .git do workspace; somente fontes, testes, documentação e instaladores. Ambientes, caches e credenciais excluídos.
- Verificação antes do envio: 53 testes, 51 passaram e 2 ignorados. Publicação aguarda autenticação via conexão GitHub. Visibilidade privada proposta como padrão; não houve publicação pública.

## 2026-11-04 — Migração documental para Claude Code
- Usuário solicitou migrar toda a documentação para o equivalente do Claude.
- Criado CLAUDE.md na raiz, com instruções estáveis, comandos e import do resumo vigente em .claude/contexto.md. Regras de efeitos Python e instalação ficaram em .claude/rules/ com escopo por caminhos.
- Preservado integralmente o antigo CONTEXTO.md em docs/HISTORICO_CONTEXTO.md; CONTEXTO.md tornou-se índice de compatibilidade. O resumo atual consolida decisões sem carregar todo o histórico ou suas pendências já resolvidas.
- Adicionado docs/CLAUDE_CODE.md com mapa de migração, retomada e manutenção. README mantém abertura para leigos e agora aponta ao contexto/entrada do Claude. Guias técnicos reconciliados com validações já relatadas e decisão de manter Sway padrão.
- Ignorados apenas arquivos pessoais CLAUDE.local.md e .claude/settings.local.json; instruções compartilhadas em .claude/ permanecem versionáveis. Diretórios protegidos .codex/.agents não foram alterados; não havia instruções úteis visíveis para converter.
- Preservadas pendências: criar/publicar fairy-mouse-effects no GitHub sem alegar push; medições e reboot adiados; início automático habilitado pelo usuário mas sem confirmação de nova sessão.
- Validação documental: links locais, import de contexto, regras com caminhos e integridade do arquivo histórico conferidos. Sem mudanças de código executável ou execução da suíte; carregamento no próprio Claude Code ainda não verificado nesta sessão.

## 2026-11-05 — Análise de estado após reinicialização
- Observado no host: boot às 18:06; sessão gráfica atual é o compositor umbriel (umbriel-nightly 20261104), não Sway. Sway continua instalado como sessão alternativa.
- fairy-mouse.service segue enabled, mas inactive, sem entradas no journal deste boot: sway-session.target não foi ativado nesta sessão, então o serviço não tinha como iniciar. O comportamento após login em Sway segue sem validação.
- Regra udev persistiu após reboot: /dev/input/fairy-mouse-logitech → event6, com ACL do usuário e leitura OK. Diagnóstico no umbriel informa layer-shell v4 e protocolos ext de captura de cursor, mas o rastro não foi executado nesse compositor.
- Workspace sem .git e gh não instalado; publicação continua pendente. Cópia instalada igual ao repositório (runtime.py conferido).
- Testes: 53 executados, 53 aprovados, nenhum ignorado; compileall OK. Sem mudanças de código.

## 2026-11-05 — Instalação em um comando e regra genérica de mouse
- Objetivo do usuário: instalar com facilidade no computador da namorada (Fedora + Sway), com README leigo no topo e detalhes técnicos abaixo. Decisões do usuário: liberar qualquer mouse, distribuir pelo GitHub, ligar e habilitar tudo na instalação.
- Criados `instalar.sh` (confere Fedora/Sway, instala dependências faltantes via dnf, instala a regra udev, instala o app, habilita e inicia se houver SWAYSOCK; idempotente, serve para atualizar) e `desinstalar.sh`.
- Nova regra `packaging/udev/71-fairy-mouse.rules`: uaccess para ID_INPUT_MOUSE, excluindo teclados. A regra do Logitech foi movida para `packaging/udev/legacy/`, e `install-mouse-access.sh` a remove de /etc só se estiver idêntica. Serviço sem `--click-device`. Diagnóstico passou a informar a regra nova, a antiga e os nós legíveis.
- README reescrito; ACESSO_MOUSE, INSTALACAO, CLAUDE.md, regra de instalação e contexto atualizados. A URL do GitHub ficou como placeholder.
- Verificado: 53 testes OK, compileall, `bash -n` nos três scripts, `udevadm verify` nas duas regras, instalação/remoção em staging com espaço no caminho e diagnóstico real. **Não executados:** `instalar.sh`/`desinstalar.sh` no host (exigem sudo e alteram serviço e udev), remoção da regra antiga em /etc e a regra genérica com outros mouses.

## 2026-11-05 — Publicação no GitHub
- O usuário criou `TamyDB/fairy-mouse-effects` e preferiu SSH, que já estava configurado. Repositório Git inicializado no workspace (branch main), commit inicial `de24dcc` enviado e conferido com `git ls-remote`. A API do GitHub confirma que ele é público.
- O URL do clone no README usa a grafia oficial TamyDB.
