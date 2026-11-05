import ctypes
import errno
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import Mock, patch

from fairy_mouse.clicks import (BTN_LEFT, EVENT, EV_KEY, EV_SYN, SYN_DROPPED,
                               SYN_REPORT, ButtonDevice, ClickState, ClickWatcher,
                               WORD_BITS, bitmap, bits_from_bytes, candidate_paths,
                               diagnose_clicks, filter_left_button, pointer_capabilities)


class ClickTests(unittest.TestCase):
    def test_only_new_left_press_triggers_and_held_does_not_repeat(self):
        state = ClickState()
        held = lambda: False
        self.assertFalse(state.feed(EV_KEY, 30, 1, held))
        self.assertFalse(state.feed(2, 0, 10, held))
        self.assertTrue(state.feed(EV_KEY, BTN_LEFT, 1, held))
        self.assertFalse(state.feed(EV_KEY, BTN_LEFT, 1, held))
        self.assertFalse(state.feed(EV_KEY, BTN_LEFT, 2, held))
        self.assertFalse(state.feed(EV_KEY, BTN_LEFT, 0, held))
        self.assertTrue(state.feed(EV_KEY, BTN_LEFT, 1, held))

    def test_overrun_resynchronizes_without_phantom_click(self):
        state = ClickState()
        state.feed(EV_SYN, SYN_DROPPED, 0, lambda: True)
        self.assertFalse(state.feed(EV_KEY, BTN_LEFT, 1, lambda: True))
        self.assertFalse(state.feed(EV_SYN, SYN_REPORT, 0, lambda: True))
        self.assertFalse(state.feed(EV_KEY, BTN_LEFT, 1, lambda: True))
        state.feed(EV_KEY, BTN_LEFT, 0, lambda: False)
        self.assertTrue(state.feed(EV_KEY, BTN_LEFT, 1, lambda: False))

    def test_pointer_classification_accepts_composite_mouse_rejects_keyboard_and_touch_only(self):
        self.assertTrue(pointer_capabilities({BTN_LEFT}, {0, 1}, set()))
        self.assertTrue(pointer_capabilities({BTN_LEFT}, set(), {0, 1}))
        self.assertTrue(pointer_capabilities({BTN_LEFT, 28}, {0, 1}, set()))
        self.assertFalse(pointer_capabilities({28, 30, 44, 57}, set(), set()))
        self.assertFalse(pointer_capabilities({28, 30, 44, 57}, {0, 1}, set()))
        self.assertFalse(pointer_capabilities({BTN_LEFT}, set(), set()))
        self.assertFalse(pointer_capabilities({330}, set(), {0, 1}))

    def test_kernel_mask_contains_only_left_button_and_event_type_filter(self):
        masks = []
        def ioctl(fd, request, data):
            event_type, size, pointer = struct.unpack('=IIQ', data)
            masks.append((event_type, bits_from_bytes(ctypes.string_at(pointer, size))))
        with patch('fairy_mouse.clicks.fcntl.ioctl', side_effect=ioctl):
            filter_left_button(10)
        self.assertEqual(masks, [(EV_KEY, {BTN_LEFT}), (EV_SYN, {EV_SYN, EV_KEY})])

    def test_bitmap_roundtrip(self):
        codes = {0, 1, 63, 64, BTN_LEFT}
        mask = bitmap(codes)
        self.assertEqual(bits_from_bytes(bytes(mask)), codes)

    def test_sysfs_discovery_includes_logitech_mouse_and_excludes_keyboard(self):
        def formatted(codes):
            words = bitmap(codes)
            return ' '.join(format(n, 'x') for n in reversed(words))
        with tempfile.TemporaryDirectory() as root:
            for name, keys in [('event1', {BTN_LEFT}), ('event2', {28, 30}),
                               ('event6', {BTN_LEFT, 28})]:
                directory = Path(root) / name / 'device' / 'capabilities'
                directory.mkdir(parents=True)
                for file, codes in [('key', keys), ('rel', {0, 1}), ('abs', set())]:
                    (directory / file).write_text(formatted(codes))
            self.assertEqual(candidate_paths(Path(root), Path('/dev/input')),
                             ['/dev/input/event1', '/dev/input/event6'])

    def test_device_opens_readonly_reads_press_and_closes(self):
        values = [{BTN_LEFT}, {0, 1}, set(), set()]
        data = EVENT.pack(0, 0, EV_KEY, BTN_LEFT, 1)
        data += EVENT.pack(0, 0, EV_SYN, SYN_REPORT, 0)
        with patch('fairy_mouse.clicks.os.open', return_value=20) as opener, \
             patch('fairy_mouse.clicks.os.close') as closer, \
             patch('fairy_mouse.clicks.get_bits', side_effect=values), \
             patch('fairy_mouse.clicks.filter_left_button'), \
             patch('fairy_mouse.clicks.os.read', return_value=data):
            device = ButtonDevice('/dev/input/event1')
            self.assertEqual(opener.call_args.args[1] & os.O_ACCMODE, os.O_RDONLY)
            self.assertEqual(device.read(), 1)
            device.close()
            device.close()
            closer.assert_called_once_with(20)

    def test_permission_denied_is_reported_without_permission_changes(self):
        with patch('fairy_mouse.clicks.ButtonDevice', side_effect=PermissionError(errno.EACCES, 'denied')):
            report = diagnose_clicks(['/dev/input/event1'])
        self.assertFalse(report['available'])
        self.assertFalse(report['devices'][0]['readable'])
        self.assertIn('denied', report['devices'][0]['reason'])

    def test_filter_failure_closes_device(self):
        with patch('fairy_mouse.clicks.os.open', return_value=20), \
             patch('fairy_mouse.clicks.os.close') as closer, \
             patch('fairy_mouse.clicks.get_bits', side_effect=[{BTN_LEFT}, {0, 1}, set()]), \
             patch('fairy_mouse.clicks.filter_left_button', side_effect=OSError('unsupported')):
            with self.assertRaises(OSError):
                ButtonDevice('/dev/input/event1')
            closer.assert_called_once_with(20)

    def test_watcher_deduplicates_and_removes_disconnected_device(self):
        glib = Mock(IO_IN=1, IO_HUP=2, IO_ERR=4)
        glib.io_add_watch.return_value = 42
        device = Mock(fd=10)
        device.read.return_value = 2
        on_click = Mock()
        with patch('fairy_mouse.clicks.ButtonDevice', return_value=device) as factory, \
             patch('fairy_mouse.clicks.os.stat', return_value=Mock(st_rdev=1, st_ino=2)), \
             patch('fairy_mouse.clicks.os.fstat', return_value=Mock(st_rdev=1, st_ino=2)):
            watcher = ClickWatcher(glib, on_click, paths=['/dev/input/event1'])
            watcher.rescan()
            watcher.rescan()
            factory.assert_called_once()
            self.assertTrue(watcher.receive('/dev/input/event1', 1))
            self.assertEqual(on_click.call_count, 2)
            with self.assertLogs('fairy_mouse.clicks', level='WARNING'):
                self.assertFalse(watcher.receive('/dev/input/event1', 2))
            self.assertFalse(watcher.devices)
            device.close.assert_called_once()
            watcher.close()

    def test_access_denied_report_identifies_device_and_permission_cause(self):
        with patch('fairy_mouse.clicks.ButtonDevice', side_effect=PermissionError(errno.EACCES, 'denied')), \
             patch('fairy_mouse.clicks.device_name', return_value='ELAN Touchpad'):
            report = diagnose_clicks(['/dev/input/event4'])
        self.assertEqual(report['devices'][0]['name'], 'ELAN Touchpad')
        self.assertTrue(report['devices'][0]['permission_denied'])

    def test_missing_device_is_not_misreported_as_permission_problem(self):
        with patch('fairy_mouse.clicks.ButtonDevice', side_effect=FileNotFoundError(errno.ENOENT, 'missing')):
            report = diagnose_clicks(['/dev/input/event4'])
        self.assertFalse(report['devices'][0]['permission_denied'])

    def test_composite_logitech_mouse_filters_before_reading_any_events(self):
        sequence = []
        def open_device(path, flags):
            sequence.append('open-readonly')
            self.assertEqual(flags & os.O_ACCMODE, os.O_RDONLY)
            return 20
        def capabilities(fd, number, size=96):
            sequence.append(('ioctl', number))
            return {0x21: {BTN_LEFT, 28}, 0x22: {0, 1}, 0x23: set(), 0x18: set()}[number]
        def filtered(fd):
            sequence.append('mask-left-only')
        with patch('fairy_mouse.clicks.os.open', side_effect=open_device), \
             patch('fairy_mouse.clicks.os.close'), \
             patch('fairy_mouse.clicks.get_bits', side_effect=capabilities), \
             patch('fairy_mouse.clicks.filter_left_button', side_effect=filtered), \
             patch('fairy_mouse.clicks.os.read') as reader:
            device = ButtonDevice('/dev/input/event6')
            reader.assert_not_called()
            self.assertLess(sequence.index('mask-left-only'), sequence.index(('ioctl', 0x18)))
            device.close()

    def test_stable_alias_reopens_after_device_replacement(self):
        glib = Mock(IO_IN=1, IO_HUP=2, IO_ERR=4)
        glib.io_add_watch.side_effect = [42, 43]
        old, new = Mock(fd=10), Mock(fd=11)
        with patch('fairy_mouse.clicks.ButtonDevice', side_effect=[old, new]) as factory, \
             patch('fairy_mouse.clicks.os.stat', return_value=Mock(st_rdev=2, st_ino=200)), \
             patch('fairy_mouse.clicks.os.fstat', return_value=Mock(st_rdev=1, st_ino=100)):
            watcher = ClickWatcher(glib, Mock(), paths=['/dev/input/fairy-mouse-logitech'])
            watcher.rescan()
            watcher.rescan()
            self.assertEqual(factory.call_count, 2)
            old.close.assert_called_once()
            glib.source_remove.assert_called_once_with(42)
            self.assertIs(watcher.devices['/dev/input/fairy-mouse-logitech'][0], new)
            watcher.close()

    def test_removed_alias_cleans_descriptor_before_next_read(self):
        glib = Mock(IO_IN=1, IO_HUP=2, IO_ERR=4)
        device = Mock(fd=10)
        with patch('fairy_mouse.clicks.ButtonDevice', side_effect=[device, FileNotFoundError()]), \
             patch('fairy_mouse.clicks.os.stat', side_effect=FileNotFoundError()):
            watcher = ClickWatcher(glib, Mock(), paths=['/dev/input/fairy-mouse-logitech'])
            watcher.rescan()
            with self.assertLogs('fairy_mouse.clicks', level='WARNING'):
                watcher.rescan()
            self.assertFalse(watcher.devices)
            self.assertFalse(watcher.receive('/dev/input/fairy-mouse-logitech', 1))
            device.close.assert_called_once()
