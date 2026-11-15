pragma ComponentBehavior: Bound
import QtQuick
import "Geometry.js" as Geo

// Shooting star drawn as a clean 2:1 pixel line.
Item {
    id: meteor
    property int index: 0
    property real seconds: 0
    property real areaWidth: 640
    property real areaHeight: 400
    readonly property var flight: Geo.meteor(index, seconds, areaWidth, areaHeight)
    x: flight.x
    y: flight.y
    visible: flight.visible
    opacity: flight.opacity

    Repeater {
        model: 16
        Rectangle {
            required property int index
            x: -meteor.flight.dir * index
            y: -Math.floor(index / 2)
            width: 1
            height: 1
            color: index === 0 ? "#ffffff" : index < 4 ? "#cfe4ff" : index < 9 ? "#7f9fe8" : "#36437e"
        }
    }
}
