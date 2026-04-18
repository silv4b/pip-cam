import cv2
import keyboard
from PyQt6.QtWidgets import (
    QLabel,
    QWidget,
    QPushButton,
    QHBoxLayout,
)
from PyQt6.QtCore import QTimer, Qt, QPoint
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QPainter,
    QPainterPath,
    QColor,
    QPen,
)

from classes.shortcut_signals import ShortcutSignals
from utils.functions import save_mode_config, save_global_config


class PipCameraWidget(QWidget):
    def __init__(
        self,
        size_val,
        cam_index,
        launcher,
        mode,
        pos_x,
        pos_y,
        border_color="#4d6fc4",
        avatar_path="",
        use_avatar_default=False,
    ):
        super().__init__()
        self.border_color = border_color
        self.avatar_path = avatar_path
        self.use_avatar = False

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

        # Guardamos a posição desejada de forma absoluta
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

        # Toolbar
        self.controls_container = QWidget(self)
        self.controls_layout = QHBoxLayout(self.controls_container)
        self.controls_layout.setContentsMargins(8, 0, 8, 0)
        self.controls_layout.setSpacing(12)

        self.btn_minus = self.create_button("➖")
        self.btn_close = self.create_button("✕", is_close=True)
        self.btn_plus = self.create_button("➕")

        self.controls_layout.addWidget(self.btn_minus)
        self.controls_layout.addWidget(self.btn_close)
        self.controls_layout.addWidget(self.btn_plus)

        self.btn_minus.clicked.connect(lambda: self.resize_widget(-20))
        self.btn_plus.clicked.connect(lambda: self.resize_widget(20))
        self.btn_close.clicked.connect(self.close_and_return)

        self.controls_container.hide()
        self.update_ui_geometry()

        self.cap = cv2.VideoCapture(self.cam_index, cv2.CAP_DSHOW)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.shortcut_manager = ShortcutSignals()
        self.shortcut_manager.resize_signal.connect(self.resize_widget)
        self.shortcut_manager.toggle_signal.connect(self.toggle_visibility)
        self.shortcut_manager.toggle_avatar_signal.connect(self.toggle_avatar)

        try:
            keyboard.add_hotkey(
                "alt+=", lambda: self.shortcut_manager.resize_signal.emit(20)
            )
            keyboard.add_hotkey(
                "alt+plus", lambda: self.shortcut_manager.resize_signal.emit(20)
            )
            keyboard.add_hotkey(
                "alt+-", lambda: self.shortcut_manager.resize_signal.emit(-20)
            )
            keyboard.add_hotkey(
                "alt+s", lambda: self.shortcut_manager.toggle_signal.emit()
            )
            keyboard.add_hotkey(
                "alt+a", lambda: self.shortcut_manager.toggle_avatar_signal.emit()
            )
        except Exception as e:
            print(f"Erro nos atalhos: {e}")

    def toggle_avatar(self):
        if self.avatar_pixmap and not self.avatar_pixmap.isNull():
            self.use_avatar = not self.use_avatar

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
        # Força a posição no nascimento da janela
        self.move(self.target_pos)
        self._initializing = False

    def create_button(self, icon_text, is_close=False):
        btn = QPushButton(icon_text)
        btn.setFixedSize(32, 32)
        bg = "rgba(220, 50, 50, 200)" if is_close else "rgba(40, 40, 40, 180)"
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {bg}; color: white; border-radius: 16px; border: 1px solid rgba(255,255,255,60); font-weight: bold; }}"  # noqa
        )
        return btn

    def update_ui_geometry(self):
        h_ratio = 0.75 if "4:3" in self.mode else 1.0
        self.curr_w = self.base_width
        self.curr_h = int(self.base_width * h_ratio)

        self.setFixedSize(self.curr_w, self.curr_h)
        self.video_label.setGeometry(0, 0, self.curr_w, self.curr_h)

        container_w, container_h = 150, 50
        margin_bottom = 25 if self.mode == "Círculo" else 15

        self.controls_container.setGeometry(
            int((self.curr_w - container_w) / 2),
            int(self.curr_h - container_h - margin_bottom),
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
        # Atualizamos o target_pos toda vez que salvamos para manter a consistência com o Alt+S
        self.target_pos = self.pos()
        save_mode_config(self.mode, self.base_width, self.x(), self.y())
        save_global_config("use_avatar", self.use_avatar)

    def update_frame(self):
        if self.use_avatar and self.avatar_pixmap:
            # Scalamos mantendo o aspecto, porém cobrindo toda a área
            scaled_avatar = self.avatar_pixmap.scaled(
                self.curr_w,
                self.curr_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Como usamos KeepAspectRatioByExpanding, pode haver sobras horizontais ou verticais
            x_offset = (scaled_avatar.width() - self.curr_w) // 2
            y_offset = (scaled_avatar.height() - self.curr_h) // 2
            cropped_avatar = scaled_avatar.copy(
                x_offset, y_offset, self.curr_w, self.curr_h
            )

            self.draw_final_pixmap(cropped_avatar)
            return

        ret, frame = self.cap.read()
        if ret:
            h_f, w_f, _ = frame.shape
            target_ratio = self.curr_w / self.curr_h
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
                self.curr_w,
                self.curr_h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.draw_final_pixmap(pixmap)

    def draw_final_pixmap(self, base_pixmap):
        out_pixmap = QPixmap(self.curr_w, self.curr_h)
        out_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(out_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        border_w = 6.0
        clip_margin = 2.0

        video_path = QPainterPath()
        if self.mode == "Círculo":
            video_path.addEllipse(
                clip_margin,
                clip_margin,
                self.curr_w - 2 * clip_margin,
                self.curr_h - 2 * clip_margin,
            )
        else:
            video_path.addRoundedRect(
                clip_margin,
                clip_margin,
                self.curr_w - 2 * clip_margin,
                self.curr_h - 2 * clip_margin,
                25 - clip_margin,
                25 - clip_margin,
            )

        painter.setClipPath(video_path)
        painter.drawPixmap(0, 0, base_pixmap)

        # Desativa o clip para que a borda seja desenhada inteira
        painter.setClipping(False)

        # Path da borda desenhado para caber na janela (evitando lados retos)
        border_path = QPainterPath()
        offset = border_w / 2.0
        if self.mode == "Círculo":
            border_path.addEllipse(
                offset, offset, self.curr_w - border_w, self.curr_h - border_w
            )
        else:
            border_path.addRoundedRect(
                offset,
                offset,
                self.curr_w - border_w,
                self.curr_h - border_w,
                25 - offset,
                25 - offset,
            )

        # Desenha a borda com a cor escolhida
        pen = QPen(QColor(self.border_color))
        pen.setWidthF(border_w)
        painter.setPen(pen)
        painter.drawPath(border_path)

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
        try:
            keyboard.remove_all_hotkeys()
        except:  # noqa
            pass
        self.store_current_state()
        self.cap.release()
        self.close()
        self.launcher.refresh_launcher_ui()
        self.launcher.show()
