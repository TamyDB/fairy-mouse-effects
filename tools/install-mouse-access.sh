#!/usr/bin/bash
# Install only the reviewed device access rule; never starts the GUI as root.
set -euo pipefail
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
rule_name=71-fairy-mouse.rules
source_rule="$script_dir/../packaging/udev/$rule_name"
target_rule="/etc/udev/rules.d/$rule_name"
# Regra antiga, restrita ao Logitech do desenvolvimento; substituída pela genérica.
legacy_source="$script_dir/../packaging/udev/legacy/71-fairy-mouse-logitech.rules"
legacy_target=/etc/udev/rules.d/71-fairy-mouse-logitech.rules
mode=${1:---install}
if [[ $# -gt 1 || ( "$mode" != --install && "$mode" != --remove ) ]]; then
    echo "Uso: sudo bash tools/install-mouse-access.sh [--install|--remove]" >&2
    exit 2
fi
if [[ $EUID -ne 0 ]]; then
    echo "Execute este instalador com sudo; o aplicativo deve continuar como usuário normal." >&2
    exit 1
fi
command -v udevadm >/dev/null
if [[ -e "$target_rule" || -L "$target_rule" ]]; then
    if [[ -L "$target_rule" ]] || ! cmp -s -- "$source_rule" "$target_rule"; then
        echo "Regra existente diferente: $target_rule. Revise-a manualmente antes de prosseguir." >&2
        exit 1
    fi
fi
remove_legacy() {
    if [[ -f "$legacy_target" && ! -L "$legacy_target" ]] && cmp -s -- "$legacy_source" "$legacy_target"; then
        rm -f -- "$legacy_target"
        echo "Regra antiga do Logitech removida: $legacy_target"
    elif [[ -e "$legacy_target" || -L "$legacy_target" ]]; then
        echo "Aviso: $legacy_target foi alterada e não será removida; revise-a manualmente." >&2
    fi
}
if [[ "$mode" == --remove ]]; then
    rm -f -- "$target_rule"
    remove_legacy
    udevadm control --reload-rules
    echo "Regra removida. Reconecte o mouse para recriar os nós e descartar ACLs anteriores."
    echo "ACLs manuais antigas não são removidas por este script."
else
    udevadm verify "$source_rule"
    install -o root -g root -m 0644 -- "$source_rule" "$target_rule"
    remove_legacy
    udevadm control --reload-rules
    udevadm trigger --action=change --subsystem-match=input --property-match=ID_INPUT_MOUSE=1
    udevadm settle --timeout=10
    echo "Regra instalada. Execute --diagnose sem sudo para conferir a leitura do mouse."
    echo "Se o clique não for lido, desconecte e reconecte o mouse na sessão local ativa."
fi
