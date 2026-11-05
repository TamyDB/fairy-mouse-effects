"""Inspeção somente de leitura; não captura entrada nem altera o compositor."""
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def diagnose():
    checks = {}
    from .gtk_runtime import preload_layer_shell
    try:
        library = preload_layer_shell()
        checks['layer_shell_preloaded'] = True
        checks['layer_shell_library'] = library._name
    except RuntimeError as exc:
        checks['layer_shell_preloaded'] = False
        checks['layer_shell_load_error'] = str(exc)
    checks['gdk_backend_environment'] = os.environ.get('GDK_BACKEND')
    checks['wayland_session'] = os.environ.get('XDG_SESSION_TYPE') == 'wayland'
    checks['wayland_display_defined'] = bool(os.environ.get('WAYLAND_DISPLAY'))
    for module in ('gi', 'cairo'):
        try:
            importlib.import_module(module)
            checks[module] = True
        except ImportError:
            checks[module] = False
    if checks['gi']:
        import gi
        for namespace, version in [('Gtk', '4.0'), ('Gtk4LayerShell', '1.0')]:
            try:
                gi.require_version(namespace, version)
                importlib.import_module(f'gi.repository.{namespace}')
                checks[namespace] = True
            except (ImportError, ValueError):
                checks[namespace] = False
    checks['swaymsg'] = bool(shutil.which('swaymsg'))
    checks['sway_connected'] = False
    if checks['swaymsg'] and os.environ.get('SWAYSOCK'):
        try:
            result = subprocess.run(
                ['swaymsg', '-t', 'get_version', '-r'], capture_output=True,
                text=True, timeout=3, check=False)
            if result.returncode == 0:
                checks['sway_version'] = json.loads(result.stdout).get('human_readable')
                checks['sway_connected'] = True
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass
    from .wayland_probe import REQUIRED, probe
    try:
        protocols = probe()
        checks['wayland_registry_connected'] = True
        checks['layer_shell_protocol_version'] = protocols.get('zwlr_layer_shell_v1', 0)
        checks['cursor_metadata_protocols'] = {name: protocols.get(name, 0) for name in REQUIRED}
        checks['cursor_metadata_candidate'] = all(name in protocols for name in REQUIRED)
    except (OSError, RuntimeError, UnicodeError) as exc:
        checks['wayland_registry_connected'] = False
        checks['layer_shell_protocol_version'] = None
        checks['cursor_metadata_probe_error'] = str(exc)
        checks['cursor_metadata_candidate'] = None
    checks['cursor_tracking_implemented'] = True
    checks['global_tracking_available'] = None
    from .clicks import diagnose_clicks
    checks['click_detection'] = diagnose_clicks()
    checks['persistent_mouse_access'] = {
        'rule_present': Path('/etc/udev/rules.d/71-fairy-mouse.rules').is_file(),
        'legacy_logitech_rule_present':
            Path('/etc/udev/rules.d/71-fairy-mouse-logitech.rules').is_file(),
        'readable_devices': [device['path'] for device in checks['click_detection']['devices']
                             if device['readable']],
    }
    checks['global_click_tracking_available'] = checks['click_detection']['available']
    checks['background_mode'] = 'ext_cursor_metadata'
    checks['note'] = ('Cliente de posição implementado; valide com --background. '
                      'Este diagnóstico não inicia sessões de cursor; disponibilidade funcional '
                      'não foi medida. Cliques físicos dependem de leitura do mouse; '
                      'toque para clicar de touchpad ainda não suportado.')
    return checks
