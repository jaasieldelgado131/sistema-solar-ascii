import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    id: form
    property alias formLayout: form
    property real cfg_Speed: 1
    property int cfg_Fps: 30
    property int cfg_PixelSize: 0
    property real cfg_StarDensity: 1
    property alias cfg_ShowLabels: labels.checked
    property alias cfg_ShowOrbits: orbits.checked
    property alias cfg_ShowExtras: extras.checked
    property alias cfg_Crt: crt.checked
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
        currentIndex: Math.max(0, [15, 24, 30, 60].indexOf(form.cfg_Fps))
        onActivated: form.cfg_Fps = [15, 24, 30, 60][currentIndex]
    }
    Controls.ComboBox {
        Kirigami.FormData.label: "Tamaño del píxel:"
        model: ["Automático", "2 px · más detalle", "3 px", "4 px · más retro"]
        currentIndex: Math.max(0, [0, 2, 3, 4].indexOf(form.cfg_PixelSize))
        onActivated: form.cfg_PixelSize = [0, 2, 3, 4][currentIndex]
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
        Kirigami.FormData.label: "Mostrar:"
        text: "Nombres de los planetas"
        checked: true
    }
    Controls.CheckBox {
        id: orbits
        text: "Órbitas punteadas"
        checked: true
    }
    Controls.CheckBox {
        id: extras
        text: "Cometa, estrellas fugaces y nave"
        checked: true
    }
    Controls.CheckBox {
        id: crt
        text: "Efecto CRT (líneas de barrido)"
    }
    Controls.CheckBox {
        id: paused
        text: "Pausar animación"
    }
    Controls.Label {
        Layout.fillWidth: true
        Layout.maximumWidth: 430
        text: "Tamaños y velocidades son artísticos. Cada planeta se ilumina desde el Sol según su posición. La animación se pausa al bloquear la sesión."
        wrapMode: Text.WordWrap
        opacity: 0.7
    }
}
