pragma ComponentBehavior: Bound
import QtQuick
import "Space.js" as Space

Item {
    id: field
    property real seconds: 0
    property real density: 1

    Repeater {
        model: 3
        Canvas {
            id: stars
            required property int index
            anchors.fill: parent
            opacity: index === 0 ? 0.52 : 0.56 + 0.23 * Math.sin(field.seconds * 0.65 + index * 2.1)
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onAvailableChanged: requestPaint()
            Connections {
                target: field
                function onDensityChanged() { stars.requestPaint(); }
            }
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);
                ctx.font = "10px 'DejaVu Sans Mono'";
                var count = Math.floor(width * height / 4100 * field.density);
                for (var n = index; n < count; n += 3) {
                    var x = Space.hash(n * 3 + 11) * width;
                    var y = Space.hash(n * 3 + 12) * height;
                    var bright = Space.hash(n * 3 + 13);
                    ctx.fillStyle = bright > 0.95 ? "#b6c5cf" : bright > 0.72 ? "#65829c" : "#3a526c";
                    ctx.fillText(bright > 0.98 ? "+" : bright > 0.91 ? "*" : ".", x, y);
                }
            }
        }
    }
}
