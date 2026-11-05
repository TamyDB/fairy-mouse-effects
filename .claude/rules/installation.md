---
paths:
  - "packaging/**"
  - "tools/**"
  - "docs/INSTALACAO.md"
  - "docs/ACESSO_MOUSE.md"
---
# Instalação e sessão Linux

- Aplicativo e instalador por usuário executam sem sudo. `instalar.sh` usa sudo só para dnf das dependências e a regra de acesso; nunca roda como root.
- Regra genérica `71-fairy-mouse.rules` (decisão do usuário em 2026-11-05): qualquer interface com ID_INPUT_MOUSE, excluindo ID_INPUT_KEYBOARD. Nunca liberar teclados. Preservar ordem anterior a 73-seat-late. A regra antiga do Logitech fica em `packaging/udev/legacy/` só para remoção segura.
- uaccess concede acesso de sessão ao usuário, não apenas ao Fairy Mouse; sua ACL padrão é rw. O_RDONLY e filtro de eventos são propriedades do aplicativo, não da ACL.
- Não substituir uaccess por MODE=0666, grupo input ou dependência de eventN. Não apagar ACLs anteriores sem avaliar origem.
- Instalação copia o código: desenvolvimento no repositório não atualiza automaticamente a cópia instalada. Preserve recusas de sobrescrita de destinos alheios e remoção de unidade habilitada.
- Serviço usa sway-session.target e PartOf da sessão gráfica. Evite After=sway-session.target combinado com WantedBy nesse target para não criar ciclo.
- Preserve Restart=no para parada intencional. Não habilitar ou reiniciar serviços apenas por editar documentação.
- Ao mudar instaladores, testar staging em diretório temporário, caminhos com espaços, atualização e remoção. Conferir shell com bash -n e regra com udevadm verify; validação systemd real depende do host.
