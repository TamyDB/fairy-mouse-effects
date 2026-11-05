import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from fairy_mouse.runtime import event_socket, runtime_directory, send_message


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fm-')
        self.addCleanup(self.temp.cleanup)
        env = patch.dict(os.environ, {'XDG_RUNTIME_DIR': self.temp.name})
        env.start()
        self.addCleanup(env.stop)

    def test_runtime_directory_is_private(self):
        path = runtime_directory()
        self.assertEqual(path.stat().st_mode & 0o777, 0o700)

    def test_insecure_runtime_directory_is_rejected(self):
        path = Path(self.temp.name) / 'fairy-mouse'
        path.mkdir(mode=0o755)
        path.chmod(0o755)
        with self.assertRaises(RuntimeError):
            runtime_directory()

    def test_missing_runtime_is_rejected(self):
        with patch.dict(os.environ, {'XDG_RUNTIME_DIR': ''}):
            with self.assertRaises(RuntimeError):
                runtime_directory()

    def test_single_instance_transport_cleanup_and_restart(self):
        try:
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            with probe:
                probe.bind(str(Path(self.temp.name) / 'probe'))
        except PermissionError:
            self.skipTest('Sandbox bloqueia criação de sockets UNIX; validar fora dela.')
        endpoint = runtime_directory() / 'events.sock'
        with event_socket() as server:
            with self.assertRaisesRegex(RuntimeError, 'já está'):
                with event_socket():
                    pass
            self.assertTrue(endpoint.exists())
            send_message(b'{"version":1,"type":"stop"}')
            self.assertIn(b'stop', server.recv(1024))
        self.assertFalse(endpoint.exists())
        with event_socket():
            self.assertTrue(endpoint.exists())

    def test_missing_instance_reports_error(self):
        try:
            send_message(b'{}')
        except PermissionError:
            self.skipTest('Sandbox bloqueia sockets UNIX.')
        except RuntimeError as exc:
            self.assertIn('Nenhuma instância', str(exc))
        else:
            self.fail('Ausência de instância deveria gerar erro.')

    def test_real_lock_excludes_second_instance_without_socket_support(self):
        # Transporte simulado; o flock e a limpeza de caminhos são reais.
        from unittest.mock import MagicMock
        server = MagicMock()
        server.bind.side_effect = lambda name: Path(name).touch(mode=0o600)
        with patch('fairy_mouse.runtime.socket.socket', return_value=server):
            with event_socket():
                with self.assertRaisesRegex(RuntimeError, 'já está'):
                    with event_socket():
                        pass
                self.assertTrue((runtime_directory() / 'events.sock').exists())
            self.assertFalse((runtime_directory() / 'events.sock').exists())
            with event_socket():
                self.assertTrue((runtime_directory() / 'events.sock').exists())
