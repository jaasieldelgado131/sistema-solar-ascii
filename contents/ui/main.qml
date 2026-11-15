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
        }
    ]

    ScreenState { id: screenState }

    SolarScene {
        anchors.fill: parent
        playing: !screenState.locked && !wallpaper.configuration.Paused
        speed: Math.max(0.1, Math.min(4, wallpaper.configuration.Speed))
        fps: wallpaper.configuration.Fps
        showLabels: wallpaper.configuration.ShowLabels
        starDensity: wallpaper.configuration.StarDensity
    }
    Component.onCompleted: console.info("Sistema solar ASCII: escena nativa cargada")
}
