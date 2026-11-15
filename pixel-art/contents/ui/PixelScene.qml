pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import "Atlas.js" as Atlas
import "Geometry.js" as Geo

// The whole system is drawn at ~640x400 "art pixels" and then enlarged with
// nearest-neighbour sampling, so every pixel stays a crisp square on screen.
Rectangle {
    id: scene
    color: "#04050d"
    clip: true
    property real seconds: 0
    property real speed: 1
    property int fps: 30
    property bool playing: true
    property bool showLabels: true
    property bool showOrbits: true
    property bool showExtras: true
    property bool crt: false
    property real starDensity: 1
    property int pixelSize: 0          // 0 = automático
    readonly property real dpr: Screen.devicePixelRatio > 0 ? Screen.devicePixelRatio : 1
    readonly property int px: pixelSize > 0 ? pixelSize : Geo.autoPixel(width * dpr, height * dpr)
    readonly property var composition: Geo.layout(art.width, art.height)
    readonly property real orbitScale: composition.scale
    // Slow things (belt, sparkles, twinkle) only need 8 updates per second.
    readonly property real tick: Math.floor(seconds * 8) / 8

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

    Item {
        id: art
        width: Math.max(1, Math.ceil(scene.width * scene.dpr / scene.px))
        height: Math.max(1, Math.ceil(scene.height * scene.dpr / scene.px))

        Image {
            x: Math.round((art.width - Atlas.data.nebula.w) / 2)
            y: Math.round((art.height - Atlas.data.nebula.h) / 2)
            source: Atlas.data.nebula.src
            smooth: false
        }

        Repeater {
            model: 3
            Canvas {
                id: stars
                required property int index
                anchors.fill: parent
                opacity: index === 0 ? 0.85 : 0.6 + 0.35 * Math.sin(scene.tick * 0.9 + index * 2.1)
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onAvailableChanged: requestPaint()
                Connections {
                    target: scene
                    function onStarDensityChanged() { stars.requestPaint(); }
                }
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.clearRect(0, 0, width, height);
                    var tints = ["#c8d4f0", "#ffe2b0", "#a8c8ff", "#ffffff"];
                    var count = Math.floor(width * height / 700 * scene.starDensity);
                    for (var n = index; n < count; n += 3) {
                        var x = Math.floor(Geo.hash(n * 3 + 11) * width);
                        var y = Math.floor(Geo.hash(n * 3 + 12) * height);
                        var bright = Geo.hash(n * 3 + 13);
                        if (bright > 0.985) {
                            ctx.fillStyle = "#56628e";
                            ctx.fillRect(x - 1, y, 3, 1);
                            ctx.fillRect(x, y - 1, 1, 3);
                            ctx.fillStyle = "#ffffff";
                        } else if (bright > 0.86) {
                            ctx.fillStyle = tints[Math.floor(Geo.hash(n * 7 + 5) * 4)];
                        } else if (bright > 0.55) {
                            ctx.fillStyle = "#56628e";
                        } else {
                            ctx.fillStyle = "#2c3558";
                        }
                        ctx.fillRect(x, y, 1, 1);
                    }
                }
            }
        }

        // Bright stars that flare into four-point sparkles now and then.
        Repeater {
            model: Math.round(16 * scene.starDensity)
            SpriteFrame {
                required property int index
                readonly property real period: 5 + Geo.hash(index * 9 + 1) * 8
                readonly property real local: Geo.mod(scene.tick + Geo.hash(index * 9 + 2) * period, period)
                x: Math.round(Geo.hash(index * 9 + 3) * (art.width - 9))
                y: Math.round(Geo.hash(index * 9 + 4) * (art.height - 9))
                source: Atlas.data.sparkle.src
                frameWidth: Atlas.data.sparkle.w
                frameHeight: Atlas.data.sparkle.h
                column: local < 1.6 ? [1, 2, 3, 4, 4, 3, 2, 1][Math.min(7, Math.floor(local / 0.2))] : 0
            }
        }

        Repeater {
            model: scene.showExtras ? 2 : 0
            Meteor {
                required property int index
                seconds: scene.seconds
                areaWidth: art.width
                areaHeight: art.height
            }
        }

        Item {
            id: system
            x: scene.composition.x
            y: scene.composition.y

            Image {
                z: -20000
                x: -Atlas.data.halo.w / 2
                y: -Atlas.data.halo.h / 2
                source: Atlas.data.halo.src
                smooth: false
                opacity: 0.8 + 0.2 * Math.sin(scene.tick * 0.7)
            }

            Canvas {
                id: orbits
                z: -10000
                visible: scene.showOrbits
                x: -system.x
                y: -system.y
                width: art.width
                height: art.height
                onAvailableChanged: requestPaint()
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                Connections {
                    target: scene
                    function onOrbitScaleChanged() { orbits.requestPaint(); }
                }
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.clearRect(0, 0, width, height);
                    for (var i = 0; i < Geo.planets.length; i++) {
                        var a = Geo.planets[i].orbit * scene.orbitScale;
                        var b = a * Geo.squash;
                        var perimeter = Math.PI * (1.5 * (a + b) - Math.sqrt(a * b));
                        var count = Math.floor(perimeter / 5);
                        for (var n = 0; n < count; n++) {
                            var p = Geo.orbitPoint(a, n * Geo.tau / count);
                            ctx.fillStyle = n % 6 === 0 ? "#3a4a86" : "#243060";
                            ctx.fillRect(Math.round(system.x + p.x), Math.round(system.y + p.y), 1, 1);
                        }
                    }
                }
            }

            SpriteFrame {
                id: sun
                z: 0
                x: -Atlas.data.sun.w / 2
                y: -Atlas.data.sun.h / 2
                readonly property int frame: Math.floor(scene.seconds * 4) % Atlas.data.sun.frames
                source: Atlas.data.sun.src
                frameWidth: Atlas.data.sun.w
                frameHeight: Atlas.data.sun.h
                column: frame % Atlas.data.sun.cols
                row: Math.floor(frame / Atlas.data.sun.cols)
            }

            Image {
                z: 0.5
                visible: scene.showLabels
                x: -Math.floor(Atlas.data.labels.sol.w / 2)
                y: Math.round(Atlas.data.sun.radius * 1.85) + 1
                source: Atlas.data.labels.sol.src
                smooth: false
            }

            // Asteroid belt between Mars and Jupiter: each rock keeps its own pace.
            Repeater {
                model: 150
                Rectangle {
                    required property int index
                    readonly property real radius: (138 + Geo.hash(index * 3 + 1) * 18) * scene.orbitScale
                    readonly property real angle: Geo.hash(index * 3 + 3) * Geo.tau
                                                  + scene.tick * Geo.tau / (150 + Geo.hash(index * 3 + 2) * 50)
                    readonly property var point: Geo.orbitPoint(radius, angle)
                    readonly property bool big: Geo.hash(index * 7 + 5) > 0.9
                    x: Math.round(point.x)
                    y: Math.round(point.y)
                    z: Math.sin(angle) * radius
                    width: big ? 2 : 1
                    height: big && Geo.hash(index * 5 + 9) > 0.4 ? 2 : 1
                    color: ["#3a3638", "#5a5048", "#7a6c5c", "#9a8a74"][Math.floor(Geo.hash(index * 11 + 7) * 4)]
                }
            }

            Repeater {
                model: Geo.planets
                Body {
                    required property var modelData
                    info: modelData
                    seconds: scene.seconds
                    orbitScale: scene.orbitScale
                }
            }

            // Names sit above every body so a passing planet never cuts them.
            Repeater {
                model: scene.showLabels ? Geo.planets : []
                Image {
                    required property var modelData
                    readonly property var sprite: Atlas.data.bodies[modelData.key]
                    readonly property var plate: Atlas.data.labels[modelData.key]
                    readonly property var orbit: Geo.planetState(modelData, scene.seconds, scene.orbitScale)
                    z: 15000
                    // Hidden while the planet is behind the Sun's disc and corona.
                    visible: orbit.z > 0 || Math.sqrt(orbit.x * orbit.x + orbit.y * orbit.y) > Atlas.data.sun.radius * 1.9
                    x: Math.round(orbit.x) - Math.floor(plate.w / 2)
                    y: Math.round(orbit.y) + Math.max(sprite.radius + 3, sprite.h / 2 + 1)
                    source: plate.src
                    smooth: false
                    opacity: 0.9
                }
            }

            // The Moon shares Earth's light; it hides behind Earth on the far side.
            SpriteFrame {
                readonly property var earth: Geo.planetState(Geo.planets[2], scene.seconds, scene.orbitScale)
                readonly property var orbit: Geo.moon(13, 7, 0.3, scene.seconds)
                x: Math.round(earth.x + orbit.x) - width / 2
                y: Math.round(earth.y + orbit.y) - height / 2
                z: earth.z + (orbit.front ? 0.5 : -0.5)
                source: Atlas.data.bodies.luna.src
                frameWidth: Atlas.data.bodies.luna.w
                frameHeight: Atlas.data.bodies.luna.h
                row: earth.light
            }

            // Galilean moons and Titan as single bright pixels.
            Repeater {
                model: [
                    {planet: 4, radius: 21, period: 4, phase: 0.0, color: "#f2dc8c"},
                    {planet: 4, radius: 25, period: 7, phase: 2.1, color: "#d8d4cc"},
                    {planet: 4, radius: 30, period: 11, phase: 4.0, color: "#c4b8a4"},
                    {planet: 4, radius: 36, period: 18, phase: 1.2, color: "#9c9488"},
                    {planet: 5, radius: 36, period: 15, phase: 3.3, color: "#e8b05a"}
                ]
                Rectangle {
                    required property var modelData
                    readonly property var host: Geo.planetState(Geo.planets[modelData.planet], scene.seconds, scene.orbitScale)
                    readonly property var orbit: Geo.moon(modelData.radius, modelData.period, modelData.phase, scene.seconds)
                    x: Math.round(host.x + orbit.x)
                    y: Math.round(host.y + orbit.y)
                    z: host.z + (orbit.front ? 0.5 : -0.5)
                    width: 1
                    height: 1
                    color: modelData.color
                }
            }

            Comet {
                visible: scene.showExtras && path.distance < 430
                seconds: scene.seconds
                orbitScale: scene.orbitScale
            }

            Ship {
                z: 20000
                visible: scene.showExtras && mission.visible
                seconds: scene.seconds
                orbitScale: scene.orbitScale
            }
        }
    }

    ShaderEffectSource {
        id: screenImage
        sourceItem: art
        hideSource: true
        smooth: false
        mipmap: false
        live: true
        textureSize: Qt.size(art.width, art.height)
        width: art.width * scene.px / scene.dpr
        height: art.height * scene.px / scene.dpr
    }

    // Optional CRT look: a dark line under every row of art pixels.
    Loader {
        anchors.fill: parent
        active: scene.crt && scene.px >= 2
        sourceComponent: Item {
            Repeater {
                model: art.height
                Rectangle {
                    required property int index
                    y: (index + 1) * scene.px / scene.dpr - 1 / scene.dpr
                    width: parent.width
                    height: 1 / scene.dpr
                    color: "#000000"
                    opacity: 0.22
                }
            }
        }
    }
}
