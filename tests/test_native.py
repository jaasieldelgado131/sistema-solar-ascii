"""Exercise real Qt timers and asynchronous D-Bus without locking the user's screen."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from pathlib import Path
import time
import unittest

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


class FakeScreenSaver(QObject):
    active = False

    @Slot(result=bool)
    def GetActive(self):
        return self.active


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.engine = QQmlEngine()

    def load(self, filename, properties=None):
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(ROOT / 'contents/ui' / filename)))
        obj = component.createWithInitialProperties(properties or {})
        self.assertIsNotNone(obj, '\n'.join(e.toString() for e in component.errors()))
        obj.setParent(self.engine)
        return obj

    def test_lock_state_uses_dbus_boolean_reply(self):
        bus = QDBusConnection.sessionBus()
        service = 'local.ascii.solar.test' + str(os.getpid())
        provider = FakeScreenSaver()
        self.assertTrue(bus.registerService(service))
        self.assertTrue(bus.registerObject('/ScreenSaver', 'org.freedesktop.ScreenSaver', provider,
                                           QDBusConnection.ExportAllSlots))
        try:
            state = self.load('ScreenState.qml', {'service': service})
            process_for(0.15)
            self.assertFalse(state.property('locked'))
            provider.active = True
            state.checkLock()
            process_for(0.15)
            self.assertTrue(state.property('locked'))
            provider.active = False
            state.checkLock()
            process_for(0.15)
            self.assertFalse(state.property('locked'))
        finally:
            bus.unregisterObject('/ScreenSaver')
            bus.unregisterService(service)

    def test_pause_freezes_time_and_resume_advances(self):
        scene = self.load('SolarScene.qml', {'playing': False, 'width': 800, 'height': 600})
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
        expected = {'cfg_Speed': 2.0, 'cfg_Fps': 24, 'cfg_ShowLabels': False,
                    'cfg_StarDensity': 0.5, 'cfg_Paused': True}
        form = self.load('config.qml', expected)
        process_for(0.1)
        for key, value in expected.items():
            self.assertEqual(form.property(key), value)


if __name__ == '__main__':
    unittest.main()
