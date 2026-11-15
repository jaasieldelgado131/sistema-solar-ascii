pragma ComponentBehavior: Bound
import QtQuick
import "Space.js" as Space

Rectangle {
    id: scene
    color: "#050912"
    clip: true
    property real seconds: 0
    property real speed: 1
    property int fps: 30
    property bool playing: true
    property bool showLabels: true
    property real starDensity: 1
    readonly property var composition: Space.layout(width, height)

    Timer {
        id: clock
        property double lastTick: 0
        interval: Math.round(1000 / Math.max(10, Math.min(60, scene.fps)))
        running: scene.playing && scene.visible
        repeat: true
        onRunningChanged: lastTick = Date.now()
        onTriggered: {
            var now = Date.now();
            scene.seconds += Math.min((now - lastTick) / 1000, 0.2) * scene.speed;
            lastTick = now;
        }
    }

    StarField {
        anchors.fill: parent
        seconds: scene.seconds
        density: scene.starDensity
    }

    Item {
        id: system
        x: scene.composition.x
        y: scene.composition.y
        scale: scene.composition.scale

        Canvas {
            id: paths
            x: -940
            y: -550
            width: 1880
            height: 1100
            z: -1000
            onAvailableChanged: requestPaint()
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);
                ctx.font = "9px 'DejaVu Sans Mono'";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                for (var i = 0; i < Space.planets.length; i++) {
                    var orbit = Space.planets[i].orbit;
                    var count = Math.round(orbit * 0.6);
                    for (var n = 0; n < count; n++) {
                        var a = n * Space.tau / count;
                        var p = Space.orbitPoint(orbit, a);
                        ctx.fillStyle = n % 5 === 0 ? "#25384c" : "#1a2a3b";
                        ctx.fillText(".", 940 + p.x, 550 + p.y);
                    }
                }
                // Sparse ASCII dust between Mars and Jupiter.
                for (var k = 0; k < 410; k++) {
                    var dust = Space.orbitPoint(405 + Space.hash(k + 700) * 28, Space.hash(k + 1700) * Space.tau);
                    ctx.fillStyle = k % 7 === 0 ? "#6c655c" : "#353c43";
                    ctx.fillText(k % 11 === 0 ? ":" : ".", 940 + dust.x, 550 + dust.y);
                }
            }
        }

        AsciiBody {
            x: -width / 2
            y: -height / 2
            radius: 73
            seconds: scene.seconds
            labels: scene.showLabels
        }

        Repeater {
            model: Space.planets
            AsciiBody {
                required property var modelData
                readonly property var position: Space.planetPosition(modelData, scene.seconds)
                x: position.x - width / 2
                y: position.y - height / 2
                z: position.y
                radius: modelData.radius
                kind: modelData.kind
                caption: modelData.name
                seconds: scene.seconds
                labels: scene.showLabels
            }
        }

        // A small companion to Earth, also drawn with characters.
        Text {
            readonly property var earth: Space.planetPosition(Space.planets[2], scene.seconds)
            x: earth.x + Math.cos(scene.seconds * 0.22) * 39 - 4
            y: earth.y + Math.sin(scene.seconds * 0.22) * 26 - 5
            z: earth.y + 1
            text: "o"
            color: "#a3abb3"
            font.family: "DejaVu Sans Mono"
            font.pixelSize: 11
        }
    }

    Repeater {
        model: 3
        Text {
            required property int index
            readonly property var flight: Space.meteor(index, scene.seconds, scene.width, scene.height)
            x: flight.x
            y: flight.y
            opacity: flight.opacity
            rotation: 27
            transformOrigin: Item.Right
            text: ".  . . : : - = + *"
            color: index === 1 ? "#edc69b" : "#a1cedc"
            font.family: "DejaVu Sans Mono"
            font.pixelSize: 12
            font.letterSpacing: 2
        }
    }

}
