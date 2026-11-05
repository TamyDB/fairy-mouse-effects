#!/usr/bin/python3
"""Injeta um evento sintético; não lê nem move o cursor real."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fairy_mouse.events import parse_message
from fairy_mouse.runtime import send_message

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', help='conector informado por swaymsg -t get_outputs')
parser.add_argument('x', type=float, help='posição lógica local à saída')
parser.add_argument('y', type=float)
parser.add_argument('--click', action='store_true')
args = parser.parse_args()
data = json.dumps(dict(version=1, type='click' if args.click else 'motion',
                       output=args.output, x=args.x, y=args.y)).encode()
try:
    parse_message(data)
    send_message(data)
except (ValueError, OSError, RuntimeError) as exc:
    parser.exit(1, f'{exc}\n')
