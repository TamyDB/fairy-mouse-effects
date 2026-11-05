#!/usr/bin/python3
"""Instala uma cópia independente no usuário; não habilita serviços ou altera udev."""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKER = '# Managed by fairy-mouse user installer.'


def systemd_quote(value):
    value = str(value)
    for old, new in [('\\', '\\\\'), ('"', '\\"'), ('\n', '\\n'), ('\r', '\\r'),
                     ('\t', '\\t'), ('%', '%%'), ('$', '$$')]:
        value = value.replace(old, new)
    return '"' + value + '"'


def managed_file(path):
    if path.is_symlink():
        raise RuntimeError(f'Destino é um link simbólico: {path}')
    if path.exists() and MARKER not in path.read_text():
        raise RuntimeError(f'Arquivo existente não pertence ao instalador: {path}')


def install(prefix, config_home, remove=False):
    data = prefix / 'share' / 'fairy-mouse'
    launcher = prefix / 'bin' / 'fairy-mouse'
    service = config_home / 'systemd' / 'user' / 'fairy-mouse.service'
    stamp = data / '.managed-by-fairy-mouse'
    for file in (launcher, service):
        managed_file(file)
    if data.is_symlink() or (data.exists() and
                            (not stamp.is_file() or stamp.read_text() != MARKER + '\n')):
        raise RuntimeError(f'Diretório existente não pertence ao instalador: {data}')
    if remove:
        # Não apagar uma unidade ainda habilitada: o usuário deve desativá-la primeiro.
        for folder in service.parent.glob('*.wants'):
            if (folder / service.name).is_symlink():
                raise RuntimeError('Desative primeiro: systemctl --user disable --now fairy-mouse.service')
        for file in (launcher, service):
            file.unlink(missing_ok=True)
        if data.exists():
            shutil.rmtree(data)
        return launcher, service

    template = (ROOT / 'packaging/systemd/fairy-mouse.service.in').read_text()
    wrapper = ('#!/usr/bin/python3\n' + MARKER + '\nimport sys\n'
               + f'sys.path.insert(0, {str(data)!r})\n'
               + 'from fairy_mouse.__main__ import main\nraise SystemExit(main())\n')
    # Pré-validar origem e artefatos antes de alterar os destinos.
    compile(wrapper, str(launcher), 'exec')
    modules = sorted((ROOT / 'fairy_mouse').glob('*.py'))
    if not modules:
        raise RuntimeError('Pacote de origem ausente.')
    (data / 'fairy_mouse').mkdir(parents=True, exist_ok=True)
    for module in modules:
        shutil.copy2(module, data / 'fairy_mouse' / module.name)
    for extra in ('README.md',):
        shutil.copy2(ROOT / extra, data / extra)
    stamp.write_text(MARKER + '\n')
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text(wrapper)
    launcher.chmod(0o755)
    service.parent.mkdir(parents=True, exist_ok=True)
    service.write_text(template.replace('@EXECUTABLE@', systemd_quote(launcher)))
    service.chmod(0o644)
    return launcher, service


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', type=Path, default=Path.home() / '.local')
    parser.add_argument('--config-home', type=Path,
                        default=Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config'))
    parser.add_argument('--remove', action='store_true')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Execute como usuário normal, sem sudo.')
    try:
        launcher, service = install(args.prefix.expanduser().absolute(),
                                    args.config_home.expanduser().absolute(), args.remove)
    except (OSError, RuntimeError) as exc:
        parser.exit(1, f'{exc}\n')
    print('Remoção concluída.' if args.remove else f'Aplicativo instalado: {launcher}\nServiço: {service}')
    print('Execute: systemctl --user daemon-reload')
    if not args.remove:
        print('Autostart não foi habilitado e nenhum processo foi iniciado.')


if __name__ == '__main__':
    main()
