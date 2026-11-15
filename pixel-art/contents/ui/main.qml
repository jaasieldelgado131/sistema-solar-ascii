import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

WallpaperItem {
    id: wallpaper

    contextualActions: [
        PlasmaCore.Action {
            text: wallpaper.configuration.Paused ? "Reanudar sistema solar" : "Pausar sistema solar"
            icon.name: wallpaper.configuration.Paused ? "media-playback-start" : "media-playback-pause"
            onTriggered: {
                wallpaper.configuration.Paused = !wallpaper.configuration.Paused;
                wallpaper.configuration.writeConfig();
            }
        },
        PlasmaCore.Action {
            text: "Cambiar al sistema solar ASCII"
            icon.name: "preferences-desktop-wallpaper"
            onTriggered: switcher.switchTo("local.solar.ascii", "Sistema solar ASCII")
        }
    ]

    ScreenState { id: screenState }
    WallpaperSwitch { id: switcher }

    PixelScene {
        anchors.fill: parent
        playing: !screenState.locked && !wallpaper.configuration.Paused
        speed: Math.max(0.1, Math.min(4, wallpaper.configuration.Speed))
        fps: wallpaper.configuration.Fps
        showLabels: wallpaper.configuration.ShowLabels
        showOrbits: wallpaper.configuration.ShowOrbits
        showExtras: wallpaper.configuration.ShowExtras
        crt: wallpaper.configuration.Crt
        starDensity: wallpaper.configuration.StarDensity
        pixelSize: wallpaper.configuration.PixelSize
    }
    Component.onCompleted: console.info("Sistema solar pixel art 1.0.0: escena cargada")
}
