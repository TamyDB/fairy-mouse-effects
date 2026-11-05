"""Observação opcional de BTN_LEFT, somente leitura e sem EVIOCGRAB.

Os ioctls usam a ABI Linux de Fedora x86_64/aarch64. As máscaras afetam
somente o descritor deste processo, nunca a entrega de eventos ao Sway.
"""
import ctypes
import errno
import fcntl
import logging
import os
from pathlib import Path
import struct
import sys

LOG = logging.getLogger(__name__)
EV_SYN, EV_KEY, EV_REL, EV_ABS = 0, 1, 2, 3
BTN_LEFT = 0x110
SYN_REPORT, SYN_DROPPED = 0, 3
EVENT = struct.Struct('@llHHi')
WORD_BITS = ctypes.sizeof(ctypes.c_ulong) * 8


def ioctl_request(direction, number, size):
    return (direction << 30) | (size << 16) | (ord('E') << 8) | number


def bitmap(codes):
    codes = tuple(codes)
    words = (ctypes.c_ulong * (max(codes, default=0) // WORD_BITS + 1))()
    for code in codes:
        words[code // WORD_BITS] |= 1 << (code % WORD_BITS)
    return words


def bits_from_bytes(data):
    result = set()
    width = ctypes.sizeof(ctypes.c_ulong)
    for start in range(0, len(data), width):
        value = int.from_bytes(data[start:start + width], byteorder=sys.byteorder)
        for bit in range(WORD_BITS):
            if value & (1 << bit):
                result.add(start * 8 + bit)
    return result


def get_bits(fd, number, size=96):
    data = bytearray(size)
    fcntl.ioctl(fd, ioctl_request(2, number, size), data, True)
    return bits_from_bytes(data)


def pointer_capabilities(keys, relative, absolute):
    # Alguns mouses Logitech anunciam KEY_ENTER na mesma interface.
    # Exigir botão + eixos; a máscara obrigatória filtra os demais códigos antes da leitura.
    return BTN_LEFT in keys and ({0, 1} <= relative or {0, 1} <= absolute)


def sysfs_codes(text):
    result = set()
    for index, word in enumerate(reversed(text.split())):
        value = int(word, 16)
        for bit in range(WORD_BITS):
            if value & (1 << bit):
                result.add(index * WORD_BITS + bit)
    return result


def candidate_paths(root=Path('/sys/class/input'), device_root=Path('/dev/input')):
    candidates = []
    for node in sorted(root.glob('event*')):
        try:
            caps = node / 'device' / 'capabilities'
            keys = sysfs_codes((caps / 'key').read_text())
            relative = sysfs_codes((caps / 'rel').read_text())
            absolute = sysfs_codes((caps / 'abs').read_text())
            if pointer_capabilities(keys, relative, absolute):
                candidates.append(str(device_root / node.name))
        except (OSError, ValueError):
            continue
    return candidates


def filter_left_button(fd):
    for event_type, codes in ((EV_KEY, [BTN_LEFT]), (EV_SYN, [EV_SYN, EV_KEY])):
        mask = bitmap(codes)
        payload = struct.pack('=IIQ', event_type, ctypes.sizeof(mask), ctypes.addressof(mask))
        fcntl.ioctl(fd, ioctl_request(1, 0x93, 16), payload)


class ClickState:
    def __init__(self, down=False):
        self.down = down
        self.dropped = False

    def feed(self, event_type, code, value, held):
        if event_type == EV_SYN and code == SYN_DROPPED:
            self.dropped = True
        elif self.dropped:
            if event_type == EV_SYN and code == SYN_REPORT:
                self.down = held()
                self.dropped = False
        elif event_type == EV_KEY and code == BTN_LEFT:
            if value == 1:
                emit = not self.down
                self.down = True
                return emit
            if value == 0:
                self.down = False
        return False


class ButtonDevice:
    def __init__(self, path):
        self.path = path
        self.fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            if not pointer_capabilities(get_bits(self.fd, 0x20 + EV_KEY),
                                        get_bits(self.fd, 0x20 + EV_REL),
                                        get_bits(self.fd, 0x20 + EV_ABS)):
                raise ValueError('Dispositivo não expõe botão esquerdo e eixos X/Y de ponteiro.')
            filter_left_button(self.fd)
            self.state = ClickState(self.held())
        except Exception:
            self.close()
            raise

    def held(self):
        return BTN_LEFT in get_bits(self.fd, 0x18)

    def read(self):
        try:
            data = os.read(self.fd, EVENT.size * 64)
        except BlockingIOError:
            return 0
        if not data:
            raise OSError('Dispositivo de clique desconectado.')
        if len(data) % EVENT.size:
            raise OSError('Pacote de entrada incompleto.')
        clicks = 0
        for _, _, event_type, code, value in EVENT.iter_unpack(data):
            clicks += self.state.feed(event_type, code, value, self.held)
        return clicks

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


def device_name(path):
    node = Path(path).resolve().name
    if not node.startswith('event') or not node[5:].isdigit():
        return None
    try:
        return (Path('/sys/class/input') / node / 'device' / 'name').read_text().strip()
    except OSError:
        return None


def diagnose_clicks(paths=None):
    report = []
    for path in candidate_paths() if paths is None else paths:
        try:
            device = ButtonDevice(path)
        except (OSError, ValueError) as exc:
            report.append({'path': path, 'name': device_name(path), 'readable': False,
                           'permission_denied': isinstance(exc, OSError) and exc.errno in
                           (errno.EACCES, errno.EPERM), 'reason': str(exc)})
        else:
            device.close()
            report.append({'path': path, 'name': device_name(path), 'readable': True,
                           'permission_denied': False})
    return {'backend': 'linux_evdev_readonly', 'devices': report,
            'available': any(item['readable'] for item in report),
            'scope': 'physical_left_button; no_touchpad_tap_synthesis'}


class ClickWatcher:
    def __init__(self, glib, on_click, paths=None):
        self.glib = glib
        self.on_click = on_click
        self.paths = paths
        self.devices = {}
        self.seen_click_devices = set()
        self.closed = False

    def rescan(self):
        if self.closed:
            return
        paths = candidate_paths() if self.paths is None else self.paths
        for path, (device, source) in list(self.devices.items()):
            try:
                current = os.stat(path)
                opened = os.fstat(device.fd)
                stale = (current.st_rdev, current.st_ino) != (opened.st_rdev, opened.st_ino)
            except OSError:
                stale = True
            if path not in paths or stale:
                self.glib.source_remove(source)
                device.close()
                del self.devices[path]
                self.seen_click_devices.discard(path)
        for path in paths:
            if path in self.devices:
                continue
            try:
                device = ButtonDevice(path)
            except (OSError, ValueError) as exc:
                LOG.warning('Clique indisponível em %s: %s', path, exc)
                continue
            try:
                source = self.glib.io_add_watch(
                    device.fd, self.glib.IO_IN | self.glib.IO_HUP | self.glib.IO_ERR,
                    lambda fd, condition, name=path: self.receive(name, condition))
            except Exception:
                device.close()
                raise
            self.devices[path] = (device, source)
            LOG.info('Leitor de clique habilitado em %s — %s (somente leitura).',
                     path, device_name(path) or 'nome indisponível')

    def receive(self, path, condition):
        entry = self.devices.get(path)
        if entry is None:
            return False
        device, source = entry
        try:
            if condition & (self.glib.IO_HUP | self.glib.IO_ERR):
                raise OSError('Dispositivo de clique desconectado ou acesso revogado.')
            count = device.read()
            if count and path not in self.seen_click_devices:
                self.seen_click_devices.add(path)
                LOG.info('Primeiro clique físico recebido em %s.', path)
            for _ in range(count):
                self.on_click()
        except OSError as exc:
            LOG.warning('Leitor de clique removido em %s: %s', path, exc)
            self.devices.pop(path)
            self.seen_click_devices.discard(path)
            device.close()
            return False
        return True

    def close(self):
        self.closed = True
        for device, source in self.devices.values():
            self.glib.source_remove(source)
            device.close()
        self.devices.clear()
