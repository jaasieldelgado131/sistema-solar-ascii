"""Load the real QML with Qt: scene, timers, settings, atlas and the D-Bus wallpaper switch."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import json
from pathlib import Path
import re
import time
import unittest

from PIL import Image
from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtDBus import QDBusConnection
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

ROOT = Path(__file__).resolve().parents[1]
APP = QGuiApplication([])


def process_for(seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        APP.processEvents()
        time.sleep(0.005)


class FakePlasmaShell(QObject):
    def __init__(self):
        super().__init__()
        self.scripts = []

    @Slot(str, result=str)
    def evaluateScript(self, script):
        self.scripts.append(script)
        return ''


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.engine = QQmlEngine()

    def load(self, filename, properties=None):
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(ROOT / 'contents/ui' / filename)))
        obj = component.createWithInitialProperties(properties or {})
        self.assertIsNotNone(obj, '\n'.join(e.toString() for e in component.errors()))
        obj.setParent(self.engine)
        return obj

    def test_scene_loads_without_warnings(self):
        warnings = []
        self.engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
        scene = self.load('PixelScene.qml', {'width': 1920, 'height': 1200, 'seconds': 36})
        process_for(0.3)
        self.assertEqual(scene.property('px'), 3)
        self.assertEqual(warnings, [])

    def test_pause_freezes_time_and_resume_advances(self):
        scene = self.load('PixelScene.qml', {'playing': False, 'width': 800, 'height': 600})
        process_for(0.15)
        self.assertEqual(scene.property('seconds'), 0)
        scene.setProperty('playing', True)
        process_for(0.25)
        self.assertGreater(scene.property('seconds'), 0.05)
        scene.setProperty('playing', False)
        frozen = scene.property('seconds')
        process_for(0.15)
        self.assertEqual(scene.property('seconds'), frozen)

    def test_settings_load_persisted_values(self):
        expected = {'cfg_Speed': 2.0, 'cfg_Fps': 24, 'cfg_PixelSize': 4, 'cfg_StarDensity': 0.5,
                    'cfg_ShowLabels': False, 'cfg_ShowOrbits': False, 'cfg_ShowExtras': False,
                    'cfg_Crt': True, 'cfg_Paused': True}
        form = self.load('config.qml', expected)
        process_for(0.1)
        for key, value in expected.items():
            self.assertEqual(form.property(key), value)

    def test_atlas_matches_images(self):
        text = (ROOT / 'contents/ui/Atlas.js').read_text()
        meta = json.loads(re.search(r'var data = (.*);', text, re.S).group(1))
        for key, body in meta['bodies'].items():
            with Image.open(ROOT / 'contents/ui' / body['src']) as image:
                self.assertEqual(image.size, (body['w'] * body['cols'], body['h'] * body['rows']), key)
        with Image.open(ROOT / 'contents/ui' / meta['sun']['src']) as image:
            rows = -(-meta['sun']['frames'] // meta['sun']['cols'])
            self.assertEqual(image.size, (meta['sun']['w'] * meta['sun']['cols'], meta['sun']['h'] * rows))

    def test_switch_sends_desktop_script_over_dbus(self):
        bus = QDBusConnection.sessionBus()
        service = 'local.solar.pixel.test' + str(os.getpid())
        shell = FakePlasmaShell()
        self.assertTrue(bus.registerService(service))
        self.assertTrue(bus.registerObject('/PlasmaShell', 'org.kde.PlasmaShell', shell,
                                           QDBusConnection.ExportAllSlots))
        try:
            switch = self.load('WallpaperSwitch.qml', {'service': service})
            switch.switchTo('local.solar.ascii', 'Sistema solar ASCII')
            process_for(0.3)
            self.assertEqual(len(shell.scripts), 1)
            self.assertIn("d.wallpaperPlugin = \"local.solar.ascii\"", shell.scripts[0])
            self.assertIn("=== \"local.solar.pixel\"", shell.scripts[0])
        finally:
            bus.unregisterObject('/PlasmaShell')
            bus.unregisterService(service)


if __name__ == '__main__':
    unittest.main()
