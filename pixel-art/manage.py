#!/usr/bin/env python3
"""Install the pixel-art wallpaper for Plasma 6 plus the `fondo-solar` switcher command."""
import argparse
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
PLUGIN = 'local.solar.pixel'
DATA_HOME = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
INSTALLED = DATA_HOME / 'plasma/wallpapers' / PLUGIN
COMMAND = Path.home() / '.local/bin/fondo-solar'

_loader = importlib.machinery.SourceFileLoader('fondo_solar', str(ROOT / 'bin/fondo-solar'))
switcher = importlib.util.module_from_spec(importlib.util.spec_from_loader('fondo_solar', _loader))
_loader.exec_module(switcher)


def package(destination):
    licence = ROOT / 'LICENSE' if (ROOT / 'LICENSE').exists() else ROOT.parent / 'LICENSE'
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT / 'metadata.json', 'metadata.json')
        archive.write(licence, 'LICENSE')
        for path in sorted((ROOT / 'contents').rglob('*')):
            if path.is_file():
                archive.write(path, str(path.relative_to(ROOT)))


def install(activate=True):
    with tempfile.TemporaryDirectory(prefix='solar-pixel-') as folder:
        artifact = Path(folder) / 'solar-pixel.zip'
        package(artifact)
        subprocess.run(['kpackagetool6', '-t', 'Plasma/Wallpaper',
                        '-u' if INSTALLED.exists() else '-i', str(artifact)], check=True)
    COMMAND.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'bin/fondo-solar', COMMAND)
    COMMAND.chmod(0o755)
    print(f'Comando instalado: {COMMAND}')
    if activate:
        switcher.activate(switcher.PIXEL)
        backup = next((b for b in (switcher.BACKUP, switcher.ASCII_BACKUP) if b.exists()), None)
        if backup:
            print('Respaldo del fondo anterior: ' + str(backup))
    else:
        print('Instalado. Actívalo con: fondo-solar pixel')


def uninstall():
    if any(d['plugin'] == PLUGIN for d in switcher.status()):
        if switcher.installed(switcher.ASCII):
            switcher.activate(switcher.ASCII)
        else:
            switcher.restore()
    if INSTALLED.exists():
        subprocess.run(['kpackagetool6', '-t', 'Plasma/Wallpaper', '-r', PLUGIN], check=True)
    if COMMAND.exists() and COMMAND.read_bytes() == (ROOT / 'bin/fondo-solar').read_bytes():
        COMMAND.unlink()
    print('Sistema solar pixel art desinstalado.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall', 'restore', 'status', 'package'])
    parser.add_argument('--no-activate', action='store_true', help='install without switching wallpaper')
    parser.add_argument('--output', type=Path, default=ROOT.parent.parent / 'sistema-solar-pixel.plasmapkg')
    args = parser.parse_args()
    if args.action == 'install':
        install(not args.no_activate)
    elif args.action == 'uninstall':
        uninstall()
    elif args.action == 'restore':
        switcher.restore()
    elif args.action == 'package':
        package(args.output)
        print(args.output)
    else:
        switcher.show_status()
