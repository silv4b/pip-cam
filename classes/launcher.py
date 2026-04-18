import os
import shutil
import cv2

from pygrabber.dshow_graph import FilterGraph
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QLineEdit,
    QColorDialog,
    QFileDialog,
    QLabel,
    QSlider,
)
from PyQt6.QtGui import (
    QGuiApplication,
    QIntValidator,
    QIcon,
    QColor,
    QImage,
    QPixmap,
    QPainter,
    QPainterPath,
    QPen,
)

from utils.functions import load_all_configs, resource_path, save_global_config
from classes.pip_camera_widget import PipCameraWidget


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        logo_path = resource_path("assets/pipcam_icon.ico")
        self.setWindowIcon(QIcon(logo_path))
        self.setWindowTitle("PiP Cam Setup")
        self.setFixedSize(440, 470)

        self.preview_cap = None
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
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
        self.size_input.editingFinished.connect(self.save_current_launcher_settings)
        form.addRow("Largura Inicial (px):", self.size_input)

        zoom_layout = QHBoxLayout()
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(100)
        self.zoom_slider.setMaximum(300)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setSingleStep(10)
        self.zoom_label = QLabel("1.0x")
        self.zoom_label.setFixedWidth(30)
        self.zoom_slider.valueChanged.connect(self.update_zoom_label)
        self.zoom_slider.sliderReleased.connect(self.save_current_launcher_settings)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_label)
        form.addRow("Zoom / Corte:", zoom_layout)

        pan_layout = QHBoxLayout()
        self.pan_slider = QSlider(Qt.Orientation.Horizontal)
        self.pan_slider.setMinimum(0)
        self.pan_slider.setMaximum(100)
        self.pan_slider.setValue(50)
        self.pan_slider.setSingleStep(5)
        self.pan_label = QLabel("Centro")
        self.pan_label.setFixedWidth(50)
        self.pan_slider.valueChanged.connect(self.update_pan_label)
        self.pan_slider.sliderReleased.connect(self.save_current_launcher_settings)
        pan_layout.addWidget(self.pan_slider)
        pan_layout.addWidget(self.pan_label)
        form.addRow("Alinhamento Y:", pan_layout)

        color_layout = QHBoxLayout()
        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("Ex: #4d6fc4")
        self.color_input.editingFinished.connect(self.save_current_launcher_settings)
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

        self.btn_preview_avatar = QPushButton("Testar")
        self.btn_preview_avatar.setCheckable(True)
        self.btn_preview_avatar.setToolTip("Alterna preview entre Câmera e Avatar")
        self.btn_preview_avatar.clicked.connect(self.save_current_launcher_settings)

        avatar_layout.addWidget(self.avatar_input)
        avatar_layout.addWidget(self.btn_avatar)
        avatar_layout.addWidget(self.btn_preview_avatar)
        form.addRow("Foto (Alt+A):", avatar_layout)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(280, 200)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_start = QPushButton("Iniciar Câmera")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setStyleSheet(
            "background-color: #4d6fc4; color: white; font-weight: bold; border-radius: 8px;"
        )
        self.btn_start.clicked.connect(self.start_pip)
        layout.addLayout(form)
        layout.addSpacing(20)
        layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(25)
        layout.addWidget(self.btn_start)
        self.setLayout(layout)

        self.cam_combo.currentIndexChanged.connect(self.restart_preview)
        self.cam_combo.currentIndexChanged.connect(self.apply_mode_preview)

        self.refresh_launcher_ui()

    def refresh_launcher_ui(self):
        self.all_configs = load_all_configs()
        self.apply_mode_preview()

        border_color = self.all_configs.get("border_color", "#4d6fc4")
        self.color_input.setText(border_color)

        avatar_path = self.all_configs.get("avatar_path", "")
        self.avatar_input.setText(avatar_path)

        # Carrega visualmente qual feed foi usado da última vez e aplica no preview
        use_avatar_default = self.all_configs.get("use_avatar", False)
        self.btn_preview_avatar.setChecked(use_avatar_default)

    def update_zoom_label(self, value):
        self.zoom_label.setText(f"{value / 100:.1f}x")

    def update_pan_label(self, value):
        if value < 45:
            self.pan_label.setText("Cima")
        elif value > 55:
            self.pan_label.setText("Baixo")
        else:
            self.pan_label.setText("Centro")

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
                self.save_current_launcher_settings()
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
            self.save_current_launcher_settings()

    def save_current_launcher_settings(self):
        cam_idx = self.cam_combo.currentData()
        if cam_idx is None or cam_idx == -1:
            return
            
        cam_name = self.cam_combo.currentText()
        mode = self.mode_combo.currentText()
        mode_key = f"{cam_name}_{mode}"
        
        try:
            size = int(self.size_input.text())
        except:  # noqa
            size = 300
            
        zoom_val = self.zoom_slider.value()
        pan_val = self.pan_slider.value()
        
        configs = load_all_configs()
        mode_cfg = configs.get(mode_key, configs.get(mode, {}))
        
        from utils.functions import save_mode_config
        save_mode_config(mode_key, size, zoom_val, pan_val, mode_cfg.get("x", 0), mode_cfg.get("y", 0))

        border_color = self.color_input.text().strip() or "#4d6fc4"
        save_global_config("border_color", border_color)
        
        avatar_path = self.avatar_input.text().strip()
        save_global_config("avatar_path", avatar_path)
        
        save_global_config("use_avatar", self.btn_preview_avatar.isChecked())

    def apply_mode_preview(self, *args):
        self.all_configs = load_all_configs()
        mode = self.mode_combo.currentText()
        cam_name = self.cam_combo.currentText()
        mode_key = f"{cam_name}_{mode}"

        mode_cfg = self.all_configs.get(mode_key, self.all_configs.get(mode, {}))
        self.size_input.setText(str(mode_cfg.get("size", "300")))

        # O slider muda sem emitir sinais se definirmos via blockSignals opcionalmente,
        # mas aqui setting o value atualiza o preview.
        self.zoom_slider.blockSignals(True)
        self.pan_slider.blockSignals(True)
        self.zoom_slider.setValue(mode_cfg.get("zoom", 100))
        self.pan_slider.setValue(mode_cfg.get("pan_y", 50))
        self.zoom_slider.blockSignals(False)
        self.pan_slider.blockSignals(False)

    def populate_cameras(self):
        try:
            devices = FilterGraph().get_input_devices()
            for index, name in enumerate(devices):
                self.cam_combo.addItem(name, index)
        except:  # noqa
            self.cam_combo.addItem("Erro ao detectar", -1)

    def showEvent(self, event):
        super().showEvent(event)
        self.restart_preview()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_preview()

    def stop_preview(self):
        self.preview_timer.stop()
        if self.preview_cap is not None:
            self.preview_cap.release()
            self.preview_cap = None

    def restart_preview(self, *args):
        if not self.isVisible():
            return
        self.stop_preview()
        cam_idx = self.cam_combo.currentData()
        if cam_idx is not None and cam_idx != -1:
            self.preview_cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
            self.preview_timer.start(30)

    def update_preview(self):
        use_avatar = (
            hasattr(self, "btn_preview_avatar") and self.btn_preview_avatar.isChecked()
        )
        avatar_pixmap = None

        if use_avatar:
            avatar_path = self.avatar_input.text().strip()
            if not avatar_path or not os.path.exists(avatar_path):
                use_avatar = False
            else:
                avatar_pixmap = QPixmap(avatar_path)
                if avatar_pixmap.isNull():
                    use_avatar = False

        if not use_avatar:
            if not self.preview_cap:
                return
            ret, frame = self.preview_cap.read()
            if not ret:
                return

            zoom_f = self.zoom_slider.value() / 100.0
            if zoom_f > 1.0:
                pan_val = self.pan_slider.value() / 100.0
                h_orig, w_orig, _ = frame.shape
                new_h = int(h_orig / zoom_f)
                new_w = int(w_orig / zoom_f)
                y_o = int((h_orig - new_h) * pan_val)
                x_o = (w_orig - new_w) // 2
                frame = frame[y_o:y_o+new_h, x_o:x_o+new_w]

        mode = self.mode_combo.currentText()
        h_ratio = 0.75 if "4:3" in mode else 1.0

        max_w, max_h = 240, 180
        curr_w = int(max_h / h_ratio) if (max_h / h_ratio) <= max_w else max_w
        curr_h = int(curr_w * h_ratio)

        self.preview_label.setFixedSize(curr_w, curr_h)

        if use_avatar and avatar_pixmap:
            scaled_avatar = avatar_pixmap.scaled(
                curr_w,
                curr_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x_offset = (scaled_avatar.width() - curr_w) // 2
            y_offset = (scaled_avatar.height() - curr_h) // 2
            pixmap = scaled_avatar.copy(x_offset, y_offset, curr_w, curr_h)
        else:
            h_f, w_f, _ = frame.shape
            target_ratio = curr_w / curr_h
            if (w_f / h_f) > target_ratio:
                new_w = int(h_f * target_ratio)
                offset = (w_f - new_w) // 2
                frame = frame[:, offset : offset + new_w]  # noqa
            else:
                new_h = int(w_f / target_ratio)
                offset = (h_f - new_h) // 2
                frame = frame[offset : offset + new_h, :]  # noqa

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
                curr_w,
                curr_h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        out_pixmap = QPixmap(curr_w, curr_h)
        out_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(out_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        border_color_str = self.color_input.text().strip() or "#4d6fc4"
        border_color = QColor(border_color_str)
        if not border_color.isValid():
            border_color = QColor("#4d6fc4")

        border_w = 4.0
        clip_margin = 1.5

        video_path = QPainterPath()
        if mode == "Círculo":
            video_path.addEllipse(
                clip_margin,
                clip_margin,
                curr_w - 2 * clip_margin,
                curr_h - 2 * clip_margin,
            )
        else:
            video_path.addRoundedRect(
                clip_margin,
                clip_margin,
                curr_w - 2 * clip_margin,
                curr_h - 2 * clip_margin,
                15,
                15,
            )

        painter.setClipPath(video_path)
        painter.drawPixmap(0, 0, pixmap)
        painter.setClipping(False)

        border_path = QPainterPath()
        offset_b = border_w / 2.0
        if mode == "Círculo":
            border_path.addEllipse(
                offset_b, offset_b, curr_w - border_w, curr_h - border_w
            )
        else:
            border_path.addRoundedRect(
                offset_b,
                offset_b,
                curr_w - border_w,
                curr_h - border_w,
                15 - offset_b,
                15 - offset_b,
            )

        pen = QPen(border_color)
        pen.setWidthF(border_w)
        painter.setPen(pen)
        painter.drawPath(border_path)

        painter.end()
        self.preview_label.setPixmap(out_pixmap)

    def start_pip(self):
        self.stop_preview()
        cam_idx = self.cam_combo.currentData()
        if cam_idx == -1:
            return
        cam_name = self.cam_combo.currentText()
        mode = self.mode_combo.currentText()
        mode_key = f"{cam_name}_{mode}"

        try:
            size = int(self.size_input.text())
        except:  # noqa
            size = 300
        border_color = self.color_input.text().strip() or "#4d6fc4"
        save_global_config("border_color", border_color)

        avatar_path = self.avatar_input.text().strip()
        save_global_config("avatar_path", avatar_path)

        zoom_val = self.zoom_slider.value()
        pan_val = self.pan_slider.value()

        self.save_current_launcher_settings()

        configs = load_all_configs()
        mode_cfg = configs.get(mode_key, configs.get(mode, {}))
        use_avatar_default = self.btn_preview_avatar.isChecked()

        screen = QGuiApplication.primaryScreen().geometry()  # type: ignore

        # Pega a posição do config ou centraliza
        pos_x = mode_cfg.get("x", (screen.width() - size) // 2)
        pos_y = mode_cfg.get("y", (screen.height() - size) // 2)

        self.pip = PipCameraWidget(
            size,
            cam_idx,
            self,
            mode,
            mode_key,
            pos_x,
            pos_y,
            zoom_val,
            pan_val,
            border_color,
            avatar_path,
            use_avatar_default,
        )
        self.pip.show()
        self.hide()
