"""Instância única e transporte local restrito à sessão do usuário."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import socket
import stat


def runtime_directory():
    value = os.environ.get('XDG_RUNTIME_DIR')
    if not value or not Path(value).is_absolute():
        raise RuntimeError('XDG_RUNTIME_DIR deve apontar para o diretório da sessão.')
    root = Path(value)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise RuntimeError('Diretório de sessão inválido.')
    path = root / 'fairy-mouse'
    path.mkdir(mode=0o700, exist_ok=True)
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise RuntimeError('O diretório fairy-mouse deve pertencer ao usuário e ter modo 0700.')
    return path


@contextmanager
def event_socket():
    directory = runtime_directory()
    fd = os.open(directory / 'instance.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    endpoint = directory / 'events.sock'
    acquired = False
    server = None
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Fairy Mouse já está em execução nesta sessão.') from None
        acquired = True
        endpoint.unlink(missing_ok=True)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(str(endpoint))
        endpoint.chmod(0o600)
        server.setblocking(False)
        yield server
    finally:
        if server is not None:
            server.close()
        if acquired:
            endpoint.unlink(missing_ok=True)
        # Manter o arquivo de lock evita corrida entre inodes de instâncias diferentes.
        os.close(fd)


def send_message(data):
    endpoint = runtime_directory() / 'events.sock'
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
        client.settimeout(1)
        try:
            client.sendto(data, str(endpoint))
        except (FileNotFoundError, ConnectionRefusedError):
            raise RuntimeError('Nenhuma instância de segundo plano está disponível.') from None
