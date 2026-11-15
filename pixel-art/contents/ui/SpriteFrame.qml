import QtQuick

// One frame of a sprite atlas, clipped and never filtered.
Item {
    id: frame
    property url source
    property int frameWidth: 1
    property int frameHeight: 1
    property int column: 0
    property int row: 0
    width: frameWidth
    height: frameHeight
    clip: true

    Image {
        x: -frame.column * frame.frameWidth
        y: -frame.row * frame.frameHeight
        source: frame.source
        smooth: false
        mipmap: false
    }
}
