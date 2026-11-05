import argparse
import json
import logging
import sys


def color(value):
    try:
        if len(value) != 7 or not value.startswith('#'):
            raise ValueError
        return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))
    except ValueError:
        raise argparse.ArgumentTypeError('Use uma cor no formato #RRGGBB.') from None


def main():
    parser = argparse.ArgumentParser(description='Fairy Mouse — protótipo leve para Sway')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--demo', action='store_true', help='testar efeitos em uma janela local')
    mode.add_argument('--diagnose', action='store_true', help='inspecionar dependências e sessão')
    mode.add_argument('--background', action='store_true', help='rastro em segundo plano usando metadados do Sway')
    mode.add_argument('--stop', action='store_true', help='encerrar a instância em segundo plano')
    parser.add_argument('--external-events', action='store_true', help='teste do overlay sem captura de posição (com --background)')
    parser.add_argument('--no-clicks', action='store_true', help='desativar observação de cliques físicos')
    parser.add_argument('--click-device', action='append', metavar='/dev/input/eventN', help='observar somente este mouse; pode repetir')
    parser.add_argument('--seat', default='seat0', help='seat do Sway para rastreamento (padrão: seat0)')
    parser.add_argument('--fps', type=int, choices=range(10, 61), default=30, metavar='10..60')
    parser.add_argument('--particles', type=int, choices=range(1, 257), default=48, metavar='1..256')
    parser.add_argument('--intensity', type=float, default=1.0)
    parser.add_argument('--color', type=color, default=color('#E5B5FF'), metavar='#RRGGBB')
    args = parser.parse_args()
    if args.external_events and not args.background:
        parser.error('--external-events exige --background.')
    if args.click_device and not args.background:
        parser.error('--click-device exige --background.')
    if args.click_device and (args.no_clicks or args.external_events):
        parser.error('--click-device não combina com --no-clicks ou --external-events.')
    if not .1 <= args.intensity <= 2:
        parser.error('--intensity deve estar entre 0.1 e 2.')
    if args.diagnose:
        from .diagnostics import diagnose
        print(json.dumps(diagnose(), ensure_ascii=False, indent=2))
        return 0
    try:
        if args.stop:
            from .runtime import send_message
            send_message(b'{"version":1,"type":"stop"}')
            print('Pedido de encerramento enviado.')
            return 0
        if args.background:
            from .background import run
        else:
            from .demo import run
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        return run(args)
    except (ImportError, ValueError, OSError, RuntimeError) as exc:
        print(f"Não foi possível iniciar: {str(exc).rstrip('.')}. Use /usr/bin/python3 e --diagnose.",
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
