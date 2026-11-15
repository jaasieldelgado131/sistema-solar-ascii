import QtQuick

Item {
    id: body
    property real radius: 73
    property int kind: -1
    property real seconds: 0
    property bool labels: true
    property string caption: "SOL"
    readonly property real extent: radius * (kind === 5 ? 2.05 : kind < 0 ? 1.6 : 1.15)
    width: Math.ceil(extent * 2)
    height: width

    AnimatedSprite {
        anchors.fill: parent
        source: Qt.resolvedUrl("sprites/" + body.kind + ".png")
        frameCount: 48
        frameWidth: body.width
        frameHeight: body.height
        interpolate: false
        paused: true
        currentFrame: Math.floor(body.seconds * 4) % 48
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        y: body.height / 2 + body.radius + (body.kind === 5 ? 24 : 13)
        visible: body.labels
        text: body.caption
        color: body.kind < 0 ? "#c89556" : "#8394a8"
        font.family: "DejaVu Sans Mono"
        font.pixelSize: 9
        font.letterSpacing: 2.3
        opacity: 0.85
    }
}
