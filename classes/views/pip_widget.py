import cv2
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import QTimer, Qt, QPoint
from PyQt6.QtGui import QPixmap
from classes.core.audio_analyzer import AudioAnalyzer
from classes.ui.floating_toolbar import FloatingToolbar
from classes.core.video_processor import VideoProcessor
from classes.core.config_manager import ConfigManager


class PipCameraWidget(QWidget):
    def __init__(
        self,
        size_val,
        cam_index,
        launcher,
        mode,
        mode_key,
        pos_x,
        pos_y,
        zoom=100,
        pan_y=50,
        border_color="#4d6fc4",
        avatar_path="",
        use_avatar_default=False,
        border_mode="Cor Sólida",
        mic_device=-1,
        starts_muted=False,
        hide_toolbar=False,
    ):
        super().__init__()
        self.zoom = zoom
        self.border_color = border_color
        self.current_border_color = border_color
        self.avatar_path = avatar_path
        self.use_avatar = False
        self.border_mode = border_mode
        self.is_mic_muted = starts_muted
        self.hide_toolbar_flag = hide_toolbar
        self.audio_level = 0.0

        self.config_manager = ConfigManager()
        self.audio_analyzer = None
        if self.border_mode == "Sinalizador de Áudio" and mic_device != -1:
            self.audio_analyzer = AudioAnalyzer(mic_device)
            self.audio_analyzer.level_changed.connect(self._on_audio_level_changed)
            self.audio_analyzer.start()

        # Carrega o avatar se existir
        self.avatar_pixmap = None
        import os

        if self.avatar_path and os.path.exists(self.avatar_path):
            self.avatar_pixmap = QPixmap(self.avatar_path)
            if not self.avatar_pixmap.isNull():
                self.use_avatar = use_avatar_default

        self.launcher = launcher
        self.base_width = size_val
        self.cam_index = cam_index
        self.mode = mode
        self.mode_key = mode_key
        self.pan_y = pan_y

        # Guardamos a posição desejada de forma absoluta
        self.target_pos = QPoint(pos_x, pos_y)

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.old_pos = None
        self._initializing = True

        self.video_label = QLabel(self)
        self.video_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.controls_container = FloatingToolbar(self)
        self.controls_container.close_requested.connect(self.close_and_return)
        self.controls_container.resize_requested.connect(self.resize_widget)
        self.controls_container.camera_toggled.connect(self.toggle_camera)
        self.controls_container.mic_toggled.connect(self.toggle_mic)
        self.controls_container.avatar_toggled.connect(self.toggle_avatar)
        self.controls_container.format_toggled.connect(self.toggle_format)

        self.controls_container.hide()
        self.update_ui_geometry()

        self.cap = cv2.VideoCapture(self.cam_index, cv2.CAP_DSHOW)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Conecta aos sinais globais do launcher
        if hasattr(self.launcher, "shortcut_manager"):
            mgr = self.launcher.shortcut_manager
            mgr.resize_signal.connect(self.resize_widget)
            mgr.toggle_signal.connect(self.toggle_visibility)
            mgr.toggle_avatar_signal.connect(self.toggle_avatar)
            mgr.toggle_mic_signal.connect(self.toggle_mic)
            mgr.toggle_camera_signal.connect(self.toggle_camera)
            mgr.toggle_format_signal.connect(self.toggle_format)

    def _on_audio_level_changed(self, level):
        self.audio_level = level

    def toggle_avatar(self):
        if self.avatar_pixmap and not self.avatar_pixmap.isNull():
            self.use_avatar = not self.use_avatar
            self.store_current_state()

    def toggle_mic(self):
        self.is_mic_muted = not self.is_mic_muted
        self.store_current_state()

    def toggle_camera(self):
        try:
            from classes.core.device_manager import DeviceManager

            all_devices = DeviceManager.get_cameras()
            configs = self.config_manager.reload()
            ignored = configs.get("ignored_cameras", [])

            # Filtra as câmeras válidas (que não estão na lista de ignoradas)
            devices = [d for d in all_devices if d not in ignored]

            if not devices:
                print("Nenhuma câmera disponível (todas filtradas ou desconectadas).")
                return

            # Se houver mais de uma câmera disponível, ou se a atual não estiver na lista filtrada
            # (ocorre se acabamos de ignorar a câmera que estava ativa)
            current_cam_name = all_devices[self.cam_index] if self.cam_index < len(all_devices) else ""
            
            if len(devices) > 1 or (len(devices) == 1 and current_cam_name not in devices):
                # Salva o estado atual da câmera que estamos saindo
                self.store_current_state()

                try:
                    current_idx_in_filtered = devices.index(current_cam_name)
                    next_idx_in_filtered = (current_idx_in_filtered + 1) % len(devices)
                except ValueError:
                    next_idx_in_filtered = 0

                new_cam_name = devices[next_idx_in_filtered]
                new_index = DeviceManager.get_camera_index(new_cam_name)

                self.cam_index = new_index

                # Reinicia a captura
                if self.cap:
                    self.cap.release()

                import time

                time.sleep(0.1)  # Breve pausa para o hardware liberar a lente

                self.cap = cv2.VideoCapture(self.cam_index, cv2.CAP_DSHOW)

                # Limpa buffer inicial
                for _ in range(5):
                    self.cap.grab()

                # Garante que as propriedades de transparência não se percam
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                self.video_label.setAttribute(
                    Qt.WidgetAttribute.WA_TranslucentBackground
                )

                self.mode_key = f"{new_cam_name}_{self.mode}"

                # Carrega as configurações específicas da nova câmera
                mode_cfg = configs.get(self.mode_key, configs.get(self.mode, {}))

                # Garante que os valores sejam tipos corretos
                self.base_width = int(mode_cfg.get("size", self.base_width))
                self.zoom = int(mode_cfg.get("zoom", 100))
                self.pan_y = int(mode_cfg.get("pan_y", 50))

                # Aplica a posição salva para esta câmera (se existir)
                if "x" in mode_cfg and "y" in mode_cfg:
                    self.target_pos = QPoint(int(mode_cfg["x"]), int(mode_cfg["y"]))
                    self.move(self.target_pos)

                # Atualiza a interface (tamanho e geometria)
                self.update_ui_geometry()
                self.update()  # Força redesenho completo
                print(
                    f"Câmera alterada: {new_cam_name} | Zoom: {self.zoom}% | Pan Y: {self.pan_y}%"
                )
        except Exception as e:
            print(f"Erro ao trocar câmera: {e}")

    def toggle_format(self):
        """Alterna entre os formatos disponíveis: Círculo, 1:1, 4:3."""
        modes = ["Círculo", "1:1 (Quadrado)", "4:3 (Retângulo)"]
        try:
            current_idx = modes.index(self.mode)
            next_idx = (current_idx + 1) % len(modes)
        except ValueError:
            next_idx = 0

        self.mode = modes[next_idx]
        
        # Atualiza a chave de modo (mantendo a câmera atual)
        cam_name = self.mode_key.split("_")[0] if "_" in self.mode_key else ""
        if not cam_name:
             # Fallback caso a chave esteja mal formatada
             from classes.core.device_manager import DeviceManager
             all_cams = DeviceManager.get_cameras()
             cam_name = all_cams[self.cam_index] if self.cam_index < len(all_cams) else ""

        self.mode_key = f"{cam_name}_{self.mode}"
        
        # Carrega as configurações salvas para este novo formato/câmera
        configs = self.config_manager.configs
        mode_cfg = configs.get(self.mode_key, configs.get(self.mode, {}))

        self.base_width = int(mode_cfg.get("size", self.base_width))
        self.zoom = int(mode_cfg.get("zoom", 100))
        self.pan_y = int(mode_cfg.get("pan_y", 50))

        if "x" in mode_cfg and "y" in mode_cfg:
            self.target_pos = QPoint(int(mode_cfg["x"]), int(mode_cfg["y"]))
            self.move(self.target_pos)

        self.update_ui_geometry()
        self.config_manager.set_global("last_mode", self.mode)
        print(f"Formato alterado para: {self.mode}")

    def toggle_visibility(self):
        if self.isVisible():
            # Antes de esconder, garantimos que a posição atual está salva no target_pos
            self.target_pos = self.pos()
            self.hide()
        else:
            # Ao mostrar, forçamos o movimento para a posição exata onde estava
            self.show()
            self.move(self.target_pos)
            self.activateWindow()

    def showEvent(self, event):
        super().showEvent(event)
        self.move(self.target_pos)
        self.activateWindow()
        self.raise_()
        self._initializing = False

    def update_ui_geometry(self):
        h_ratio = 0.75 if "4:3" in self.mode else 1.0
        self.curr_w = self.base_width
        self.curr_h = int(self.base_width * h_ratio)

        self.setFixedSize(self.curr_w, self.curr_h)
        self.video_label.setGeometry(0, 0, self.curr_w, self.curr_h)

        container_w, container_h = 175, 85

        # Centraliza o container de botões exatamente no meio do widget
        self.controls_container.setGeometry(
            int((self.curr_w - container_w) / 2),
            int((self.curr_h - container_h) / 2),
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
        self.config_manager.set_mode(
            self.mode_key, self.base_width, self.zoom, self.pan_y, self.x(), self.y()
        )
        self.config_manager.set_global("use_avatar", self.use_avatar)

    def update_frame(self):
        if self.border_mode == "Sinalizador de Áudio":
            if self.is_mic_muted:
                self.current_border_color = "#e74c3c"
            else:
                self.current_border_color = (
                    "#2ecc71" if self.audio_level > 0.015 else "#2d2d2d"
                )
        else:
            self.current_border_color = self.border_color

        if self.use_avatar and self.avatar_pixmap:
            pixmap = VideoProcessor.create_masked_pixmap(
                self.avatar_pixmap,
                self.curr_w,
                self.curr_h,
                self.mode,
                self.current_border_color,
            )
        else:
            ret, frame = self.cap.read()
            if not ret:
                return
            qimage = VideoProcessor.process_frame(
                frame, self.zoom, self.pan_y, self.curr_w, self.curr_h
            )
            pixmap = VideoProcessor.create_masked_pixmap(
                qimage, self.curr_w, self.curr_h, self.mode, self.current_border_color
            )

        self.video_label.setPixmap(pixmap)

    def enterEvent(self, event):
        if not self.hide_toolbar_flag:
            self.controls_container.show()

    def leaveEvent(self, event):
        if not self.hide_toolbar_flag:
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
        try:
            # Desconecta os sinais globais para não receber ordens após fechar
            if hasattr(self.launcher, "shortcut_manager"):
                mgr = self.launcher.shortcut_manager
                try:
                    mgr.resize_signal.disconnect(self.resize_widget)
                    mgr.toggle_signal.disconnect(self.toggle_visibility)
                    mgr.toggle_avatar_signal.disconnect(self.toggle_avatar)
                    mgr.toggle_mic_signal.disconnect(self.toggle_mic)
                    mgr.toggle_camera_signal.disconnect(self.toggle_camera)
                    mgr.toggle_format_signal.disconnect(self.toggle_format)
                except:
                    pass

            self.store_current_state()
            if self.audio_analyzer:
                self.audio_analyzer.stop()
            if self.cap:
                self.cap.release()

            self.close()
            # Se não estiver no modo multi-câmeras, volta para o Launcher
            if not self.config_manager.get("multi_cam_mode", False):
                self.launcher.refresh_launcher_ui()
                self.launcher.show()
        except Exception as e:
            print(f"Erro ao fechar widget: {e}")
            self.close()
