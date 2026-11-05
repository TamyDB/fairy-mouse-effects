"""Contrato de integração; não é uma fonte de eventos do Sway."""
from dataclasses import dataclass
import json
import math

MAX_MESSAGE = 1024


@dataclass(frozen=True, slots=True)
class PointerEvent:
    kind: str
    output: str
    x: float
    y: float


def parse_message(data):
    if len(data) > MAX_MESSAGE:
        raise ValueError('Mensagem muito grande.')
    try:
        message = json.loads(data)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError('JSON inválido.') from exc
    if (not isinstance(message, dict) or type(message.get('version')) is not int
            or message['version'] != 1):
        raise ValueError('Esperado objeto com version=1.')
    kind = message.get('type')
    if kind == 'stop':
        return None
    if kind not in ('motion', 'click'):
        raise ValueError('Evento desconhecido.')
    output = message.get('output')
    if not isinstance(output, str) or not output or len(output) > 128:
        raise ValueError('Saída inválida.')
    coords = [message.get('x'), message.get('y')]
    if any(type(v) not in (int, float) or v < 0 or v > 100000 or not math.isfinite(v)
           for v in coords):
        raise ValueError('Coordenadas lógicas inválidas.')
    return PointerEvent(kind, output, *coords)
