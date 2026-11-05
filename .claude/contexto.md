# Contexto vigente — Fairy Mouse

Atualizado na migração de documentação em 2026-11-04. Este é o resumo canônico de retomada. O histórico anterior está em `docs/HISTORICO_CONTEXTO.md`, sem carregamento automático integral.

## Objetivo e preferências

Fedora + Sway padrão, sem patches do compositor. Rastro de fada e brilho discreto no clique para máquinas antigas, com animações simples. Usuário aprovou o visual e quer operação em segundo plano. Manter README acessível a leigos.

## Confirmado pelo usuário

- Fedora 44, Sway 1.11, GTK 4, Gtk4LayerShell e Cairo disponíveis no Python do sistema.
- Rastro global sobre aplicações, brilho no botão esquerdo físico e alinhamento na ponta do cursor funcionam.
- Logitech Wireless Mouse reconhecido, com teclas extras na mesma interface.
- Acesso pela regra persistente recebeu cliques; desconectar/reconectar o mouse voltou a funcionar.
- Aplicativo roda em segundo plano; usuário executou `systemctl --user enable fairy-mouse.service` e confirmou habilitação.

Após reboot (2026-11-05), regra udev e acesso ao Logitech persistiram (observado). A sessão desse boot era o compositor umbriel, não Sway: o serviço, que depende de sway-session.target, ficou inactive. Início automático no Sway após login continua sem validação; uso no umbriel não é suportado nem testado.

## Operação atual

```bash
systemctl --user start fairy-mouse.service
systemctl --user stop fairy-mouse.service
systemctl --user status fairy-mouse.service --no-pager
systemctl --user is-enabled fairy-mouse.service
```

Instalação para leigos: `bash instalar.sh` (dnf das dependências, regra udev, cópia do usuário, enable e start se houver Sway). Rodar de novo atualiza. `bash desinstalar.sh` remove. `tools/install-user.py` sozinho continua preparando o serviço desabilitado. A cópia em `~/.local/share/fairy-mouse` é independente do repositório. README reescrito: parte leiga no topo, "Detalhes técnicos" abaixo. URL do clone: github.com/tamydb/fairy-mouse-effects.

Modo direto, com serviço parado: `/usr/bin/python3 -m fairy_mouse --background`. Encerrar com Ctrl+C. Não iniciar duas instâncias.

## Acesso ao mouse

Desde 2026-11-05, por decisão do usuário (instalar no computador da namorada, também Fedora + Sway, mouse desconhecido): regra genérica `packaging/udev/71-fairy-mouse.rules`, com uaccess para todo ID_INPUT_MOUSE e exclusão de ID_INPUT_KEYBOARD. O serviço não usa mais `--click-device`; o app auto-detecta mouses legíveis. A regra antiga do Logitech (046d/4054, symlink `/dev/input/fairy-mouse-logitech`) fica em `packaging/udev/legacy/` e o instalador a remove se estiver intacta. A regra genérica ainda não foi instalada nem testada em host real; nesta máquina a antiga continua em /etc.

uaccess dá ACL rw ao usuário da sessão, não exclusiva ao app; o app abre O_RDONLY. Não usar grupo input ou GUI como root. ACLs manuais antigas nos nós ELAN não foram removidas.

## Correções essenciais preservadas

- Preload nativo de Gtk4LayerShell antes de GTK/GDK por GI, com backend Wayland para o overlay.
- Zona exclusiva -1, quatro âncoras e região de entrada vazia. Zona 0 respeitava painéis e deslocava/comprimia o desenho.
- Posição EXT já representa hotspot em coordenadas transformadas: não subtrair hotspot ou aplicar rotação novamente.
- Aceitar mouse composto com KEY_ENTER; rejeitá-lo escondia o Logitech. Máscara obrigatória por descritor permite apenas BTN_LEFT e sincronização antes da leitura.
- Snapshot do cursor válido em repouso; invalidar ao sair/remover saída. Não substituir por hotspot fora dos limites de outro monitor.
- Reabrir leitor quando a identidade do nó de um caminho estável mudar. Reconexão usa eventos, sem varredura periódica.

## Validação e pendências

Suíte executada no Claude Code em 2026-11-05: 53 testes, 53 aprovados, nenhum ignorado. Validações reais acima foram relatadas pelo usuário; testes de protocolo/dispositivos também usam simuladores. A sessão anterior não acessava display, /dev/input ou bus de logind. Verifique o ambiente atual antes de declarar um bloqueio.

Por decisão do usuário, adiar medições de consumo e teste após reboot. Limites atuais: 48 partículas e 30 FPS por padrão; não são benchmarks. Não suportados: tap-to-click, remapeamentos e cliques virtuais. Vários monitores, escalas e encerramento completo com a sessão ainda precisam de testes reais mais amplos.

Publicação pendente: criar `fairy-mouse-effects` no GitHub e enviar código/documentação. Não houve confirmação de criação ou push. A integração GitHub não estava conectada e a pasta .git era vazia/somente leitura na sessão anterior. Um commit foi preparado apenas em /tmp; não presumir que esse artefato temporário ainda exista ou que seja o histórico do workspace. A visibilidade privada foi proposta pelo assistente, não confirmada explicitamente pelo usuário. Verificar autenticação, repositório e histórico reais antes de publicar.

Próxima melhoria funcional sugerida: salvar cor, intensidade e FPS em arquivo. Ainda não implementada nem iniciada; o usuário priorizou a migração da documentação para o Claude.
