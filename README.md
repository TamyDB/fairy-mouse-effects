# Fairy Mouse ✨

Um toque de magia no seu mouse: um **rastro de fada** quando você move o cursor e um **brilho** quando aperta o botão esquerdo. Ele fica ligado em segundo plano, sem janela, e liga sozinho quando você entra no computador.

## Funciona no meu computador?

Funciona se o computador usa **Fedora com Sway**. Serve qualquer mouse comum, com ou sem fio.

No touchpad (a área de toque do notebook), o rastro aparece, mas o brilho só acontece ao apertar o botão de verdade, não com um toque leve.

## Como instalar

Você vai precisar abrir o **Terminal** e colar dois comandos. A instalação é feita uma vez só.

**1.** Abra o Terminal. No Sway, o atalho costuma ser **Super + Enter** (Super é a tecla com o símbolo do Windows).

**2.** Copie a linha abaixo, cole no Terminal com **Ctrl + Shift + V** e aperte **Enter**. Ela baixa o Fairy Mouse para a sua pasta pessoal:

```bash
git clone https://github.com/TamyDB/fairy-mouse-effects.git ~/fairy-mouse
```

**3.** Agora cole esta linha e aperte **Enter**:

```bash
bash ~/fairy-mouse/instalar.sh
```

O instalador vai pedir **a sua senha** do computador. **Enquanto você digita, nada aparece na tela. Isso é normal.** Digite a senha e aperte Enter.

**4.** Espere aparecer **"Pronto!"**. Mova o mouse e clique: o rastro e o brilho já devem aparecer. Pode fechar o Terminal.

Daqui para a frente, os efeitos ligam sozinhos sempre que você entrar no Sway.

## Ligar e desligar

Cole no Terminal o comando do que você quer fazer:

| Quero... | Comando |
| --- | --- |
| Desligar agora | `systemctl --user stop fairy-mouse.service` |
| Ligar de novo | `systemctl --user start fairy-mouse.service` |
| Que pare de ligar sozinho | `systemctl --user disable --now fairy-mouse.service` |
| Que volte a ligar sozinho | `systemctl --user enable --now fairy-mouse.service` |

Desligar os efeitos não afeta o mouse, que continua funcionando normalmente.

## Deu algum problema?

- **Apareceu "ERRO" durante a instalação:** leia a mensagem logo acima. Se não entender, tire uma foto ou copie o texto e mande para quem te passou o Fairy Mouse.
- **O rastro aparece, mas o clique não brilha:** desconecte o mouse (ou o receptor USB), conecte de novo e teste outra vez.
- **Nada aparece:** rode `bash ~/fairy-mouse/instalar.sh` de novo. Se continuar, mande a saída deste comando para quem te ajudou:

  ```bash
  journalctl --user -u fairy-mouse.service -n 40 --no-pager
  ```

## Atualizar

Quando houver uma versão nova:

```bash
git -C ~/fairy-mouse pull
bash ~/fairy-mouse/instalar.sh
```

## Desinstalar

```bash
bash ~/fairy-mouse/desinstalar.sh
```

Depois, se quiser, apague a pasta `~/fairy-mouse`.

---

# Detalhes técnicos

O que vem abaixo é para quem quer entender ou mexer no projeto. Ninguém precisa ler isto só para usar o Fairy Mouse.

## Compatibilidade e estado

- Testado no Fedora 44 com Sway 1.11, com um Logitech Wireless Mouse. Rastro, brilho no clique físico, alinhamento com o cursor, reconexão do mouse e segundo plano foram validados no uso real. Ainda não foram testados na prática: outros mouses com a regra genérica, início automático depois de um novo login, vários monitores e escalas diferentes.
- O desenho é feito com `wlr-layer-shell`, e a posição vem dos metadados de cursor `ext-image-copy-capture`. Por isso, **GNOME não é suportado**. Outros compositores com esses protocolos podem funcionar, mas não foram testados e o serviço só inicia junto com `sway-session.target`.
- O app lê apenas o botão esquerdo físico. Não suporta toque leve para clicar no touchpad, remapeamentos nem cliques virtuais.
- Padrões: até 48 partículas no total e 30 FPS. A animação para quando não há partículas. O consumo de CPU, memória e GPU ainda não foi medido.

## O que o `instalar.sh` faz

1. Recusa rodar como root e confere se o sistema é Fedora e se o Sway está instalado.
2. Instala, com `sudo dnf`, os pacotes que faltarem entre `python3-gobject`, `python3-cairo`, `gtk4` e `gtk4-layer-shell`.
3. Instala a regra de acesso ao mouse com `sudo bash tools/install-mouse-access.sh` (veja abaixo).
4. Instala o aplicativo para o usuário com `/usr/bin/python3 tools/install-user.py` e depois roda `daemon-reload` e `enable`.
5. Se estiver numa sessão Sway, importa o ambiente gráfico e inicia o serviço. Fora do Sway, o serviço fica habilitado para a próxima sessão.

Rodar de novo é seguro e serve para atualizar: o script para o serviço antes de copiar os arquivos. O `sudo` só é usado nos passos 2 e 3.

O `desinstalar.sh` desabilita o serviço, remove a cópia instalada e remove a regra udev. Os pacotes do dnf continuam instalados.

### Instalação manual, passo a passo

Os comandos abaixo devem ser rodados na pasta do projeto e equivalem ao `instalar.sh`:

```bash
/usr/bin/python3 -m fairy_mouse --diagnose
sudo dnf install python3-gobject python3-cairo gtk4 gtk4-layer-shell
sudo bash tools/install-mouse-access.sh
/usr/bin/python3 tools/install-user.py
systemctl --user daemon-reload
systemctl --user enable fairy-mouse.service
systemctl --user import-environment WAYLAND_DISPLAY SWAYSOCK XDG_SESSION_TYPE XDG_CURRENT_DESKTOP
systemctl --user start fairy-mouse.service
```

`active` quer dizer "rodando agora" e `enabled` quer dizer "configurado para iniciar nas próximas sessões". Para conferir, use `systemctl --user is-active fairy-mouse.service` e `is-enabled`.

Arquivos instalados:

- `~/.local/share/fairy-mouse/`: uma cópia do código, que não acompanha o repositório.
- `~/.local/bin/fairy-mouse`: o comando.
- `~/.config/systemd/user/fairy-mouse.service`: o serviço de usuário.
- `/etc/udev/rules.d/71-fairy-mouse.rules`: a regra de acesso ao mouse.

## Acesso ao mouse

O brilho precisa ler o botão do mouse em `/dev/input`, que normalmente só o root pode ler. A regra `packaging/udev/71-fairy-mouse.rules` marca com `uaccess` **toda interface classificada como mouse** (`ID_INPUT_MOUSE=1`) e exclui interfaces de teclado. Com isso, o systemd-logind dá ao usuário da sessão local ativa uma ACL sobre esses dispositivos. A regra não usa o grupo `input` nem `MODE=0666`.

Isso dá acesso ao usuário, e não apenas ao app. O Fairy Mouse abre os dispositivos somente para leitura e filtra apenas `BTN_LEFT`. Sem `--click-device`, ele observa todos os mouses que consegue ler e acompanha quando um é conectado ou removido.

A versão anterior usava uma regra restrita ao Logitech (`packaging/udev/legacy/`). O instalador remove essa regra automaticamente se ela não tiver sido alterada. Detalhes em [Acesso ao mouse](docs/ACESSO_MOUSE.md).

## Desenvolvimento

Use sempre `/usr/bin/python3`, porque o Python do PATH pode ser de outro ambiente.

```bash
/usr/bin/python3 -m fairy_mouse --diagnose      # relatório, não liga efeitos
/usr/bin/python3 -m fairy_mouse --demo          # janela de teste do visual
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m compileall -q fairy_mouse main.py tests tools
```

Para rodar direto no terminal, pare o serviço antes para não haver duas instâncias:

```bash
systemctl --user stop fairy-mouse.service
/usr/bin/python3 -m fairy_mouse --background
```

Encerre com Ctrl+C. As opções `--fps`, `--particles`, `--intensity`, `--color` e `--click-device` ajustam a execução, por exemplo:

```bash
/usr/bin/python3 -m fairy_mouse --demo --fps 20 --particles 24 --intensity 0.5 --color '#FFD5F5'
```

Depois de mudar o código, rode `bash instalar.sh` de novo para atualizar a cópia instalada.

## Documentação técnica

- [Instalação e serviço](docs/INSTALACAO.md): instalação por usuário e ciclo da sessão Sway.
- [Acesso ao mouse](docs/ACESSO_MOUSE.md): regra udev e escopo das permissões.
- [Integração](docs/INTEGRACAO.md): Wayland, desenho e leitura de clique.
- [Processo](docs/PROCESSO.md): histórico de implementação e validação.
- [CLAUDE.md](CLAUDE.md), [contexto atual](.claude/contexto.md) e [guia do Claude Code](docs/CLAUDE_CODE.md): desenvolvimento assistido.
