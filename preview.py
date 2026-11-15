#!/usr/bin/env python3
"""Preview the real Qt Quick scene, optionally saving two animated frames."""
import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView

parser = argparse.ArgumentParser()
parser.add_argument('--capture', type=Path)
parser.add_argument('--width', type=int, default=1920)
parser.add_argument('--height', type=int, default=1200)
parser.add_argument('--time', type=float, default=0)
parser.add_argument('--body', action='store_true')
args = parser.parse_args()
app = QGuiApplication(sys.argv)
view = QQuickView()
view.setColor('#050912')
view.setTitle('Sistema solar ASCII — vista previa')
view.setResizeMode(QQuickView.SizeRootObjectToView)
view.resize(args.width, args.height)
component = 'AsciiBody.qml' if args.body else 'SolarScene.qml'
view.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / 'contents/ui' / component)))
if view.status() == QQuickView.Error:
    sys.exit(1)
view.rootObject().setProperty('seconds', args.time)
view.show()

if args.capture:
    args.capture = args.capture.resolve()
    args.capture.parent.mkdir(parents=True, exist_ok=True)

    def capture(path):
        image = view.grabWindow()
        if image.isNull() or not image.save(str(path)):
            print(f'Capture failed: {path}', file=sys.stderr)
            app.exit(1)
        else:
            print(f'Saved {path} ({image.width()}x{image.height()})')

    QTimer.singleShot(700, lambda: capture(args.capture))
    QTimer.singleShot(2400, lambda: capture(args.capture.with_stem(args.capture.stem + '-2')))
    QTimer.singleShot(2700, app.quit)

sys.exit(app.exec())
