#!/usr/bin/env python3
"""Install a native wallpaper and preserve the previous per-desktop selection."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

PLUGIN = 'local.solar.ascii'
ROOT = Path(__file__).resolve().parent
STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / PLUGIN
BACKUP = STATE / 'previous-wallpaper.json'


def evaluate(script):
    return subprocess.run([
        'qdbus6', 'org.kde.plasmashell', '/PlasmaShell',
        'org.kde.PlasmaShell.evaluateScript', script,
    ], check=True, capture_output=True, text=True).stdout.strip()


def status():
    return json.loads(evaluate('''print(JSON.stringify(desktops().map(function(d) {
        return {id: d.id, screen: d.screen, plugin: d.wallpaperPlugin};
    })))'''))


def package(destination):
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT / 'metadata.json', 'metadata.json')
        archive.write(ROOT / 'LICENSE', 'LICENSE')
        for path in sorted((ROOT / 'contents').rglob('*')):
            if path.is_file():
                archive.write(path, str(path.relative_to(ROOT)))


def install():
    previous = status()
    if not previous:
        raise RuntimeError('No se encontró un escritorio Plasma activo.')
    if any(d['plugin'] != PLUGIN for d in previous):
        STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Omit our own selection so repeated installation preserves the original.
        saved = json.loads(BACKUP.read_text()) if BACKUP.exists() else []
        by_id = {d['id']: d for d in saved}
        by_id.update({d['id']: d for d in previous if d['plugin'] != PLUGIN})
        BACKUP.write_text(json.dumps(list(by_id.values()), indent=2) + '\n')
        BACKUP.chmod(0o600)
    data_home = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    installed = data_home / 'plasma/wallpapers' / PLUGIN
    with tempfile.TemporaryDirectory(prefix='solar-ascii-') as folder:
        artifact = Path(folder) / 'solar.zip'
        package(artifact)
        subprocess.run(['kpackagetool6', '-t', 'Plasma/Wallpaper',
                        '-u' if installed.exists() else '-i', str(artifact)], check=True)
    evaluate('desktops().forEach(function(d) { d.wallpaperPlugin = ' + json.dumps(PLUGIN) + '; });')
    if any(d['plugin'] != PLUGIN for d in status()):
        raise RuntimeError('Plasma no confirmó la selección del fondo.')
    print('Sistema solar ASCII instalado y activado.')
    print('Respaldo del fondo anterior: ' + str(BACKUP))


def restore():
    if not BACKUP.exists():
        raise RuntimeError('No existe un respaldo del fondo anterior.')
    saved = json.loads(BACKUP.read_text())
    evaluate('''var saved = ''' + json.dumps(saved) + ''';
        desktops().forEach(function(d) {
            if (d.wallpaperPlugin !== ''' + json.dumps(PLUGIN) + ''') return;
            var previous = saved.find(function(s) { return s.id === d.id; })
                || saved.find(function(s) { return s.screen === d.screen; });
            if (previous) d.wallpaperPlugin = previous.plugin;
        });''')
    print('Fondo anterior restaurado. El paquete ASCII sigue disponible en los ajustes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'restore', 'status', 'package'])
    parser.add_argument('--output', type=Path, default=ROOT.parent / 'sistema-solar-ascii.plasmapkg')
    args = parser.parse_args()
    if args.action == 'install':
        install()
    elif args.action == 'restore':
        restore()
    elif args.action == 'package':
        package(args.output)
        print(args.output)
    else:
        print(json.dumps(status(), indent=2))
