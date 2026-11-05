# Instalação do aplicativo e início opcional com o Sway

## Estado

O instalador copia o aplicativo para a área do usuário, sem dependência do diretório de desenvolvimento. Não altera udev, permissões de dispositivos, configuração principal do Sway ou início automático. O teste de persistência do acesso ao mouse após reboot foi adiado pelo usuário; continua pendente, assim como as medições de consumo.

A unidade de usuário usa `sway-session.target`, fornecido pelo Fedora Sway desta máquina. A integração padrão em `/etc/sway/config.d/10-systemd-session.conf` importa o ambiente gráfico antes de iniciar esse target e o encerra com o compositor. Uma configuração personalizada do Sway que omita essa integração precisa ser ajustada separadamente.

## Instalação completa

`bash instalar.sh`, na raiz, instala dependências via dnf, a regra de acesso ao mouse e o aplicativo, habilita o serviço e o inicia se houver sessão Sway. Rodar de novo atualiza. `bash desinstalar.sh` desfaz tudo menos os pacotes. As seções abaixo descrevem os passos individuais.

## Instalar sem sudo

Na raiz do projeto:

```bash
/usr/bin/python3 tools/install-user.py
systemctl --user daemon-reload
```

Arquivos instalados por padrão:

- `~/.local/share/fairy-mouse/`: cópia do pacote Python e README.
- `~/.local/bin/fairy-mouse`: comando usando `/usr/bin/python3`.
- `${XDG_CONFIG_HOME:-~/.config}/systemd/user/fairy-mouse.service`: unidade ainda desativada.

O serviço roda sem `--click-device` e lê todos os mouses liberados pela regra de acesso persistente. A instalação do aplicativo não concede esse acesso. Se `~/.local/bin` não estiver no PATH, use o caminho completo.

Para testar manualmente:

```bash
~/.local/bin/fairy-mouse --background
```

Para rodar supervisionado, fora do terminal, primeiro encerre a instância manual com Ctrl+C. Então, no terminal da sessão Sway:

```bash
systemctl --user import-environment WAYLAND_DISPLAY SWAYSOCK XDG_SESSION_TYPE XDG_CURRENT_DESKTOP
systemctl --user start fairy-mouse.service
systemctl --user status fairy-mouse.service
journalctl --user -u fairy-mouse.service -n 40 --no-pager
```

A importação é para a sessão atual, usando somente essas variáveis. Nas próximas sessões, a integração padrão do Fedora as importa. A unidade não contém caminhos para sockets de uma sessão antiga.

## Habilitar início automático — opcional

Verifique a integração e habilite somente se desejar:

```bash
systemctl --user is-active sway-session.target
systemctl --user enable fairy-mouse.service
```

Isso agenda o início para a próxima sessão Sway; não inicia imediatamente. Para iniciar agora, use `systemctl --user start fairy-mouse.service`. Não habilite outro mecanismo de autostart em paralelo. O bloqueio de instância continua protegendo contra duplicação, mas uma instância manual já aberta fará o serviço falhar ao iniciar.

`PartOf` vincula encerramento às sessões Sway/gráfica. SIGTERM é tratado pela aplicação; fechar a conexão gráfica também encerra o processo. `Restart=no` permite parar intencionalmente e evita ciclos de reinício em caso de falta de acesso ao display ou instância duplicada. Não há daemonização por fork ou processo root.

## Parar, desativar e atualizar

```bash
systemctl --user stop fairy-mouse.service
systemctl --user disable fairy-mouse.service
```

Parar atua agora; desativar remove o início nas próximas sessões. Para fazer ambos, use `disable --now`. Para atualizar a cópia instalada após editar o código:

```bash
systemctl --user stop fairy-mouse.service
/usr/bin/python3 tools/install-user.py
systemctl --user daemon-reload
systemctl --user start fairy-mouse.service
```

A cópia não acompanha automaticamente as alterações do repositório. O instalador atualiza somente seus destinos identificados por marcador e recusa substituir um comando/unidade não gerenciado. Personalizações da unidade devem ficar em drop-ins via `systemctl --user edit fairy-mouse.service`; o arquivo gerado é substituído na atualização. Nenhuma configuração personalizada do aplicativo é criada nesta etapa.

## Desinstalar

```bash
systemctl --user disable --now fairy-mouse.service
/usr/bin/python3 tools/install-user.py --remove
systemctl --user daemon-reload
```

A remoção recusa uma unidade ainda habilitada. Stop/desativação devem ser executados mesmo que a unidade esteja apenas rodando manualmente. A regra de acesso udev é independente e permanece instalada; para removê-la veja `ACESSO_MOUSE.md`. Drop-ins criados pelo usuário não são apagados. Não use sudo no instalador do aplicativo.

## Testes e limitações

O instalador aceita `--prefix` e `--config-home` para staging e testes. Testes executam o launcher instalado a partir de outro diretório, com espaços no caminho, verificam reinstalação/remoção e recusam sobrescrever arquivos alheios ou remover serviço habilitado. O serviço foi preparado com base na integração local do Fedora e na documentação systemd.

A sandbox bloqueou `systemd-analyze --user verify` em operações de socket. Para verificar no host, após instalar:

```bash
systemd-analyze --user verify "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/fairy-mouse.service"
```

O agente não iniciou/habilitou serviços. O usuário posteriormente confirmou funcionamento em segundo plano e habilitou o serviço com systemctl --user enable. Encerramento com a sessão e início na próxima sessão/reinicialização ainda precisam de confirmação. Os efeitos e a reconexão do mouse já foram validados anteriormente em execução manual.

Referência: [systemd — serviços da sessão gráfica](https://www.freedesktop.org/software/systemd/man/latest/systemd.special.html), além dos arquivos locais de integração do Fedora Sway citados acima.
