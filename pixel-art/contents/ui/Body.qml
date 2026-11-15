import QtQuick
import "Atlas.js" as Atlas
import "Geometry.js" as Geo

// A planet: lit, rotating sprite chosen from its atlas.
Item {
    id: body
    property var info: Geo.planets[0]
    property real seconds: 0
    property real orbitScale: 1
    readonly property var sprite: Atlas.data.bodies[info.key]
    readonly property var orbit: Geo.planetState(info, seconds, orbitScale)
    x: Math.round(orbit.x)
    y: Math.round(orbit.y)
    z: orbit.z

    SpriteFrame {
        x: -body.sprite.w / 2
        y: -body.sprite.h / 2
        source: body.sprite.src
        frameWidth: body.sprite.w
        frameHeight: body.sprite.h
        column: body.orbit.frame
        row: body.orbit.light
    }
}
