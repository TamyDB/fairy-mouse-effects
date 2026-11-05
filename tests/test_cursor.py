import struct
import unittest

from fairy_mouse.cursor import (CursorClient, CursorPosition, LatestPosition, Output,
                                read_string, string, uints)
from fairy_mouse.wayland_probe import HEADER, REQUIRED, request


class FakeCompositor:
    """Servidor de protocolo em memória, incluindo respostas às associações."""
    def __init__(self, missing=False, seat='seat0'):
        self.queue = bytearray()
        self.requests = []
        self.bound = {}
        self.closed = False
        self.missing = missing
        self.seat = seat

    def settimeout(self, timeout):
        pass

    def shutdown(self, how):
        pass

    def close(self):
        self.closed = True

    def event(self, object_id, opcode, payload=b''):
        self.queue.extend(request(object_id, opcode, payload))

    def sendall(self, data):
        offset = 0
        while offset < len(data):
            object_id, word = HEADER.unpack_from(data, offset)
            size, opcode = word >> 16, word & 0xffff
            payload = data[offset + 8:offset + size]
            self.requests.append((object_id, opcode, payload))
            offset += size
            if object_id == 1 and opcode == 1:
                registry = struct.unpack('=I', payload)[0]
                interfaces = [(REQUIRED[0], 1), (REQUIRED[1], 1), ('wl_output', 4), ('wl_seat', 5)]
                for global_id, (interface, version) in enumerate(interfaces, 10):
                    if self.missing and interface == REQUIRED[0]:
                        continue
                    self.event(registry, 0, uints(global_id) + string(interface) + uints(version))
            elif object_id == 1 and opcode == 0:
                callback = struct.unpack('=I', payload)[0]
                self.event(callback, 0, uints(1))
                self.event(1, 1, uints(callback))
            elif object_id == 2 and opcode == 0:
                interface, at = read_string(payload, 4)
                version, new_id = struct.unpack_from('=II', payload, at)
                self.bound[new_id] = interface
                if interface == 'wl_output':
                    geometry = struct.pack('=iiiii', 0, 0, 300, 200, 0)
                    geometry += string('Example') + string('Display') + struct.pack('=i', 0)
                    self.event(new_id, 0, geometry)
                    self.event(new_id, 1, struct.pack('=Iiii', 1, 1920, 1080, 60000))
                    self.event(new_id, 4, string('eDP-1'))
                    self.event(new_id, 2)
                elif interface == 'wl_seat':
                    self.event(new_id, 0, uints(3))
                    self.event(new_id, 1, string(self.seat))
            elif self.bound.get(object_id) == REQUIRED[0] and opcode == 1:
                cursor, source, pointer = struct.unpack('=III', payload)
                self.event(cursor, 0)
                self.event(cursor, 2, struct.pack('=ii', 960, 540))

    def recv(self, size):
        if not self.queue:
            return b''
        size = min(size, 3, len(self.queue))
        chunk = bytes(self.queue[:size])
        del self.queue[:size]
        return chunk


class CursorTests(unittest.TestCase):
    def test_handshake_and_real_protocol_position_without_image_requests(self):
        server = FakeCompositor()
        positions = []
        client = CursorClient(positions.append, connection=server).connect()
        self.assertEqual(positions, [CursorPosition('eDP-1', 960, 540, 1920, 1080)])
        self.assertTrue(client.pointer)
        # Não há bind de teclado, shm ou superfície; o manager só cria sessão de cursor.
        manager = client.managers[REQUIRED[0]][1]
        self.assertEqual([op for obj, op, _ in server.requests if obj == manager], [1])
        self.assertFalse(any(interface in ('wl_shm', 'wl_compositor')
                             for interface in server.bound.values()))
        client.close()
        self.assertTrue(server.closed)

    def test_absent_protocol_or_wrong_seat_fails_and_closes(self):
        for server in (FakeCompositor(missing=True), FakeCompositor(seat='other')):
            with self.subTest(server=server):
                with self.assertRaises(RuntimeError):
                    CursorClient(lambda _: None, connection=server).connect()
                self.assertTrue(server.closed)

    def test_removing_output_destroys_sessions_and_stops_positions(self):
        server = FakeCompositor()
        positions = []
        client = CursorClient(positions.append, connection=server).connect()
        output = client.outputs[12]
        client.global_removed(12)
        count = len(positions)
        client.handle(output.cursor, 2, struct.pack('=ii', 100, 100))
        self.assertEqual(len(positions), count)
        self.assertNotIn(12, client.outputs)
        self.assertTrue(all((obj, 0, b'') in server.requests for obj in
                            (output.cursor, output.source, output.object_id)))
        client.close()

    def test_cursor_leave_ignores_stale_positions(self):
        client = CursorClient(lambda _: self.fail('Posição após leave'))
        output = Output(12, 20, name='eDP-1', width=1920, height=1080, inside=True)
        client.objects[30] = ('cursor', output)
        client.handle(30, 1, b'')
        client.handle(30, 2, struct.pack('=ii', 1, 1))

    def test_scale_fractional_rotation_and_edge_clipping(self):
        self.assertEqual(CursorPosition('DP-1', 960, 540, 1920, 1080).logical(1280, 720),
                         (640, 360))
        for transform in range(8):
            output = Output(1, 2, width=1920, height=1080, transform=transform)
            expected = (1080, 1920) if transform % 2 else (1920, 1080)
            position = output.position(expected[0] // 2, expected[1] // 2)
            self.assertEqual((position.pixel_width, position.pixel_height), expected)
            self.assertEqual(position.logical(800, 600), (400, 300))
        for x, y in [(-1, 0), (0, -1), (1920, 0), (0, 1080)]:
            self.assertIsNone(CursorPosition('DP-1', x, y, 1920, 1080).logical(1280, 720))
        self.assertIsNone(CursorPosition('DP-1', 0, 0, 0, 0).logical(1280, 720))

    def test_bridge_coalesces_burst_and_closes_cleanly(self):
        scheduled, consumed = [], []
        bridge = LatestPosition(scheduled.append, consumed.append)
        for x in range(1000):
            bridge.put(x)
        self.assertEqual(len(scheduled), 1)
        scheduled.pop()()
        self.assertEqual(consumed, [999])
        bridge.put(1000)
        bridge.close()
        scheduled.pop()()
        bridge.put(1001)
        self.assertEqual(consumed, [999])
        self.assertFalse(scheduled)

    def test_hotplug_creates_new_output_session_and_reuses_it_on_geometry_change(self):
        server = FakeCompositor()
        positions = []
        client = CursorClient(positions.append, connection=server).connect()
        client.global_added(14, 'wl_output', 4)
        output = client.outputs[14]
        # Escoar eventos do bind de uma saída adicionada depois da inicialização.
        while server.queue:
            client.dispatch_one()
        self.assertTrue(output.cursor)
        initial = output.cursor
        client.handle(output.object_id, 1, struct.pack('=Iiii', 1, 2560, 1440, 60000))
        client.handle(output.object_id, 2, b'')
        self.assertEqual(output.cursor, initial)
        client.handle(output.cursor, 2, struct.pack('=ii', 1280, 720))
        self.assertEqual(positions[-1], CursorPosition('eDP-1', 1280, 720, 2560, 1440))
        client.close()

    def test_protocol_error_and_lost_pointer_are_reported(self):
        server = FakeCompositor()
        client = CursorClient(lambda _: None, connection=server).connect()
        with self.assertRaisesRegex(RuntimeError, 'recusou'):
            client.handle(1, 0, uints(1, 0) + string('denied'))
        with self.assertRaisesRegex(RuntimeError, 'Ponteiro removido'):
            client.handle(client.selected_seat, 0, uints(0))
        client.close()

    def test_click_snapshot_is_fresh_before_render_and_valid_while_stationary(self):
        scheduled = []
        bridge = LatestPosition(scheduled.append, lambda _: None)
        first = CursorPosition('eDP-1', 10, 20, 100, 100)
        newer = CursorPosition('eDP-1', 30, 40, 100, 100)
        bridge.put(first)
        bridge.put(newer)
        self.assertEqual(bridge.snapshot(), newer)
        scheduled.pop()()
        self.assertEqual(bridge.snapshot(), newer)
        bridge.invalidate('DP-2')
        self.assertEqual(bridge.snapshot(), newer)
        bridge.invalidate('eDP-1')
        self.assertIsNone(bridge.snapshot())
        bridge.close()
        self.assertIsNone(bridge.snapshot())

    def test_cursor_image_overlap_does_not_replace_hotspot_on_actual_output(self):
        positions = []
        client = CursorClient(positions.append)
        output = Output(12, 20, name='eDP-1', width=1920, height=1080, inside=True)
        client.objects[30] = ('cursor', output)
        for x, y in [(-5, 200), (1920, 200), (200, -1), (200, 1080)]:
            client.handle(30, 2, struct.pack('=ii', x, y))
        self.assertEqual(positions, [])
        client.handle(30, 2, struct.pack('=ii', 100, 200))
        self.assertEqual(len(positions), 1)
