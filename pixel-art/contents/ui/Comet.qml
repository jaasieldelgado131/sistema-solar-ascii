pragma ComponentBehavior: Bound
import QtQuick
import "Geometry.js" as Geo

// Comet head with an ion tail (blue, straight away from the Sun) and a curved dust tail.
Item {
    id: comet
    property real seconds: 0
    property real orbitScale: 1
    readonly property var path: Geo.cometState(seconds, orbitScale)
    readonly property int tail: path.tail
    x: Math.round(path.x)
    y: Math.round(path.y)
    z: path.z
    visible: path.distance < 430

    Repeater {
        model: 26
        Rectangle {
            required property int index
            readonly property int step: index + 1
            readonly property real bend: 0.16 + step * 0.012
            readonly property real ux: comet.path.dx * Math.cos(bend) - comet.path.dy * Math.sin(bend)
            readonly property real uy: comet.path.dx * Math.sin(bend) + comet.path.dy * Math.cos(bend)
            visible: step <= comet.tail * 0.7
            x: Math.round(ux * step)
            y: Math.round(uy * step)
            width: 1
            height: 1
            color: step < comet.tail * 0.25 ? "#fff3d0" : step < comet.tail * 0.5 ? "#c8b48a" : "#6e6250"
        }
    }

    Repeater {
        model: 38
        Rectangle {
            required property int index
            readonly property int step: index + 1
            visible: step <= comet.tail
            x: Math.round(comet.path.dx * step)
            y: Math.round(comet.path.dy * step)
            width: 1
            height: 1
            color: step < comet.tail * 0.3 ? "#e4fbff" : step < comet.tail * 0.65 ? "#7fd0ff" : "#3e6cbc"
            opacity: step > comet.tail * 0.85 ? 0.6 : 1
        }
    }

    Rectangle { x: -1; y: 0; width: 3; height: 1; color: "#a8e8ff" }
    Rectangle { x: 0; y: -1; width: 1; height: 3; color: "#a8e8ff" }
    Rectangle { x: 0; y: 0; width: 1; height: 1; color: "#ffffff" }
}
