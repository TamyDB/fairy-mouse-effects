import json
import unittest

from fairy_mouse.events import PointerEvent, parse_message


class EventTests(unittest.TestCase):
    def encode(self, **changes):
        event = dict(version=1, type='motion', output='eDP-1', x=10.5, y=20)
        event.update(changes)
        return json.dumps(event).encode()

    def test_motion_and_click_preserve_output_and_logical_coordinates(self):
        for kind in ('motion', 'click'):
            self.assertEqual(parse_message(self.encode(type=kind)),
                             PointerEvent(kind, 'eDP-1', 10.5, 20))

    def test_stop_command(self):
        self.assertIsNone(parse_message(b'{"version":1,"type":"stop"}'))

    def test_invalid_payloads_rejected(self):
        payloads = [b'{}', b'[]', b'null', b'\xff', b'{' * 1025,
                    self.encode(version=True), self.encode(x=10 ** 500), self.encode(version=2), self.encode(type='keyboard'),
                    self.encode(output=''), self.encode(x=True),
                    self.encode(x=float('nan')), self.encode(y=float('inf')),
                    self.encode(x=-1), self.encode(x='10'), self.encode(x=None)]
        for data in payloads:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    parse_message(data)
