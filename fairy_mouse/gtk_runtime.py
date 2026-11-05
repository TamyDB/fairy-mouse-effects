"""Carregamento de Gtk4LayerShell antes de GTK/libwayland, conforme upstream."""
import ctypes
from ctypes.util import find_library
import importlib
import os

_layer_library = None


def preload_layer_shell():
    global _layer_library
    if _layer_library is None:
        name = find_library('gtk4-layer-shell') or 'libgtk4-layer-shell.so.0'
        try:
            _layer_library = ctypes.CDLL(name, mode=ctypes.RTLD_GLOBAL)
        except OSError as exc:
            raise RuntimeError(f'Não foi possível carregar Gtk4LayerShell ({name}): {exc}') from exc
    return _layer_library


def load_background_gtk():
    # Precisa ocorrer antes de qualquer import GI que possa carregar GTK/Wayland.
    os.environ['GDK_BACKEND'] = 'wayland'
    preload_layer_shell()
    import gi
    for namespace, version in (('Gtk', '4.0'), ('Gdk', '4.0'), ('Gtk4LayerShell', '1.0')):
        gi.require_version(namespace, version)
    return tuple(importlib.import_module(f'gi.repository.{name}')
                 for name in ('Gdk', 'Gio', 'GLib', 'Gtk', 'Gtk4LayerShell'))
