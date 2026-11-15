pragma ComponentBehavior: Bound
import QtQuick
import "Atlas.js" as Atlas
import "Geometry.js" as Geo

// Small rocket shuttling between Earth and Mars along an arc.
Item {
    id: ship
    property real seconds: 0
    property real orbitScale: 1
    readonly property var mission: Geo.missionState(seconds, orbitScale)
    readonly property var sprite: Atlas.data.ship
    readonly property var colors: ["#ffd060", "#ff9a3c", "#e0602c", "#a83c2c", "#6a2a2c", "#3a1c28"]
    visible: mission.visible

    Repeater {
        model: ship.mission.trail.length
        Rectangle {
            required property int index
            x: ship.mission.trail[index].x
            y: ship.mission.trail[index].y
            width: 1
            height: 1
            color: ship.colors[index]
        }
    }

    SpriteFrame {
        x: Math.round(ship.mission.x) - Math.floor(ship.sprite.w / 2)
        y: Math.round(ship.mission.y) - Math.floor(ship.sprite.h / 2)
        source: ship.sprite.src
        frameWidth: ship.sprite.w
        frameHeight: ship.sprite.h
        column: ship.mission.dir
        row: Math.floor(ship.seconds * 9) % 2
    }
}
