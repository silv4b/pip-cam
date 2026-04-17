import sys
import cv2
import json
import os
import platform  # Para detectar o sistema operacional

# Importação condicional para evitar erro no Linux
if platform.system() == "Windows":
    try:
        from pygrabber.dshow_graph import FilterGraph

        HAS_PYGRABBER = True
    except ImportError:
        HAS_PYGRABBER = False
    import keyboard

    HAS_KEYBOARD = True
else:
    HAS_PYGRABBER = False
    HAS_KEYBOARD = False  # keyboard no Linux exige root e mapeamento diferente

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
)
from PyQt6.QtCore import QTimer, Qt, QPoint, pyqtSignal, QObject
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QPainter,
    QPainterPath,
    QGuiApplication,
    QIntValidator,
)

CONFIG_FILE = "pip_config.json"


def load_all_configs():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_mode_config(mode_name, size, x, y):
    configs = load_all_configs()
    configs[mode_name] = {"size": size, "x": x, "y": y}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(configs, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar: {e}")


class ShortcutSignals(QObject):
    resize_signal = pyqtSignal(int)
    toggle_signal = pyqtSignal()


class PipCameraWidget(QWidget):
    def __init__(self, size_val, cam_index, launcher, mode, pos_x, pos_y):
        super().__init__()
        self.launcher = launcher
        self.base_width = size_val
        self.cam_index = cam_index
        self.mode = mode
        self.target_pos = QPoint(pos_x, pos_y)

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.old_pos = None
        self._initializing = True

        self.video_label = QLabel(self)

        self.controls_container = QWidget(self)
        self.controls_layout = QHBoxLayout(self.controls_container)
        self.controls_layout.setContentsMargins(8, 0, 8, 0)
        self.controls_layout.setSpacing(12)

        self.btn_minus = self.create_button("-")
        self.btn_close = self.create_button("X", is_close=True)
        self.btn_plus = self.create_button("+")

        self.controls_layout.addWidget(self.btn_minus)
        self.controls_layout.addWidget(self.btn_close)
        self.controls_layout.addWidget(self.btn_plus)

        self.btn_minus.clicked.connect(lambda: self.resize_widget(-20))
        self.btn_plus.clicked.connect(lambda: self.resize_widget(20))
        self.btn_close.clicked.connect(self.close_and_return)

        self.controls_container.hide()
        self.update_ui_geometry()

        # Seleção de Backend: DSHOW para Windows, V4L2 para Linux
        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_V4L2
        self.cap = cv2.VideoCapture(self.cam_index, backend)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Atalhos apenas no Windows (Keyboard no Linux requer privilégios de root)
        if HAS_KEYBOARD:
            self.shortcut_manager = ShortcutSignals()
            self.shortcut_manager.resize_signal.connect(self.resize_widget)
            self.shortcut_manager.toggle_signal.connect(self.toggle_visibility)
            try:
                keyboard.add_hotkey(
                    "alt+=", lambda: self.shortcut_manager.resize_signal.emit(20)
                )
                keyboard.add_hotkey(
                    "alt+-", lambda: self.shortcut_manager.resize_signal.emit(-20)
                )
                keyboard.add_hotkey(
                    "alt+s", lambda: self.shortcut_manager.toggle_signal.emit()
                )
            except:
                pass

    def toggle_visibility(self):
        if self.isVisible():
            self.target_pos = self.pos()
            self.hide()
        else:
            self.show()
            self.move(self.target_pos)
            self.activateWindow()

    def showEvent(self, event):
        super().showEvent(event)
        self.move(self.target_pos)
        self._initializing = False

    def create_button(self, icon_text, is_close=False):
        btn = QPushButton(icon_text)
        btn.setFixedSize(32, 32)
        bg = "rgba(220, 50, 50, 200)" if is_close else "rgba(40, 40, 40, 180)"
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {bg}; color: white; border-radius: 16px; border: 1px solid rgba(255,255,255,60); font-weight: bold; }}"
        )
        return btn

    def update_ui_geometry(self):
        h_ratio = 0.75 if "4:3" in self.mode else 1.0
        self.curr_w = self.base_width
        self.curr_h = int(self.base_width * h_ratio)
        self.setFixedSize(self.curr_w, self.curr_h)
        self.video_label.setGeometry(0, 0, self.curr_w, self.curr_h)

        container_w, container_h = 150, 50
        self.controls_container.setGeometry(
            int((self.curr_w - container_w) / 2),
            int(self.curr_h - container_h - 10),
            container_w,
            container_h,
        )
        if not self._initializing:
            self.store_current_state()

    def resize_widget(self, delta):
        new_size = self.base_width + delta
        if 200 <= new_size <= 800:
            self.base_width = new_size
            self.update_ui_geometry()

    def store_current_state(self):
        if self.x() <= 0 and self.y() <= 0:
            return
        self.target_pos = self.pos()
        save_mode_config(self.mode, self.base_width, self.x(), self.y())

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            h_f, w_f, _ = frame.shape
            target_ratio = self.curr_w / self.curr_h
            if (w_f / h_f) > target_ratio:
                new_w = int(h_f * target_ratio)
                offset = (w_f - new_w) // 2
                frame = frame[:, offset : offset + new_w]
            else:
                new_h = int(w_f / target_ratio)
                offset = (h_f - new_h) // 2
                frame = frame[offset : offset + new_h, :]

            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qt_img = QImage(
                frame.data,
                frame.shape[1],
                frame.shape[0],
                frame.shape[1] * 3,
                QImage.Format.Format_RGB888,
            )
            pixmap = QPixmap.fromImage(qt_img).scaled(
                self.curr_w,
                self.curr_h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            out_pixmap = QPixmap(self.curr_w, self.curr_h)
            out_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(out_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            if self.mode == "Círculo":
                path.addEllipse(0, 0, self.curr_w, self.curr_h)
            else:
                path.addRoundedRect(0, 0, self.curr_w, self.curr_h, 25, 25)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            self.video_label.setPixmap(out_pixmap)

    def enterEvent(self, event):
        self.controls_container.show()

    def leaveEvent(self, event):
        self.controls_container.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None
            self.store_current_state()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_and_return()

    def close_and_return(self):
        if HAS_KEYBOARD:
            try:
                keyboard.remove_all_hotkeys()
            except:
                pass
        self.store_current_state()
        self.cap.release()
        self.close()
        self.launcher.refresh_launcher_ui()
        self.launcher.show()


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PiP Cam Setup")
        self.setFixedSize(380, 320)
        layout = QVBoxLayout()
        form = QFormLayout()
        self.cam_combo = QComboBox()
        self.populate_cameras()
        form.addRow("Câmera:", self.cam_combo)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Círculo", "1:1 (Quadrado)", "4:3 (Retângulo)"])
        self.mode_combo.currentTextChanged.connect(self.apply_mode_preview)
        form.addRow("Formato:", self.mode_combo)
        self.size_input = QLineEdit()
        self.size_input.setValidator(QIntValidator(100, 2000, self))
        form.addRow("Largura Inicial (px):", self.size_input)
        self.btn_start = QPushButton("Iniciar Câmera")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setStyleSheet(
            "background-color: #2ecc71; color: white; font-weight: bold; border-radius: 8px;"
        )
        self.btn_start.clicked.connect(self.start_pip)
        layout.addLayout(form)
        layout.addSpacing(20)
        layout.addWidget(self.btn_start)
        self.setLayout(layout)
        self.refresh_launcher_ui()

    def refresh_launcher_ui(self):
        self.all_configs = load_all_configs()
        self.apply_mode_preview()

    def apply_mode_preview(self):
        mode = self.mode_combo.currentText()
        mode_cfg = self.all_configs.get(mode, {})
        self.size_input.setText(str(mode_cfg.get("size", "300")))

    def populate_cameras(self):
        if HAS_PYGRABBER:
            try:
                devices = FilterGraph().get_input_devices()
                for index, name in enumerate(devices):
                    self.cam_combo.addItem(name, index)
            except:
                self.cam_combo.addItem("Erro ao detectar", -1)
        else:
            # Fallback para Linux: Detecção via OpenCV simples
            for i in range(5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    self.cam_combo.addItem(f"Dispositivo de Vídeo {i}", i)
                    cap.release()
            if self.cam_combo.count() == 0:
                self.cam_combo.addItem("Nenhuma câmera detectada", -1)

    def start_pip(self):
        cam_idx = self.cam_combo.currentData()
        if cam_idx == -1:
            return
        mode = self.mode_combo.currentText()
        try:
            size = int(self.size_input.text())
        except:
            size = 300
        configs = load_all_configs()
        mode_cfg = configs.get(mode, {})
        screen = QGuiApplication.primaryScreen().geometry()
        pos_x = mode_cfg.get("x", (screen.width() - size) // 2)
        pos_y = mode_cfg.get("y", (screen.height() - size) // 2)
        self.pip = PipCameraWidget(size, cam_idx, self, mode, pos_x, pos_y)
        self.pip.show()
        self.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())
