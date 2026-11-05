#!/usr/bin/bash
# Remove o Fairy Mouse e a liberação do mouse. Rode como usuário normal:
#   bash desinstalar.sh
# Os programas instalados pelo dnf (GTK etc.) são mantidos.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ $EUID -eq 0 ]]; then
    echo "Não use sudo neste comando. Rode apenas: bash desinstalar.sh" >&2
    exit 1
fi
systemctl --user disable --now fairy-mouse.service 2>/dev/null || true
/usr/bin/python3 tools/install-user.py --remove >/dev/null
systemctl --user daemon-reload
echo "Aplicativo removido. A sua senha pode ser pedida para remover a liberação do mouse."
sudo bash tools/install-mouse-access.sh --remove
echo "Fairy Mouse desinstalado."
