"""Consulta somente o registro Wayland; não cria superfícies nem captura imagens."""
import os
from pathlib import Path
import socket
import struct

HEADER = struct.Struct('=II')
UINT = struct.Struct('=I')
REQUIRED = ('ext_image_copy_capture_manager_v1',
            'ext_output_image_capture_source_manager_v1')


def request(object_id, opcode, payload):
    size = HEADER.size + len(payload)
    return HEADER.pack(object_id, (size << 16) | opcode) + payload


def receive_exact(connection, size):
    data = bytearray()
    while len(data) < size:
        chunk = connection.recv(size - len(data))
        if not chunk:
            raise RuntimeError('Conexão Wayland encerrada durante diagnóstico.')
        data.extend(chunk)
    return bytes(data)


def read_registry(connection):
    # wl_display.get_registry(new_id=2), seguido por wl_display.sync(new_id=3).
    connection.sendall(request(1, 1, UINT.pack(2)) + request(1, 0, UINT.pack(3)))
    globals_found = {}
    for _ in range(4096):
        object_id, word = HEADER.unpack(receive_exact(connection, HEADER.size))
        size, opcode = word >> 16, word & 0xffff
        if size < HEADER.size or size % 4:
            raise RuntimeError('Mensagem inválida no registro Wayland.')
        payload = receive_exact(connection, size - HEADER.size)
        if object_id == 1 and opcode == 0:
            raise RuntimeError('O compositor recusou a consulta ao registro Wayland.')
        if object_id == 3 and opcode == 0:
            return globals_found
        if object_id != 2 or opcode != 0:
            continue
        # wl_registry.global(name: uint, interface: string, version: uint).
        if len(payload) < 12:
            raise RuntimeError('Registro Wayland truncado.')
        length = UINT.unpack_from(payload, 4)[0]
        padded = (length + 3) & ~3
        if not length or 8 + padded + 4 != len(payload):
            raise RuntimeError('Nome inválido no registro Wayland.')
        if payload[8 + length - 1] != 0:
            raise RuntimeError('Nome sem terminador no registro Wayland.')
        interface = payload[8:8 + length - 1].decode('ascii')
        version = UINT.unpack_from(payload, 8 + padded)[0]
        globals_found[interface] = max(version, globals_found.get(interface, 0))
    raise RuntimeError('Registro Wayland excedeu o limite de mensagens.')


def probe():
    name = os.environ.get('WAYLAND_DISPLAY')
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if not name or (not os.path.isabs(name) and not runtime):
        raise RuntimeError('Ambiente Wayland não definido.')
    path = name if os.path.isabs(name) else str(Path(runtime) / name)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        # Tempo total limitado, inclusive em servidor que não termina o sync.
        import time
        deadline = time.monotonic() + 1
        connection.settimeout(1)
        connection.connect(path)

        class BoundedConnection:
            def sendall(self, data):
                connection.settimeout(max(.001, deadline - time.monotonic()))
                connection.sendall(data)

            def recv(self, size):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Tempo de consulta Wayland esgotado.')
                connection.settimeout(remaining)
                return connection.recv(size)

        return read_registry(BoundedConnection())
