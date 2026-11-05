#!/usr/bin/bash
# Instalação completa do Fairy Mouse para Fedora com Sway. Rode como usuário normal:
#   bash instalar.sh
# Também serve para atualizar: rode de novo depois de baixar uma versão nova.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
packages=(python3-gobject python3-cairo gtk4 gtk4-layer-shell)

step() { printf '\n==> %s\n' "$1"; }
fail() { printf '\nERRO: %s\n' "$1" >&2; exit 1; }

[[ $EUID -ne 0 ]] || fail "Não use sudo neste comando. Rode apenas: bash instalar.sh"
grep -qx 'ID=fedora' /etc/os-release || fail "Este instalador foi feito para o Fedora."
command -v sway >/dev/null || fail "O Sway não está instalado. O Fairy Mouse funciona somente no Sway."

echo "Fairy Mouse: instalação. A sua senha pode ser pedida."
echo "(É normal não aparecer nada enquanto você digita a senha.)"

step "1/4 Conferindo programas necessários"
missing=()
for package in "${packages[@]}"; do
    rpm -q "$package" >/dev/null 2>&1 || missing+=("$package")
done
if (( ${#missing[@]} )); then
    sudo dnf install -y "${missing[@]}"
else
    echo "Tudo já está instalado."
fi

step "2/4 Liberando o mouse para o brilho do clique"
sudo bash tools/install-mouse-access.sh

step "3/4 Instalando o Fairy Mouse"
systemctl --user stop fairy-mouse.service 2>/dev/null || true
/usr/bin/python3 tools/install-user.py >/dev/null
systemctl --user daemon-reload
systemctl --user enable fairy-mouse.service 2>/dev/null
echo "Instalado e configurado para ligar sozinho ao entrar no Sway."

step "4/4 Ligando os efeitos"
if [[ -z "${SWAYSOCK:-}" ]]; then
    echo "Você não está no Sway agora. Os efeitos vão ligar na próxima vez que entrar no Sway."
    exit 0
fi
systemctl --user import-environment WAYLAND_DISPLAY SWAYSOCK XDG_SESSION_TYPE XDG_CURRENT_DESKTOP
systemctl --user start fairy-mouse.service
sleep 2
if systemctl --user is-active --quiet fairy-mouse.service; then
    printf '\nPronto! Mova o mouse e clique com o botão esquerdo. ✨\n'
else
    echo "Os efeitos não ligaram. Mensagens recentes:" >&2
    journalctl --user -u fairy-mouse.service -n 15 --no-pager >&2 || true
    fail "Se aparecer que já existe uma instância, feche o Fairy Mouse aberto em outro terminal e rode de novo."
fi
