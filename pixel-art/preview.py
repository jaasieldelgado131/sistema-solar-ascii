#!/usr/bin/env python3
"""Preview the real Qt Quick scene, optionally saving frames at chosen times."""
import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView

parser = argparse.ArgumentParser()
parser.add_argument('--capture', type=Path, help='PNG path; one file per --time value')
parser.add_argument('--width', type=int, default=1920)
parser.add_argument('--height', type=int, default=1200)
parser.add_argument('--time', type=float, nargs='+', default=[0])
parser.add_argument('--pixel', type=int, default=0, help='pixel size, 0 = automatic')
parser.add_argument('--crt', action='store_true')
args = parser.parse_args()
app = QGuiApplication(sys.argv)
view = QQuickView()
view.setColor('#04050d')
view.setTitle('Sistema solar pixel art — vista previa')
view.setResizeMode(QQuickView.SizeRootObjectToView)
view.resize(args.width, args.height)
view.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / 'contents/ui/PixelScene.qml')))
if view.status() == QQuickView.Error:
    sys.exit(1)
root = view.rootObject()
root.setProperty('pixelSize', args.pixel)
root.setProperty('crt', args.crt)
root.setProperty('seconds', args.time[0])
view.show()

if args.capture:
    root.setProperty('playing', False)
    base = args.capture.resolve()
    base.parent.mkdir(parents=True, exist_ok=True)
    shots = list(args.time)

    def shoot(index=0):
        if index:
            image = view.grabWindow()
            path = base if len(shots) == 1 else base.with_stem(f'{base.stem}-{index - 1}')
            if image.isNull() or not image.save(str(path)):
                print(f'Capture failed: {path}', file=sys.stderr)
                app.exit(1)
                return
            print(f'Saved {path} ({image.width()}x{image.height()})')
        if index == len(shots):
            app.quit()
            return
        root.setProperty('seconds', shots[index])
        QTimer.singleShot(500, lambda: shoot(index + 1))

    QTimer.singleShot(400, shoot)

sys.exit(app.exec())
