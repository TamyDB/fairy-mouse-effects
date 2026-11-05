# Acesso persistente ao mouse

## Regra genérica (atual)

A regra `packaging/udev/71-fairy-mouse.rules` aplica `TAG+="uaccess"` a todo nó `event*` com `ID_INPUT_MOUSE=1`, excluindo `ID_INPUT_KEYBOARD=1`. Ela vale para qualquer mouse, com fio, sem fio ou Bluetooth, e foi adotada por decisão do usuário em 2026-11-05 para facilitar a instalação em outros computadores. Teclados e as interfaces de teclado de receptores combinados ficam de fora. Touchpads normalmente são marcados como `ID_INPUT_TOUCHPAD` e não `ID_INPUT_MOUSE`, então não são cobertos.

`uaccess` delega ao systemd-logind a ACL para o usuário da sessão local ativa do seat. O arquivo começa com `71-` para ser processado antes de `73-seat-late.rules`. A regra não cria grupos e não define MODE=0666. A política padrão de uaccess dá leitura e escrita ao usuário ativo. O Fairy Mouse abre o nó somente com O_RDONLY e limita sua própria fila a BTN_LEFT. A autorização vale para o usuário, não só para o aplicativo: as máscaras não restringem outros processos desse usuário. A remoção da ACL não fecha um descritor já aberto.

Sem `--click-device`, o aplicativo seleciona os nós com BTN_LEFT e eixos X/Y, abre os que consegue ler e refaz a busca quando `/dev/input` muda, sem varredura periódica. Nós sem permissão geram um aviso no log e são ignorados.

## Instalação

O `instalar.sh` já faz isso. Para fazer manualmente, na raiz do projeto:

```bash
cat packaging/udev/71-fairy-mouse.rules
sudo bash tools/install-mouse-access.sh
/usr/bin/python3 -m fairy_mouse --diagnose
```

O instalador verifica a sintaxe, copia a regra para `/etc/udev/rules.d`, recarrega as regras e reprocessa os dispositivos de mouse. Ele recusa sobrescrever uma regra diferente ou um symlink no destino. Reexecutar com a mesma regra é permitido.

No diagnóstico, `persistent_mouse_access.readable_devices` lista os nós legíveis. A presença do arquivo de regra, sozinha, não prova que ela foi aplicada. Se o mouse não aparecer, reconecte-o e confirme que a sessão local está ativa com `loginctl session-status`.

## Regra antiga do Logitech

A versão anterior instalava `71-fairy-mouse-logitech.rules`. Essa regra identificava só o Logitech Wireless Mouse (input 046d/4054) e criava `/dev/input/fairy-mouse-logitech`. O arquivo agora fica em `packaging/udev/legacy/` apenas para comparação. Ao instalar ou remover, o script apaga a regra antiga de `/etc/udev/rules.d` se ela for idêntica à original e avisa se ela tiver sido alterada. O symlink deixa de ser criado. Use `--click-device /dev/input/eventN` se quiser limitar o app a um mouse.

## Remover

```bash
sudo bash tools/install-mouse-access.sh --remove
```

Depois, reconecte o mouse para recriar os nós com a política padrão. A remoção não apaga ACLs manuais anteriores, como as do ELAN na máquina de desenvolvimento, nem encerra descritores já abertos.

## Estado de validação

A regra genérica foi aprovada por `udevadm verify`. **Ainda não foi testada em host real.** O usuário validou a regra antiga do Logitech: cliques recebidos, reconexão física e persistência após o reboot de 2026-11-05. A seleção automática de candidatos é coberta por testes simulados.

Referências: [udev — regras e atributos de pais](https://www.freedesktop.org/software/systemd/man/latest/udev.html), [logind — seats e uaccess](https://www.freedesktop.org/software/systemd/man/latest/sd-login.html), e arquivos locais `/usr/lib/udev/rules.d/70-uaccess.rules` e `73-seat-late.rules`.
