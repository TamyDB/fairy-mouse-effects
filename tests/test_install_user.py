import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('install_user', SOURCE / 'tools/install-user.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_installed_copy_runs_outside_repository_and_removes(self):
        with tempfile.TemporaryDirectory(prefix='fairy install ') as root:
            prefix, config = Path(root) / 'local', Path(root) / 'config'
            launcher, service = installer.install(prefix, config)
            self.assertIn('WantedBy=sway-session.target', service.read_text())
            self.assertIn('Restart=no', service.read_text())
            result = subprocess.run([str(launcher), '--help'], cwd=root,
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--background', result.stdout)
            self.assertFalse((service.parent / 'sway-session.target.wants').exists())
            installer.install(prefix, config)  # Reinstalação permitida.
            installer.install(prefix, config, remove=True)
            self.assertFalse(launcher.exists())
            self.assertFalse(service.exists())
            self.assertFalse((prefix / 'share/fairy-mouse').exists())

    def test_unrelated_launcher_is_preserved_before_any_copy(self):
        with tempfile.TemporaryDirectory() as root:
            prefix, config = Path(root) / 'local', Path(root) / 'config'
            (prefix / 'bin').mkdir(parents=True)
            launcher = prefix / 'bin/fairy-mouse'
            launcher.write_text('user content')
            with self.assertRaises(RuntimeError):
                installer.install(prefix, config)
            self.assertEqual(launcher.read_text(), 'user content')
            self.assertFalse((prefix / 'share').exists())

    def test_enabled_service_must_be_disabled_before_uninstall(self):
        with tempfile.TemporaryDirectory() as root:
            prefix, config = Path(root) / 'local', Path(root) / 'config'
            launcher, service = installer.install(prefix, config)
            wants = service.parent / 'sway-session.target.wants'
            wants.mkdir()
            (wants / service.name).symlink_to(service)
            with self.assertRaises(RuntimeError):
                installer.install(prefix, config, remove=True)
            self.assertTrue(launcher.exists())
            self.assertTrue(service.exists())

    def test_systemd_path_escaping_has_no_raw_line_or_expansion(self):
        quoted = installer.systemd_quote('/tmp/path space/"%x$HOME\nrun')
        self.assertNotIn('\n', quoted)
        self.assertIn('%%x$$HOME', quoted)
        self.assertIn('\\"', quoted)
        self.assertIn('\\n', quoted)
