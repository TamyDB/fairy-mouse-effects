from io import BytesIO
import struct
import unittest

from fairy_mouse.wayland_probe import read_registry, request


class FakeConnection:
    def __init__(self, data):
        self.data = BytesIO(data)
        self.sent = b''

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        return self.data.read(min(size, 3))


def global_event(interface, version):
    name = interface.encode() + b'\0'
    padding = b'\0' * (-len(name) % 4)
    payload = struct.pack('=II', 10, len(name)) + name + padding + struct.pack('=I', version)
    return request(2, 0, payload)


class ProbeTests(unittest.TestCase):
    def test_registry_handles_fragmented_messages_and_versions(self):
        events = global_event('ext_image_copy_capture_manager_v1', 1)
        events += global_event('wl_output', 4) + global_event('wl_output', 3)
        events += request(3, 0, struct.pack('=I', 1))
        connection = FakeConnection(events)
        self.assertEqual(read_registry(connection),
                         {'ext_image_copy_capture_manager_v1': 1, 'wl_output': 4})
        self.assertEqual(connection.sent, request(1, 1, struct.pack('=I', 2)) +
                         request(1, 0, struct.pack('=I', 3)))

    def test_truncated_and_invalid_messages_fail(self):
        for data in (b'', struct.pack('=II', 2, 7 << 16), request(2, 0, b'\0' * 4),
                     request(1, 0, b'\0' * 4)):
            with self.subTest(data=data):
                with self.assertRaises(RuntimeError):
                    read_registry(FakeConnection(data))
