from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal


class FloatingToolbar(QWidget):
    # Definimos sinais para que o widget pai responda às ações
    close_requested = pyqtSignal()
    resize_requested = pyqtSignal(int)
    camera_toggled = pyqtSignal()
    mic_toggled = pyqtSignal()
    avatar_toggled = pyqtSignal()
    format_toggled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Row 1
        self.row1 = QHBoxLayout()
        self.btn_minus = self._create_btn("➖")
        self.btn_close = self._create_btn("❌", "background-color: #e74c3c;")
        self.btn_plus = self._create_btn("➕")
        self.row1.addWidget(self.btn_minus)
        self.row1.addWidget(self.btn_close)
        self.row1.addWidget(self.btn_plus)

        # Row 2
        self.row2 = QHBoxLayout()
        self.btn_mic = self._create_btn("🎤")
        self.btn_avatar = self._create_btn("😎")
        self.btn_cam = self._create_btn("🎥")
        self.btn_format = self._create_btn("🖼️")
        self.btn_format.setToolTip("Alternar Formato (Alt+F)")
        self.row2.addWidget(self.btn_mic)
        self.row2.addWidget(self.btn_avatar)
        self.row2.addWidget(self.btn_format)
        self.row2.addWidget(self.btn_cam)

        self.layout.addLayout(self.row1)
        self.layout.addLayout(self.row2)

        # Conexões internas
        self.btn_close.clicked.connect(self.close_requested.emit)
        self.btn_minus.clicked.connect(lambda: self.resize_requested.emit(-20))
        self.btn_plus.clicked.connect(lambda: self.resize_requested.emit(20))
        self.btn_cam.clicked.connect(self.camera_toggled.emit)
        self.btn_mic.clicked.connect(self.mic_toggled.emit)
        self.btn_avatar.clicked.connect(self.avatar_toggled.emit)
        self.btn_format.clicked.connect(self.format_toggled.emit)

        self.hide()

    def _create_btn(self, text, extra_style=""):
        btn = QPushButton(text)
        btn.setFixedSize(32, 32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        style = (
            """
            QPushButton {
                background-color: rgba(45, 45, 45, 230);
                color: white;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 30);
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 70, 255);
                border: 1px solid rgba(255, 255, 255, 80);
            }
        """
            + extra_style
        )
        btn.setStyleSheet(style)
        return btn
