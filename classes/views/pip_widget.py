from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import QTimer, Qt, QPoint
from PyQt6.QtGui import QPixmap
from classes.ui.floating_toolbar import FloatingToolbar
from classes.core.video_processor import VideoProcessor
from classes.core.config_manager import ConfigManager


class PipCameraWidget(QWidget):
    """
    O Widget principal da aplicação (A bolinha da câmera).
    É uma janela sem bordas (FramelessWindowHint) que fica sempre no topo,
    exibindo o processamento em tempo real do feed da câmera com máscaras.
    """

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
        pan_x=50,
        pan_y=50,
        border_color="#4d6fc4",
        avatar_path="",
        use_avatar_default=False,
        border_mode="Cor Sólida",
        mic_device=-1,
        starts_muted=False,
        hide_toolbar=False,
        show_border=True,
    ):
        """
        Inicializa o widget flutuante da câmera.
        
        Args:
            size_val (int): Tamanho base da janela em pixels.
            cam_index (int): Índice da câmera do sistema a ser aberta.
            launcher (Launcher): Referência para a janela de configurações principal.
            mode (str): O formato inicial da máscara (Círculo, Quadrado, etc).
            mode_key (str): Chave usada para salvar as configurações no JSON.
            pos_x (int): Posição inicial X na tela.
            pos_y (int): Posição inicial Y na tela.
            zoom (int): Nível de zoom (100 a 500).
            pan_x (int): Posição horizontal do recorte do zoom.
            pan_y (int): Posição vertical do recorte do zoom.
            border_color (str): Cor inicial da borda.
            avatar_path (str): Caminho para a imagem de avatar (se existir).
            use_avatar_default (bool): Se deve iniciar exibindo o avatar ao invés da câmera.
            border_mode (str): Modo da borda ("Cor Sólida" ou "Sinalizador de Áudio").
            mic_device (int): Índice do dispositivo de microfone selecionado.
            starts_muted (bool): Se o avatar deve iniciar com indicação de mutado.
            hide_toolbar (bool): Se a barra flutuante de ferramentas deve estar desabilitada.
            show_border (bool): Se a borda deve ser desenhada ou não.
        """
        super().__init__()

        # ==========================================
        # Sessão de Inicialização de Estado
        # ==========================================
        self.zoom = zoom
        self.border_color = border_color
        self.current_border_color = border_color
        self.avatar_path = avatar_path
        self.use_avatar = False
        self.border_mode = border_mode
        self.is_mic_muted = starts_muted
        self.hide_toolbar_flag = hide_toolbar
        self.show_border = show_border
        self.config_manager = ConfigManager()
        
        # Estado do áudio
        self.audio_level = 0.0
        self.audio_sensitivity = self.config_manager.configs.get("audio_sensitivity", 2.0)
        self.audio_threshold = self.config_manager.configs.get("audio_threshold", 0.01)
        self.mic_device = mic_device
        self.audio_analyzer = None

        # ==========================================
        # Sessão de Configuração de Módulos (Áudio e Avatar)
        # ==========================================
        if self.border_mode == "Sinalizador de Áudio" and mic_device != -1:
            from classes.core.audio_analyzer import AudioAnalyzer

            self.audio_analyzer = AudioAnalyzer(mic_device)
            self.audio_analyzer.set_sensitivity(self.audio_sensitivity)
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
        self.pan_x = pan_x
        self.pan_y = pan_y

        # Guardamos a posição desejada de forma absoluta
        self.target_pos = QPoint(pos_x, pos_y)

        # ==========================================
        # Sessão de Configuração da Janela (Window Flags)
        # ==========================================
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

        # ==========================================
        # Sessão de Toolbar e Sinais
        # ==========================================
        self.controls_container = FloatingToolbar(self)
        self.controls_container.close_requested.connect(self.close_and_return)
        self.controls_container.resize_requested.connect(self.resize_widget)
        self.controls_container.camera_toggled.connect(self.toggle_camera)
        self.controls_container.mic_toggled.connect(self.toggle_mic)
        self.controls_container.avatar_toggled.connect(self.toggle_avatar)
        self.controls_container.format_toggled.connect(self.toggle_format)
        self.controls_container.border_mode_toggled.connect(self.toggle_border_mode)

        self.controls_container.hide()
        self.update_ui_geometry()

        # ==========================================
        # Sessão de Inicialização de Câmera e Timers
        # ==========================================
        from classes.core.device_manager import DeviceManager
        self.cap = DeviceManager.open_camera(self.cam_index)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Timer para retomar o preview após mover o widget
        self.resume_timer = QTimer()
        self.resume_timer.setSingleShot(True)
        self.resume_timer.timeout.connect(self.resume_preview)

        # Conecta aos sinais globais do launcher gerados pelo HotkeyManager
        if hasattr(self.launcher, "shortcut_manager"):
            mgr = self.launcher.shortcut_manager
            mgr.resize_signal.connect(self.resize_widget)
            mgr.toggle_signal.connect(self.toggle_visibility)
            mgr.toggle_avatar_signal.connect(self.toggle_avatar)
            mgr.toggle_mic_signal.connect(self.toggle_mic)
            mgr.toggle_camera_signal.connect(self.toggle_camera)
            mgr.toggle_format_signal.connect(self.toggle_format)
            mgr.toggle_border_mode_signal.connect(self.toggle_border_mode)
            mgr.toggle_border_visibility_signal.connect(self.toggle_border_visibility)

    # ==========================================
    # Sessão de Ações (Toggles e Controles)
    # ==========================================

    def _on_audio_level_changed(self, level):
        """Atualiza a variável local de nível de áudio ao receber do Analyzer."""
        self.audio_level = level

    def toggle_avatar(self):
        """Alterna a visualização entre a Câmera e a Imagem de Avatar."""
        if self.avatar_pixmap and not self.avatar_pixmap.isNull():
            self.use_avatar = not self.use_avatar
            self.store_current_state()

    def toggle_mic(self):
        """Muta/Desmuta visualmente o microfone, forçando a borda a ficar vermelha."""
        self.is_mic_muted = not self.is_mic_muted
        self.store_current_state()

    def toggle_camera(self):
        """
        Pula para a próxima câmera ativa disponível no sistema, 
        ignorando as que foram filtradas nas configurações.
        """
        try:
            from classes.core.device_manager import DeviceManager

            configs = self.config_manager.reload()
            ignored = configs.get("ignored_cameras", [])

            new_index, new_cam_name = DeviceManager.get_next_available_camera(
                self.cam_index, ignored
            )

            if new_index == -1:
                print("Nenhuma câmera disponível (todas filtradas ou desconectadas).")
                return

            if new_index != self.cam_index:
                # Salva o estado atual da câmera que estamos saindo
                self.store_current_state()

                self.cam_index = new_index

                # Reinicia a captura
                if self.cap:
                    self.cap.release()

                import time

                time.sleep(0.1)  # Breve pausa para o hardware liberar a lente

                self.cap = DeviceManager.open_camera(self.cam_index)

                # Limpa buffer inicial da câmera
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
                self.pan_x = int(mode_cfg.get("pan_x", 50))
                self.pan_y = int(mode_cfg.get("pan_y", 50))

                # Aplica a posição salva para esta câmera (se existir)
                if "x" in mode_cfg and "y" in mode_cfg:
                    self.target_pos = QPoint(int(mode_cfg["x"]), int(mode_cfg["y"]))
                    self.move(self.target_pos)

                # Atualiza a interface (tamanho e geometria)
                self.update_ui_geometry()
                self.update()  # Força redesenho completo
                print(
                    f"Câmera alterada: {new_cam_name} | Zoom: {self.zoom}% | Pan X: {self.pan_x}% | Pan Y: {self.pan_y}%"
                )
        except Exception as e:
            print(f"Erro ao trocar câmera: {e}")

    def toggle_format(self):
        """Alterna entre os formatos disponíveis da janela: Círculo, 1:1, 4:3."""
        modes = ["Círculo", "1:1 (Quadrado)", "4:3 (Retângulo)"]
        try:
            current_idx = modes.index(self.mode)
            next_idx = (current_idx + 1) % len(modes)
        except ValueError:
            next_idx = 0

        # Salva o estado atual ANTES de trocar o formato
        self.store_current_state()

        self.mode = modes[next_idx]

        # Atualiza a chave de modo (mantendo a câmera atual)
        cam_name = self.mode_key.split("_")[0] if "_" in self.mode_key else ""
        if not cam_name:
            # Fallback caso a chave esteja mal formatada
            from classes.core.device_manager import DeviceManager

            all_cams = DeviceManager.get_cameras()
            cam_name = (
                all_cams[self.cam_index] if self.cam_index < len(all_cams) else ""
            )

        self.mode_key = f"{cam_name}_{self.mode}"

        # Carrega as configurações salvas para este novo formato/câmera
        configs = self.config_manager.configs
        mode_cfg = configs.get(self.mode_key, configs.get(self.mode, {}))

        self.base_width = int(mode_cfg.get("size", self.base_width))
        self.zoom = int(mode_cfg.get("zoom", 100))
        self.pan_x = int(mode_cfg.get("pan_x", 50))
        self.pan_y = int(mode_cfg.get("pan_y", 50))

        self.update_ui_geometry()
        self.config_manager.set_global("last_mode", self.mode)
        print(f"Formato alterado para: {self.mode}")

    def toggle_border_mode(self):
        """Alterna entre 'Cor Sólida' e 'Sinalizador de Áudio' (Modo Discord)."""
        if self.border_mode == "Cor Sólida":
            self.border_mode = "Sinalizador de Áudio"
            if not self.audio_analyzer and self.mic_device != -1:
                from classes.core.audio_analyzer import AudioAnalyzer

                self.audio_analyzer = AudioAnalyzer(self.mic_device)
                self.audio_analyzer.set_sensitivity(self.audio_sensitivity)
                self.audio_analyzer.level_changed.connect(self._on_audio_level_changed)
                self.audio_analyzer.start()
            elif self.audio_analyzer:
                self.audio_analyzer.start()
        else:
            self.border_mode = "Cor Sólida"
            if self.audio_analyzer:
                self.audio_analyzer.stop()

        self.config_manager.set_global("border_mode", self.border_mode)
        print(f"Modo de borda alterado para: {self.border_mode}")

    def toggle_border_visibility(self):
        """Ativa ou desativa a renderização visual da borda."""
        self.show_border = not self.show_border

    def toggle_visibility(self):
        """Esconde ou mostra a janela inteira, respeitando posições na tela."""
        if self.isVisible():
            # Antes de esconder, garantimos que a posição atual está salva no target_pos
            self.target_pos = self.pos()
            self.hide()
        else:
            # Ao mostrar, forçamos o movimento para a posição exata onde estava
            self.show()
            self.move(self.target_pos)
            self.activateWindow()

    # ==========================================
    # Sessão de Geometria e Eventos
    # ==========================================

    def showEvent(self, event):
        """Gatilho acionado assim que a janela é exibida."""
        super().showEvent(event)
        self.move(self.target_pos)
        self.activateWindow()
        self.raise_()
        self._initializing = False

    def update_ui_geometry(self):
        """
        Recalcula as proporções reais da janela com base no modo (Círculo, Retângulo)
        e reposiciona a Toolbar no centro exato.
        """
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
        """Aumenta ou diminui a janela respeitando os limites mínimo e máximo."""
        new_size = self.base_width + delta
        if 200 <= new_size <= 800:
            self.base_width = new_size
            self.update_ui_geometry()

    def store_current_state(self):
        """
        Persiste no ConfigManager o estado atual do widget (Posição, tamanho, pan).
        """
        # Ignora apenas se a janela ainda não foi posicionada (coordenadas negativas)
        if self.x() < 0 or self.y() < 0:
            return
        self.target_pos = self.pos()
        self.config_manager.set_mode(
            self.mode_key,
            self.base_width,
            self.zoom,
            self.pan_x,
            self.pan_y,
            self.x(),
            self.y(),
        )
        self.config_manager.set_global("use_avatar", self.use_avatar)

    # ==========================================
    # Sessão de Processamento Gráfico
    # ==========================================

    def update_frame(self):
        """
        Loop de renderização principal chamado pelo QTimer a cada ~30ms.
        Pega o novo frame (ou avatar), processa as cores de borda (áudio/mudo),
        gera as máscaras e exibe no QLabel.
        """
        # Lógica visual para modo de áudio
        if self.border_mode == "Sinalizador de Áudio":
            if self.is_mic_muted:
                self.current_border_color = "#e74c3c" # Vermelho
            else:
                # Verde vivo se passar o threshold, cinza escuro caso contrário
                self.current_border_color = (
                    "#2ecc71" if self.audio_level > self.audio_threshold else "#2d2d2d"
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
                show_border=self.show_border,
            )
        else:
            ret, frame = self.cap.read()
            if not ret:
                return
            qimage = VideoProcessor.process_frame(
                frame, self.zoom, self.pan_x, self.pan_y, self.curr_w, self.curr_h
            )
            pixmap = VideoProcessor.create_masked_pixmap(
                qimage,
                self.curr_w,
                self.curr_h,
                self.mode,
                self.current_border_color,
                show_border=self.show_border,
            )

        self.video_label.setPixmap(pixmap)

    def resume_preview(self):
        """Retoma o processamento de frames após o movimento (para evitar stutters)."""
        if self.isVisible() and self.cap:
            self.timer.start(30)

    # ==========================================
    # Sessão de Controles de Mouse / Teclado
    # ==========================================

    def enterEvent(self, event):
        """Mostra a Toolbar quando o mouse entra."""
        if not self.hide_toolbar_flag:
            self.controls_container.show()

    def leaveEvent(self, event):
        """Esconde a Toolbar quando o mouse sai."""
        if not self.hide_toolbar_flag:
            self.controls_container.hide()

    def mousePressEvent(self, event):
        """Inicia o movimento (drag) do widget."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Atualiza a posição da janela durante o arraste."""
        if self.old_pos:
            # Pausa o processamento durante o arrasto para evitar lags gráficos no SO
            if self.timer.isActive():
                self.timer.stop()

            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Encerra o drag e salva a nova posição final."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None
            self.resume_timer.start(50)  # Retomada com 50ms de delay
            self.store_current_state()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_and_return()

    # ==========================================
    # Sessão de Encerramento
    # ==========================================

    def close_and_return(self):
        """
        Fecha o widget atual limpando recursos e, se aplicável,
        restaura o Launcher.
        """
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
                    mgr.toggle_border_mode_signal.disconnect(self.toggle_border_mode)
                    mgr.toggle_border_visibility_signal.disconnect(
                        self.toggle_border_visibility
                    )
                except:
                    pass

            self.store_current_state()
            if self.audio_analyzer:
                self.audio_analyzer.stop()
            if self.cap:
                self.cap.release()

            self.close()
            # Se não estiver no modo multi-câmeras, volta para o Launcher principal
            if not self.config_manager.get("multi_cam_mode", False):
                self.launcher.refresh_launcher_ui()
                self.launcher.show()
        except Exception as e:
            print(f"Erro ao fechar widget: {e}")
            self.close()
