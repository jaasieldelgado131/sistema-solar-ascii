import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    id: form
    property alias formLayout: form
    property real cfg_Speed: 1
    property int cfg_Fps: 30
    property alias cfg_ShowLabels: labels.checked
    property real cfg_StarDensity: 1
    property alias cfg_Paused: paused.checked

    Controls.Slider {
        Kirigami.FormData.label: "Velocidad orbital:"
        from: 0.1
        to: 3
        stepSize: 0.1
        value: form.cfg_Speed
        onMoved: form.cfg_Speed = value
        Controls.ToolTip.visible: hovered || pressed
        Controls.ToolTip.text: value.toFixed(1) + "x"
    }
    Controls.ComboBox {
        Kirigami.FormData.label: "Fluidez:"
        model: ["15 FPS · ahorro", "24 FPS", "30 FPS · equilibrado", "60 FPS"]
        currentIndex: [15, 24, 30, 60].indexOf(form.cfg_Fps)
        onActivated: form.cfg_Fps = [15, 24, 30, 60][currentIndex]
    }
    Controls.Slider {
        Kirigami.FormData.label: "Cantidad de estrellas:"
        from: 0.25
        to: 2
        stepSize: 0.25
        value: form.cfg_StarDensity
        onMoved: form.cfg_StarDensity = value
    }
    Controls.CheckBox {
        id: labels
        text: "Mostrar nombres de los planetas"
        checked: true
    }
    Controls.CheckBox {
        id: paused
        text: "Pausar animación"
    }
    Controls.Label {
        Layout.fillWidth: true
        Layout.maximumWidth: 430
        text: "El movimiento y los tamaños son artísticos. La animación se pausa al bloquear la sesión."
        wrapMode: Text.WordWrap
        opacity: 0.7
    }
}
