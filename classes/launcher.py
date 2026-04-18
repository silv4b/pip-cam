import os
import shutil

from pygrabber.dshow_graph import FilterGraph
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QColorDialog,
    QFileDialog,
)
from PyQt6.QtGui import QGuiApplication, QIntValidator, QIcon, QColor

from utils.functions import load_all_configs, resource_path, save_global_config
from classes.pip_camera_widget import PipCameraWidget


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        logo_path = resource_path("assets/pipcam_icon.ico")
        self.setWindowIcon(QIcon(logo_path))
        self.setWindowTitle("PiP Cam Setup")
        self.setFixedSize(380, 420)
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

        color_layout = QHBoxLayout()
        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("Ex: #4d6fc4")
        self.btn_color = QPushButton("Cor")
        self.btn_color.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_input)
        color_layout.addWidget(self.btn_color)
        form.addRow("Cor da Borda:", color_layout)

        avatar_layout = QHBoxLayout()
        self.avatar_input = QLineEdit()
        self.avatar_input.setPlaceholderText("Nenhuma foto selecionada")
        self.avatar_input.setReadOnly(True)
        self.btn_avatar = QPushButton("Procurar")
        self.btn_avatar.clicked.connect(self.choose_avatar)
        avatar_layout.addWidget(self.avatar_input)
        avatar_layout.addWidget(self.btn_avatar)
        form.addRow("Foto (Alt+A):", avatar_layout)

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

        border_color = self.all_configs.get("border_color", "#4d6fc4")
        self.color_input.setText(border_color)

        avatar_path = self.all_configs.get("avatar_path", "")
        self.avatar_input.setText(avatar_path)

    def choose_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Escolha um Avatar", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            os.makedirs("avatar", exist_ok=True)
            filename = os.path.basename(file_path)
            dest_path = os.path.join("avatar", filename)
            try:
                shutil.copy(file_path, dest_path)
                self.avatar_input.setText(dest_path)
            except Exception as e:
                print(f"Erro ao copiar avatar: {e}")

    def choose_color(self):
        current_color_str = self.color_input.text().strip() or "#4d6fc4"
        current_color = QColor(current_color_str)
        if not current_color.isValid():
            current_color = QColor("#4d6fc4")
        color = QColorDialog.getColor(current_color, self, "Escolha a cor da borda")
        if color.isValid():
            self.color_input.setText(color.name())

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
        border_color = self.color_input.text().strip() or "#4d6fc4"
        save_global_config("border_color", border_color)

        avatar_path = self.avatar_input.text().strip()
        save_global_config("avatar_path", avatar_path)

        configs = load_all_configs()
        mode_cfg = configs.get(mode, {})
        use_avatar_default = configs.get("use_avatar", False)

        screen = QGuiApplication.primaryScreen().geometry()  # type: ignore

        # Pega a posição do config ou centraliza
        pos_x = mode_cfg.get("x", (screen.width() - size) // 2)
        pos_y = mode_cfg.get("y", (screen.height() - size) // 2)

        self.pip = PipCameraWidget(
            size,
            cam_idx,
            self,
            mode,
            pos_x,
            pos_y,
            border_color,
            avatar_path,
            use_avatar_default,
        )
        self.pip.show()
        self.hide()
