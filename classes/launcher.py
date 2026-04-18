from pygrabber.dshow_graph import FilterGraph
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QFormLayout,
    QLineEdit,
)
from PyQt6.QtGui import QGuiApplication, QIntValidator, QIcon

from utils.functions import load_all_configs, resource_path
from classes.pip_camera_widget import PipCameraWidget


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        logo_path = resource_path("assets/pipcam_icon.ico")
        self.setWindowIcon(QIcon(logo_path))
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
            "background-color: #4d6fc4; color: white; font-weight: bold; border-radius: 8px;"
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
        try:
            devices = FilterGraph().get_input_devices()
            for index, name in enumerate(devices):
                self.cam_combo.addItem(name, index)
        except:  # noqa
            self.cam_combo.addItem("Erro ao detectar", -1)

    def start_pip(self):
        cam_idx = self.cam_combo.currentData()
        if cam_idx == -1:
            return
        mode = self.mode_combo.currentText()
        try:
            size = int(self.size_input.text())
        except:  # noqa
            size = 300
        configs = load_all_configs()
        mode_cfg = configs.get(mode, {})
        screen = QGuiApplication.primaryScreen().geometry()  # type: ignore

        # Pega a posição do config ou centraliza
        pos_x = mode_cfg.get("x", (screen.width() - size) // 2)
        pos_y = mode_cfg.get("y", (screen.height() - size) // 2)

        self.pip = PipCameraWidget(size, cam_idx, self, mode, pos_x, pos_y)
        self.pip.show()
        self.hide()
