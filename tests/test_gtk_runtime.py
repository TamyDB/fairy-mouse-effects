import os
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from fairy_mouse import gtk_runtime


class GtkRuntimeTests(unittest.TestCase):
    def test_preload_before_gi_and_force_wayland_for_background(self):
        events = []
        gi = Mock()
        gi.require_version.side_effect = lambda *args: events.append(('require', args[0]))
        def preload():
            self.assertEqual(os.environ['GDK_BACKEND'], 'wayland')
            events.append(('preload', None))
        def import_module(name):
            events.append(('import', name))
            return name
        with patch.dict(os.environ, {'GDK_BACKEND': 'x11'}), \
             patch.dict(sys.modules, {'gi': gi}), \
             patch.object(gtk_runtime, 'preload_layer_shell', side_effect=preload), \
             patch.object(gtk_runtime.importlib, 'import_module', side_effect=import_module):
            modules = gtk_runtime.load_background_gtk()
        self.assertEqual(events[0], ('preload', None))
        self.assertEqual(len(modules), 5)
        self.assertEqual(events[1], ('require', 'Gtk'))

    def test_versioned_library_is_cached_and_loads_globally(self):
        library = Mock()
        with patch.object(gtk_runtime, '_layer_library', None), \
             patch.object(gtk_runtime, 'find_library', return_value='libgtk4-layer-shell.so.0'), \
             patch.object(gtk_runtime.ctypes, 'CDLL', return_value=library) as loader:
            self.assertIs(gtk_runtime.preload_layer_shell(), library)
            self.assertIs(gtk_runtime.preload_layer_shell(), library)
            loader.assert_called_once_with('libgtk4-layer-shell.so.0', mode=gtk_runtime.ctypes.RTLD_GLOBAL)

    def test_missing_native_library_reports_specific_error(self):
        with patch.object(gtk_runtime, '_layer_library', None), \
             patch.object(gtk_runtime, 'find_library', return_value=None), \
             patch.object(gtk_runtime.ctypes, 'CDLL', side_effect=OSError('not found')):
            with self.assertRaisesRegex(RuntimeError, 'Gtk4LayerShell'):
                gtk_runtime.preload_layer_shell()

    @unittest.skipUnless(sys.executable == '/usr/bin/python3', 'Requer bindings GTK do sistema.')
    def test_real_loading_in_fresh_process_without_display(self):
        code = '''
import sys
from fairy_mouse.gtk_runtime import preload_layer_shell, load_background_gtk
assert 'gi.repository.Gtk' not in sys.modules
library = preload_layer_shell()
assert 'gi.repository.Gtk' not in sys.modules
Gdk, Gio, GLib, Gtk, Layer = load_background_gtk()
assert library._name
assert Layer.get_major_version() >= 1
print(library._name)
'''
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
