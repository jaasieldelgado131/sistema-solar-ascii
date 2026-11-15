import QtQuick
import org.kde.plasma.workspace.dbus as DBus

Item {
    id: lockState
    property string service: "org.freedesktop.ScreenSaver"
    property bool locked: false

    function checkLock() {
        DBus.SessionBus.asyncCall({
            service: lockState.service,
            path: "/ScreenSaver",
            iface: "org.freedesktop.ScreenSaver",
            member: "GetActive"
        }, function(reply) {
            lockState.locked = Boolean(reply.value);
        }, function(reply) {
            console.warn("Sistema solar: estado de bloqueo no disponible:", reply.error.message);
        });
    }

    Timer {
        interval: 3000
        running: lockState.visible
        repeat: true
        triggeredOnStart: true
        onTriggered: lockState.checkLock()
    }
}
