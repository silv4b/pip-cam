import os
import shutil
from PyQt6.QtCore import QTimer, Qt
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
    QLabel,
    QSlider,
    QCheckBox,
    QMessageBox,
)
from PyQt6.QtGui import QGuiApplication, QIntValidator, QIcon, QColor, QPixmap
from utils.functions import resource_path
from classes.views.pip_widget import PipCameraWidget
from classes.core.device_manager import DeviceManager
from classes.ui.filter_dialogs import FilterDialog
from classes.core.config_manager import ConfigManager


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        logo_path = resource_path("assets/pipcam_icon.ico")
        self.setWindowIcon(QIcon(logo_path))
        self.setWindowTitle("PiP Cam Setup")
        self.setFixedSize(440, 810)

        self.config_manager = ConfigManager()
        self.all_configs = self.config_manager.configs
        self.preview_cap = None
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)

        # Timer para retomar o preview após mover a janela
        self.resume_timer = QTimer()
        self.resume_timer.setSingleShot(True)
        self.resume_timer.timeout.connect(self.resume_preview)

        self.active_pips = []
        layout = QVBoxLayout()
        self.form = QFormLayout()
        self.form.setVerticalSpacing(12)
        self.form.setSpacing(10)
        cam_layout = QHBoxLayout()
        self.cam_combo = QComboBox()
        self.cam_combo.setFixedHeight(26)
        self.btn_filter = QPushButton("⚙️")
        self.btn_filter.setFixedSize(40, 26)
        self.btn_filter.setToolTip("Filtrar câmeras (Ignorar)")
        self.btn_filter.clicked.connect(self.open_camera_filters)
        self.populate_cameras()
        cam_layout.addWidget(self.cam_combo)
        cam_layout.addWidget(self.btn_filter)
        self.form.addRow("Câmera:", cam_layout)
        self.mode_combo = QComboBox()
        self.mode_combo.setFixedHeight(26)
        self.mode_combo.addItems(["Círculo", "1:1 (Quadrado)", "4:3 (Retângulo)"])
        self.mode_combo.currentTextChanged.connect(self.apply_mode_preview)
        self.mode_combo.currentTextChanged.connect(self.save_current_launcher_settings)
        self.form.addRow("Formato:", self.mode_combo)
        self.size_input = QLineEdit()
        self.size_input.setFixedHeight(26)
        self.size_input.setValidator(QIntValidator(100, 2000, self))
        self.size_input.editingFinished.connect(self.save_current_launcher_settings)
        self.form.addRow("Largura Inicial (px):", self.size_input)

        zoom_layout = QHBoxLayout()
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(100)
        self.zoom_slider.setMaximum(500)
        self.zoom_slider.setValue(100)
        self.zoom_label = QLabel("1.0x")
        self.zoom_label.setFixedWidth(30)
        self.zoom_slider.valueChanged.connect(self.update_zoom_label)
        self.zoom_slider.valueChanged.connect(self.save_current_launcher_settings)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_label)
        self.form.addRow("Zoom / Corte:", zoom_layout)

        pan_layout = QHBoxLayout()
        self.pan_slider = QSlider(Qt.Orientation.Horizontal)
        self.pan_slider.setMinimum(0)
        self.pan_slider.setMaximum(100)
        self.pan_slider.setValue(50)
        self.pan_slider.setSingleStep(5)
        self.pan_label = QLabel("Centro")
        self.pan_label.setFixedWidth(50)
        self.pan_slider.valueChanged.connect(self.update_pan_label)
        self.pan_slider.valueChanged.connect(self.save_current_launcher_settings)
        pan_layout.addWidget(self.pan_slider)
        pan_layout.addWidget(self.pan_label)
        self.form.addRow("Alinhamento Y:", pan_layout)

        pan_x_layout = QHBoxLayout()
        self.pan_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.pan_x_slider.setMinimum(0)
        self.pan_x_slider.setMaximum(100)
        self.pan_x_slider.setValue(50)
        self.pan_x_slider.setSingleStep(5)
        self.pan_x_label = QLabel("Centro")
        self.pan_x_label.setFixedWidth(50)
        self.pan_x_slider.valueChanged.connect(self.update_pan_x_label)
        self.pan_x_slider.valueChanged.connect(self.save_current_launcher_settings)
        pan_x_layout.addWidget(self.pan_x_slider)
        pan_x_layout.addWidget(self.pan_x_label)
        self.form.addRow("Alinhamento X:", pan_x_layout)

        self.border_mode_combo = QComboBox()
        self.border_mode_combo.setFixedHeight(26)
        self.border_mode_combo.addItems(["Cor Sólida", "Sinalizador de Áudio"])
        self.border_mode_combo.currentTextChanged.connect(self.toggle_border_config)
        self.border_mode_combo.currentTextChanged.connect(
            self.save_current_launcher_settings
        )
        self.form.addRow("Comportamento:", self.border_mode_combo)

        self.check_show_border = QCheckBox("Exibir Borda (Alt+B para Alternar)")
        self.check_show_border.setChecked(True)
        self.check_show_border.setMinimumHeight(30)
        self.check_show_border.stateChanged.connect(self.save_current_launcher_settings)
        self.form.addRow("", self.check_show_border)

        self.color_container = QWidget()
        color_layout = QHBoxLayout(self.color_container)
        color_layout.setContentsMargins(0, 2, 0, 2)
        color_layout.setSpacing(10)
        self.color_input = QLineEdit()
        self.color_input.setFixedHeight(26)
        self.color_input.setPlaceholderText("Ex: #4d6fc4")
        self.color_input.editingFinished.connect(self.save_current_launcher_settings)
        self.btn_color = QPushButton("Cor")
        self.btn_color.setFixedSize(60, 26)
        self.btn_color.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_input)
        color_layout.addWidget(self.btn_color)
        self.form.addRow("Cor da Borda:", self.color_container)

        # Microfone Section
        self.mic_label = QLabel("Microfone:")
        mic_top_layout = QHBoxLayout()
        self.mic_combo = QComboBox()
        self.mic_combo.setFixedHeight(26)
        self.btn_filter_mic = QPushButton("⚙️")
        self.btn_filter_mic.setFixedSize(40, 26)
        self.btn_filter_mic.setToolTip("Filtrar microfones (Ignorar)")
        self.btn_filter_mic.clicked.connect(self.open_mic_filters)
        self.populate_mics()
        mic_top_layout.addWidget(self.mic_combo)
        mic_top_layout.addWidget(self.btn_filter_mic)

        self.mic_combo.currentIndexChanged.connect(self.save_current_launcher_settings)
        self.check_mic_muted = QCheckBox("Iniciar Mutado (Alt+M para Alternar)")
        self.check_mic_muted.setMinimumHeight(30)
        self.check_mic_muted.setStyleSheet("padding-bottom: 5px;")
        self.check_mic_muted.stateChanged.connect(self.save_current_launcher_settings)

        self.form.addRow(self.mic_label, mic_top_layout)
        self.form.addRow("", self.check_mic_muted)

        audio_sensitivity_layout = QHBoxLayout()
        self.audio_sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.audio_sensitivity_slider.setMinimum(1)
        self.audio_sensitivity_slider.setMaximum(10)
        self.audio_sensitivity_slider.setValue(2)
        self.audio_sensitivity_slider.setToolTip(
            "Ajusta a amplificação do sinal do microfone"
        )
        self.audio_sensitivity_label = QLabel("2.0x")
        self.audio_sensitivity_label.setFixedWidth(35)
        self.audio_sensitivity_slider.valueChanged.connect(
            self.update_audio_sensitivity_label
        )
        self.audio_sensitivity_slider.valueChanged.connect(
            self.save_current_launcher_settings
        )
        audio_sensitivity_layout.addWidget(self.audio_sensitivity_slider)
        audio_sensitivity_layout.addWidget(self.audio_sensitivity_label)
        self.audio_sensitivity_container = QWidget()
        self.audio_sensitivity_container.setLayout(audio_sensitivity_layout)
        self.form.addRow("Sensibilidade Áudio:", self.audio_sensitivity_container)

        avatar_layout = QHBoxLayout()
        self.avatar_input = QLineEdit()
        self.avatar_input.setFixedHeight(26)
        self.avatar_input.setPlaceholderText("Nenhuma foto selecionada")
        self.avatar_input.setReadOnly(True)
        self.avatar_input.setFixedWidth(170)

        self.btn_avatar = QPushButton("Procurar")
        self.btn_avatar.setFixedSize(60, 26)
        self.btn_avatar.clicked.connect(self.choose_avatar)

        self.btn_preview_avatar = QPushButton("Testar")
        self.btn_preview_avatar.setFixedSize(60, 26)
        self.btn_preview_avatar.setCheckable(True)
        self.btn_preview_avatar.setToolTip("Alterna preview entre Câmera e Avatar")
        self.btn_preview_avatar.clicked.connect(self.save_current_launcher_settings)

        avatar_layout.addWidget(self.avatar_input)
        avatar_layout.addWidget(self.btn_avatar)
        avatar_layout.addWidget(self.btn_preview_avatar)
        self.form.addRow("Foto (Alt+A):", avatar_layout)

        self.check_multi_cam = QCheckBox("Modo Multi-Câmeras (Abrir vários widgets)")
        self.check_multi_cam.stateChanged.connect(self.save_current_launcher_settings)
        self.form.addRow("", self.check_multi_cam)

        self.check_hide_toolbar = QCheckBox(
            "Ocultar controles flutuantes (Usar apenas atalhos)"
        )
        self.check_hide_toolbar.stateChanged.connect(
            self.save_current_launcher_settings
        )
        self.form.addRow("", self.check_hide_toolbar)

        # Preview do Setup
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(350, 260)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Botões de Ação Inferiores
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.btn_start = QPushButton("Iniciar Câmera")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setStyleSheet(
            "background-color: #4d6fc4; color: white; font-weight: bold; border-radius: 8px;"
        )
        self.btn_start.clicked.connect(self.start_pip)

        self.btn_reset = QPushButton("🗑️")
        self.btn_reset.setFixedSize(50, 50)
        self.btn_reset.setToolTip("Resetar Configurações")
        self.btn_reset.setStyleSheet(
            "background-color: #f44336; color: white; font-size: 20px; border-radius: 8px;"
        )
        self.btn_reset.clicked.connect(self.confirm_reset_settings)

        actions_layout.addWidget(self.btn_start, 7)  # Proporção 7 de 8
        actions_layout.addWidget(self.btn_reset, 1)  # Proporção 1 de 8

        layout.addLayout(self.form)
        layout.addSpacing(20)
        layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addLayout(actions_layout)
        self.setLayout(layout)

        self.cam_combo.currentIndexChanged.connect(self.restart_preview)
        self.cam_combo.currentIndexChanged.connect(self.apply_mode_preview)
        self.cam_combo.currentIndexChanged.connect(self.save_current_launcher_settings)

        self.refresh_launcher_ui()
        self.init_global_hotkeys()

    def init_global_hotkeys(self):
        from classes.core.hotkey_manager import HotkeyManager

        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.setup_global_hotkeys()
        self.shortcut_manager = self.hotkey_manager.signals

    def refresh_launcher_ui(self):
        self.all_configs = self.config_manager.reload()

        # Bloqueia sinais para evitar loops de salvamento durante o carregamento
        self.cam_combo.blockSignals(True)
        self.mode_combo.blockSignals(True)
        self.border_mode_combo.blockSignals(True)
        self.mic_combo.blockSignals(True)
        self.zoom_slider.blockSignals(True)
        self.pan_slider.blockSignals(True)
        self.pan_x_slider.blockSignals(True)
        self.audio_sensitivity_slider.blockSignals(True)
        self.check_mic_muted.blockSignals(True)
        self.btn_preview_avatar.blockSignals(True)

        self.populate_cameras()

        # Restaura a última câmera selecionada
        last_cam = self.all_configs.get("last_camera_name")
        if last_cam:
            idx = self.cam_combo.findText(last_cam)
            if idx != -1:
                self.cam_combo.setCurrentIndex(idx)

        # Restaura o último formato selecionado
        last_mode = self.all_configs.get("last_mode")
        if last_mode:
            self.mode_combo.setCurrentText(last_mode)

        self.populate_mics()
        self.apply_mode_preview()

        border_color = self.all_configs.get("border_color", "#4d6fc4")
        self.color_input.setText(border_color)

        avatar_path = self.all_configs.get("avatar_path", "")
        self.avatar_input.setText(avatar_path)

        # Carrega visualmente qual feed foi usado da última vez e aplica no preview
        use_avatar_default = self.all_configs.get("use_avatar", False)
        self.btn_preview_avatar.setChecked(use_avatar_default)

        border_mode = self.all_configs.get("border_mode", "Cor Sólida")
        self.border_mode_combo.setCurrentText(border_mode)

        saved_mic_idx = self.all_configs.get("mic_device", -1)
        if saved_mic_idx != -1:
            idx = self.mic_combo.findData(saved_mic_idx)
            if idx != -1:
                self.mic_combo.setCurrentIndex(idx)

        self.check_mic_muted.setChecked(self.all_configs.get("starts_muted", False))
        self.check_multi_cam.setChecked(self.all_configs.get("multi_cam_mode", False))
        self.check_hide_toolbar.setChecked(self.all_configs.get("hide_toolbar", False))

        audio_sensitivity = self.all_configs.get("audio_sensitivity", 2.0)
        self.audio_sensitivity_slider.setValue(int(audio_sensitivity))
        self.audio_sensitivity_label.setText(f"{audio_sensitivity:.1f}x")

        # Desbloqueia e sincroniza
        self.cam_combo.blockSignals(False)
        self.mode_combo.blockSignals(False)
        self.border_mode_combo.blockSignals(False)
        self.mic_combo.blockSignals(False)
        self.zoom_slider.blockSignals(False)
        self.pan_slider.blockSignals(False)
        self.pan_x_slider.blockSignals(False)
        self.audio_sensitivity_slider.blockSignals(False)
        self.check_mic_muted.blockSignals(False)
        self.btn_preview_avatar.blockSignals(False)

        # Dispara manualmente as atualizações visuais
        self.toggle_border_config(border_mode)
        self.apply_mode_preview()

    def open_camera_filters(self):
        try:
            cameras = DeviceManager.get_cameras()
            ignored = self.all_configs.get("ignored_cameras", [])

            dialog = FilterDialog("Filtrar Câmeras", cameras, ignored, self)
            if dialog.exec():
                new_ignored = dialog.get_selected_items()
                self.config_manager.set_global("ignored_cameras", new_ignored)
                self.config_manager.save_now()
                self.all_configs = self.config_manager.configs
                self.populate_cameras()
        except Exception as e:
            print(f"Erro ao abrir filtros: {e}")

    def open_mic_filters(self):
        try:
            mics = DeviceManager.get_microphones()
            ignored = self.all_configs.get("ignored_mics", [])

            dialog = FilterDialog("Filtrar Microfones", mics, ignored, self)
            if dialog.exec():
                new_ignored = dialog.get_selected_items()
                self.config_manager.set_global("ignored_mics", new_ignored)
                self.config_manager.save_now()
                self.all_configs = self.config_manager.configs
                self.populate_mics()
        except Exception as e:
            print(f"Erro ao abrir filtros de mic: {e}")

    def update_zoom_label(self, value):
        self.zoom_label.setText(f"{value / 100:.1f}x")

    def update_pan_label(self, value):
        if value < 45:
            self.pan_label.setText("Cima")
        elif value > 55:
            self.pan_label.setText("Baixo")
        else:
            self.pan_label.setText("Centro")

    def update_pan_x_label(self, value):
        if value < 45:
            self.pan_x_label.setText("Esq.")
        elif value > 55:
            self.pan_x_label.setText("Dir.")
        else:
            self.pan_x_label.setText("Centro")

    def update_audio_sensitivity_label(self, value):
        self.audio_sensitivity_label.setText(f"{value / 1.0:.1f}x")

    def toggle_border_config(self, mode_text):
        is_solid = mode_text == "Cor Sólida"
        self.form.setRowVisible(self.color_container, is_solid)
        self.form.setRowVisible(self.mic_label, not is_solid)
        self.form.setRowVisible(self.check_mic_muted, not is_solid)
        self.form.setRowVisible(self.audio_sensitivity_container, not is_solid)

    def populate_mics(self):
        self.mic_combo.clear()
        try:
            all_mics = DeviceManager.get_microphones()
            ignored = self.all_configs.get("ignored_mics", [])
            for name in all_mics:
                if name not in ignored:
                    self.mic_combo.addItem(name, DeviceManager.get_mic_info(name))
        except Exception as e:
            print(f"Erro ao listar microfones: {e}")
            self.mic_combo.addItem("Erro ao detectar", -1)

    def choose_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Escolha um Avatar", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            from utils.functions import AVATAR_DIR

            os.makedirs(AVATAR_DIR, exist_ok=True)
            filename = os.path.basename(file_path)
            dest_path = os.path.join(AVATAR_DIR, filename)
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
        # Salvamos configurações GLOBAIS independentemente de ter câmera selecionada
        border_color = self.color_input.text().strip() or "#4d6fc4"
        self.config_manager.set_global("border_color", border_color)

        avatar_path = self.avatar_input.text().strip()
        self.config_manager.set_global("avatar_path", avatar_path)

        self.config_manager.set_global(
            "use_avatar", self.btn_preview_avatar.isChecked()
        )
        self.config_manager.set_global(
            "border_mode", self.border_mode_combo.currentText()
        )
        self.config_manager.set_global(
            "show_border", self.check_show_border.isChecked()
        )
        self.config_manager.set_global("last_camera_name", self.cam_combo.currentText())
        self.config_manager.set_global("last_mode", self.mode_combo.currentText())

        mic_data = self.mic_combo.currentData()
        self.config_manager.set_global(
            "mic_device", mic_data if mic_data is not None else -1
        )
        self.config_manager.set_global("starts_muted", self.check_mic_muted.isChecked())
        self.config_manager.set_global(
            "multi_cam_mode", self.check_multi_cam.isChecked()
        )
        self.config_manager.set_global(
            "hide_toolbar", self.check_hide_toolbar.isChecked()
        )
        self.config_manager.set_global(
            "audio_sensitivity", self.audio_sensitivity_slider.value()
        )

        # Configurações ESPECÍFICAS de câmera/modo
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
        pan_x_val = self.pan_x_slider.value()
        pan_val = self.pan_slider.value()

        self.config_manager.set_mode(
            mode_key,
            size,
            zoom_val,
            pan_x_val,
            pan_val,
            self.all_configs.get(mode_key, {}).get("x", 0),
            self.all_configs.get(mode_key, {}).get("y", 0),
        )
        self.all_configs = self.config_manager.configs

    def apply_mode_preview(self, *args):
        self.all_configs = self.config_manager.reload()
        mode = self.mode_combo.currentText()
        cam_name = self.cam_combo.currentText()
        mode_key = f"{cam_name}_{mode}"

        mode_cfg = self.config_manager.get_mode_config(mode_key, mode)
        self.size_input.setText(str(mode_cfg.get("size", "300")))

        # O slider muda sem emitir sinais se definirmos via blockSignals opcionalmente,
        # mas aqui setting o value atualiza o preview.
        self.zoom_slider.blockSignals(True)
        self.pan_slider.blockSignals(True)
        self.pan_x_slider.blockSignals(True)
        self.zoom_slider.setValue(mode_cfg.get("zoom", 100))
        self.pan_slider.setValue(mode_cfg.get("pan_y", 50))
        self.pan_x_slider.setValue(mode_cfg.get("pan_x", 50))
        self.zoom_slider.blockSignals(False)
        self.pan_slider.blockSignals(False)
        self.pan_x_slider.blockSignals(False)

    def populate_cameras(self):
        self.cam_combo.clear()
        try:
            all_devices = DeviceManager.get_cameras()
            ignored = self.all_configs.get("ignored_cameras", [])
            # Filtra as câmeras válidas (que não estão na lista de ignoradas)
            for name in all_devices:
                if name not in ignored:
                    self.cam_combo.addItem(name, DeviceManager.get_camera_index(name))
        except Exception as e:
            print(f"Erro ao carregar câmeras: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self.restart_preview()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_preview()

    def moveEvent(self, event):
        """Pausa o preview enquanto a janela está sendo movida para garantir fluidez."""
        super().moveEvent(event)
        if self.preview_timer.isActive():
            self.preview_timer.stop()
        # Debounce: retoma o preview 50ms após o último movimento
        self.resume_timer.start(50)

    def resume_preview(self):
        """Retoma apenas o timer, sem reconectar o hardware da câmera."""
        if self.isVisible() and self.preview_cap:
            self.preview_timer.start(30)

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
            import cv2

            self.preview_cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
            self.preview_timer.start(30)

    def update_preview(self):
        from classes.core.video_processor import VideoProcessor

        mode = self.mode_combo.currentText()
        zoom_val = self.zoom_slider.value()
        pan_x_val = self.pan_x_slider.value() if self.pan_x_slider.isEnabled() else 50
        pan_val = self.pan_slider.value() if self.pan_slider.isEnabled() else 50
        use_avatar = (
            hasattr(self, "btn_preview_avatar") and self.btn_preview_avatar.isChecked()
        )
        avatar_path = self.avatar_input.text().strip()
        avatar_pixmap = (
            QPixmap(avatar_path)
            if avatar_path and os.path.exists(avatar_path)
            else None
        )

        # Mantemos o tamanho da label fixo para suportar o maior preview possível (4:3 -> ~347x260)
        self.preview_label.setFixedSize(350, 260)

        # Calcula tamanho da imagem do preview: Altura fixa em 260
        p_h = 260
        p_h_ratio = 0.75 if "4:3" in mode else 1.0
        p_w = int(p_h / p_h_ratio)

        if use_avatar and avatar_pixmap:
            pixmap = VideoProcessor.create_masked_pixmap(
                avatar_pixmap,
                p_w,
                p_h,
                mode,
                self.color_input.text().strip(),
                border_width=4.0,
            )
        else:
            if not self.preview_cap:
                return
            ret, frame = self.preview_cap.read()
            if not ret:
                return
            qimage = VideoProcessor.process_frame(
                frame, zoom_val, pan_x_val, pan_val, p_w, p_h
            )
            pixmap = VideoProcessor.create_masked_pixmap(
                qimage,
                p_w,
                p_h,
                mode,
                self.color_input.text().strip(),
                border_width=4.0,
            )

        self.preview_label.setPixmap(pixmap)

    def remove_pip_from_list(self, pip_obj):
        if pip_obj in self.active_pips:
            print(f"Removendo camera {pip_obj.cam_index} da lista ativa.")
            self.active_pips.remove(pip_obj)
        if not self.active_pips:
            self.restart_preview()

    def start_pip(self):
        is_multi = self.check_multi_cam.isChecked()
        cam_idx = self.cam_combo.currentData()
        if cam_idx == -1:
            return

        # No modo NORMAL (Single), fechamos as outras antes de abrir a nova
        if not is_multi:
            for pip in list(self.active_pips):
                try:
                    pip.close()
                except:
                    pass
            self.active_pips = []
        else:
            # No modo MULTI, apenas impedimos de abrir a MESMA câmera duas vezes
            for pip in self.active_pips:
                try:
                    if pip.cam_index == cam_idx:
                        pip.activateWindow()
                        pip.show()
                        return
                except RuntimeError:
                    self.active_pips.remove(pip)
                    continue

        self.stop_preview()
        cam_name = self.cam_combo.currentText()
        mode = self.mode_combo.currentText()
        mode_key = f"{cam_name}_{mode}"

        try:
            size = int(self.size_input.text())
        except:  # noqa
            size = 300
        border_color = self.color_input.text().strip() or "#4d6fc4"
        avatar_path = self.avatar_input.text().strip()
        zoom_val = self.zoom_slider.value()
        pan_x_val = self.pan_x_slider.value()
        pan_val = self.pan_slider.value()

        self.save_current_launcher_settings()

        mode_cfg = self.config_manager.get_mode_config(mode_key, mode)
        use_avatar_default = self.btn_preview_avatar.isChecked()

        screen = QGuiApplication.primaryScreen().geometry()  # type: ignore
        center_x = (screen.width() - size) // 2
        center_y = (screen.height() - size) // 2

        # Só usa posição salva se for específica deste mode_key (não de um fallback)
        own_cfg = self.config_manager.configs.get(mode_key, {})
        saved_x = own_cfg.get("x")
        saved_y = own_cfg.get("y")

        # Valida se as coordenadas estão dentro dos limites da tela
        if (
            saved_x is not None
            and saved_y is not None
            and 0 <= saved_x <= screen.width() - size
            and 0 <= saved_y <= screen.height() - size
        ):
            pos_x, pos_y = saved_x, saved_y
        else:
            pos_x, pos_y = center_x, center_y

        self.pip = PipCameraWidget(
            size,
            cam_idx,
            self,
            mode,
            mode_key,
            pos_x,
            pos_y,
            zoom_val,
            pan_x_val,
            pan_val,
            border_color,
            avatar_path,
            use_avatar_default,
            self.border_mode_combo.currentText(),
            (
                self.mic_combo.currentData()
                if self.mic_combo.currentData() is not None
                else -1
            ),
            self.check_mic_muted.isChecked(),
            self.check_hide_toolbar.isChecked(),
            self.check_show_border.isChecked(),
        )

        # Conecta o sinal de fechamento para remover da lista capturando o objeto correto
        current_pip = self.pip
        self.pip.destroyed.connect(lambda: self.remove_pip_from_list(current_pip))

        self.active_pips.append(self.pip)
        self.pip.show()

        if not is_multi:
            self.hide()

    def confirm_reset_settings(self):
        reply = QMessageBox.question(
            self,
            "Confirmar Reset",
            "Deseja realmente apagar todas as configurações e avatares?\nIsso não pode ser desfeito.\nO programa será encerrado após a operação.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.perform_reset()

    def perform_reset(self):
        try:
            from utils.functions import BASE_DIR

            self.stop_preview()

            # Para o timer de salvamento para evitar que ele tente salvar após o delete
            if hasattr(self.config_manager, "_save_timer"):
                self.config_manager._save_timer.stop()

            # Fecha todos os widgets ativos
            for pip in list(self.active_pips):
                try:
                    pip.close()
                except:
                    pass
            self.active_pips = []

            # Apaga a pasta de configurações inteira
            if os.path.exists(BASE_DIR):
                shutil.rmtree(BASE_DIR)
                print(f"Diretório {BASE_DIR} removido com sucesso.")

            QMessageBox.information(
                self,
                "Reset concluído",
                "As configurações foram apagadas.\nO aplicativo será fechado.",
            )
            self.close()
            QGuiApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao resetar: {e}")
