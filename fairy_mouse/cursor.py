"""Cliente Wayland dedicado a metadados do cursor, sem buffers de imagem.

Usa apenas wl_registry, wl_output, wl_seat/wl_pointer e sessões EXT de cursor.
Não associa teclado, não cria superfícies e não solicita cópia de pixels.
"""
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import socket
import struct
import threading
import time

from .wayland_probe import HEADER, UINT, REQUIRED, receive_exact, request

LOG = logging.getLogger(__name__)


def uints(*values):
    return struct.pack('=' + 'I' * len(values), *values)


def string(value):
    data = value.encode() + b'\0'
    return UINT.pack(len(data)) + data + b'\0' * (-len(data) % 4)


def read_string(data, offset=0):
    if offset + 4 > len(data):
        raise RuntimeError('String Wayland truncada.')
    size = UINT.unpack_from(data, offset)[0]
    end = offset + 4 + size
    if not size or end > len(data) or data[end - 1] != 0:
        raise RuntimeError('String Wayland inválida.')
    return data[offset + 4:end - 1].decode(), offset + 4 + ((size + 3) & ~3)


@dataclass(frozen=True, slots=True)
class CursorPosition:
    output: str
    x: int
    y: int
    pixel_width: int
    pixel_height: int

    def logical(self, width, height):
        if min(width, height, self.pixel_width, self.pixel_height) <= 0:
            return None
        x = self.x * width / self.pixel_width
        y = self.y * height / self.pixel_height
        # A imagem do cursor pode cruzar duas saídas; usar o hotspot dentro delas.
        if not (0 <= x < width and 0 <= y < height):
            return None
        return x, y


@dataclass
class Output:
    global_id: int
    object_id: int
    name: str = ''
    width: int = 0
    height: int = 0
    transform: int = 0
    ready: bool = False
    source: int = 0
    cursor: int = 0
    inside: bool = False

    def position(self, x, y):
        w, h = self.width, self.height
        if self.transform in (1, 3, 5, 7):
            w, h = h, w
        return CursorPosition(self.name, x, y, w, h)


class CursorClient:
    def __init__(self, on_position, seat='seat0', connection=None, on_leave=None):
        self.on_position = on_position
        self.on_leave = on_leave or (lambda output: None)
        self.seat_name = seat
        self.connection = connection
        self.next_id = 2
        self.objects = {1: ('display', None)}
        self.outputs = {}
        self.seats = {}
        self.managers = {}
        self.pointer = 0
        self.selected_seat = 0
        self.pending_sync = 0
        self.running = False
        self.ready = False
        self.deadline = None

    def allocate(self, kind, data=None):
        object_id = self.next_id
        self.next_id += 1
        self.objects[object_id] = (kind, data)
        return object_id

    def send(self, object_id, opcode, payload=b''):
        self.connection.sendall(request(object_id, opcode, payload))

    def bind(self, global_id, interface, version, kind, data=None):
        object_id = self.allocate(kind, data)
        self.send(self.registry, 0, uints(global_id) + string(interface) + uints(version, object_id))
        return object_id

    def connect(self):
        try:
            if self.connection is None:
                name = os.environ.get('WAYLAND_DISPLAY')
                runtime = os.environ.get('XDG_RUNTIME_DIR')
                if not name or (not os.path.isabs(name) and not runtime):
                    raise RuntimeError('Ambiente Wayland não definido.')
                path = name if os.path.isabs(name) else str(Path(runtime) / name)
                self.connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.connection.settimeout(2)
                self.connection.connect(path)
            self.deadline = time.monotonic() + 2
            self.registry = self.allocate('registry')
            self.send(1, 1, uints(self.registry))
            self.roundtrip()
            missing = [name for name in REQUIRED if name not in self.managers]
            if missing:
                raise RuntimeError('Protocolos de cursor ausentes: ' + ', '.join(missing))
            # Receber eventos das associações feitas ao processar wl_registry.global.
            self.roundtrip()
            for object_id, seat in self.seats.items():
                if seat['name'] == self.seat_name and seat['caps'] & 1:
                    self.selected_seat = object_id
                    self.pointer = self.allocate('pointer')
                    self.send(object_id, 0, uints(self.pointer))
                    break
            if not self.pointer:
                raise RuntimeError(f'Seat {self.seat_name} sem ponteiro disponível.')
            self.ready = True
            for output in list(self.outputs.values()):
                self.start_output(output)
            self.roundtrip()
            self.deadline = None
            self.connection.settimeout(None)
            return self
        except Exception:
            self.close()
            raise

    def roundtrip(self):
        callback = self.allocate('callback')
        self.pending_sync = callback
        self.send(1, 0, uints(callback))
        while self.pending_sync:
            self.dispatch_one()

    def recv(self, count):
        if self.deadline is not None:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Inicialização do rastreamento excedeu dois segundos.')
            self.connection.settimeout(remaining)
        return self.connection.recv(count)

    def dispatch_one(self):
        object_id, word = HEADER.unpack(receive_exact(self, HEADER.size))
        size, opcode = word >> 16, word & 0xffff
        if size < HEADER.size or size % 4:
            raise RuntimeError('Mensagem Wayland inválida.')
        data = receive_exact(self, size - HEADER.size)
        try:
            self.handle(object_id, opcode, data)
        except (struct.error, UnicodeError) as exc:
            raise RuntimeError('Evento Wayland truncado ou inválido.') from exc

    def handle(self, object_id, opcode, data):
        kind, state = self.objects.get(object_id, ('ignored', None))
        if kind == 'display':
            if opcode == 0:
                message, _ = read_string(data, 8)
                raise RuntimeError(f'O compositor recusou o rastreamento: {message}')
            if opcode == 1:
                self.objects.pop(UINT.unpack(data)[0], None)
        elif kind == 'callback':
            if object_id == self.pending_sync:
                self.pending_sync = 0
        elif kind == 'registry':
            if opcode == 0:
                global_id = UINT.unpack_from(data)[0]
                interface, offset = read_string(data, 4)
                version = UINT.unpack_from(data, offset)[0]
                self.global_added(global_id, interface, version)
            elif opcode == 1:
                self.global_removed(UINT.unpack(data)[0])
        elif kind == 'output':
            if opcode == 0:
                _, offset = read_string(data, 20)
                _, offset = read_string(data, offset)
                state.transform = struct.unpack_from('=i', data, offset)[0]
            elif opcode == 1:
                flags, width, height, refresh = struct.unpack('=Iiii', data)
                if flags & 1:
                    state.width, state.height = width, height
            elif opcode == 2:
                state.ready = True
                if self.ready:
                    self.start_output(state)
            elif opcode == 4:
                state.name, _ = read_string(data)
        elif kind == 'seat':
            if opcode == 0:
                state['caps'] = UINT.unpack(data)[0]
                if self.ready and object_id == self.selected_seat and not state['caps'] & 1:
                    raise RuntimeError('Ponteiro removido do seat; reinicie após reconectar.')
            elif opcode == 1:
                state['name'], _ = read_string(data)
        elif kind == 'cursor':
            if opcode == 0:
                state.inside = True
            elif opcode == 1:
                state.inside = False
                self.on_leave(state.name)
            elif opcode == 2 and state.inside:
                x, y = struct.unpack('=ii', data)
                if state.name and state.width > 0 and state.height > 0:
                    position = state.position(x, y)
                    if 0 <= x < position.pixel_width and 0 <= y < position.pixel_height:
                        self.on_position(position)
            # hotspot é relativo à imagem. position já descreve o hotspot real.

    def global_added(self, global_id, interface, version):
        if interface in REQUIRED and interface not in self.managers:
            object_id = self.bind(global_id, interface, 1, 'manager')
            self.managers[interface] = (global_id, object_id)
        elif interface == 'wl_output':
            if version < 4:
                LOG.warning('Saída ignorada: wl_output sem nome de conector (v4).')
                return
            output = Output(global_id, 0)
            output.object_id = self.bind(global_id, interface, 4, 'output', output)
            self.outputs[global_id] = output
        elif interface == 'wl_seat':
            if version < 2:
                return
            seat = {'name': '', 'caps': 0, 'global_id': global_id}
            object_id = self.bind(global_id, interface, min(version, 5), 'seat', seat)
            self.seats[object_id] = seat

    def start_output(self, output):
        if output.cursor or not output.ready or not output.name:
            return
        output.source = self.allocate('source', output)
        self.send(self.managers[REQUIRED[1]][1], 0, uints(output.source, output.object_id))
        output.cursor = self.allocate('cursor', output)
        self.send(self.managers[REQUIRED[0]][1], 1,
                  uints(output.cursor, output.source, self.pointer))

    def global_removed(self, global_id):
        output = self.outputs.pop(global_id, None)
        if output:
            output.inside = False
            self.on_leave(output.name)
            for object_id in (output.cursor, output.source, output.object_id):
                if object_id:
                    self.send(object_id, 0)  # destroy / wl_output.release
                    self.objects[object_id] = ('ignored', None)
        if any(gid == global_id for gid, _ in self.managers.values()):
            raise RuntimeError('O compositor retirou o protocolo de metadados do cursor.')
        if any(s['global_id'] == global_id for s in self.seats.values()):
            raise RuntimeError('Seat removido; reinicie o rastreamento na sessão atual.')

    def listen(self):
        self.running = True
        try:
            while self.running:
                self.dispatch_one()
        finally:
            self.running = False

    def close(self):
        self.running = False
        if self.connection is not None:
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.connection.close()


class LatestPosition:
    """Uma única atualização pendente entre o leitor e o loop GTK."""
    def __init__(self, schedule, consume):
        self.schedule = schedule
        self.consume = consume
        self.lock = threading.Lock()
        self.latest = None
        self.current = None
        self.pending = False
        self.closed = False

    def put(self, position):
        with self.lock:
            if self.closed:
                return
            self.latest = position
            self.current = position
            if not self.pending:
                self.pending = True
                self.schedule(self.deliver)

    def deliver(self):
        with self.lock:
            position = self.latest
            self.latest = None
            self.pending = False
            closed = self.closed
        if not closed and position is not None:
            self.consume(position)
        return False

    def snapshot(self):
        with self.lock:
            return self.current

    def invalidate(self, output):
        with self.lock:
            if self.current is not None and self.current.output == output:
                self.current = None
            if self.latest is not None and self.latest.output == output:
                self.latest = None

    def close(self):
        with self.lock:
            self.closed = True
            self.latest = None
            self.current = None
