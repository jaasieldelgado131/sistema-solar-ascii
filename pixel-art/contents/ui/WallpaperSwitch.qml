import QtQuick
import org.kde.plasma.workspace.dbus as DBus

// Asks plasmashell (same desktop scripting manage.py uses) to swap this
// wallpaper for another one on every desktop currently showing it.
QtObject {
    id: switcher
    property string service: "org.kde.plasmashell"
    property string from: "local.solar.pixel"

    function script(target, targetName) {
        return "var known = knownWallpaperPlugins();"
            + "if (!(" + JSON.stringify(targetName) + " in known)) throw new Error('No está instalado: ' + "
            + JSON.stringify(targetName) + ");"
            + "desktops().forEach(function(d) {"
            + " if (d.wallpaperPlugin === " + JSON.stringify(switcher.from) + ")"
            + " d.wallpaperPlugin = " + JSON.stringify(target) + ";"
            + "});";
    }

    function switchTo(target, targetName) {
        DBus.SessionBus.asyncCall({
            service: switcher.service,
            path: "/PlasmaShell",
            iface: "org.kde.PlasmaShell",
            member: "evaluateScript",
            arguments: [switcher.script(target, targetName)]
        }, function(reply) {}, function(reply) {
            console.warn("Sistema solar pixel art: no se pudo cambiar de fondo:", reply.error.message);
        });
    }
}
