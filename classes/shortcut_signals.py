from PyQt6.QtCore import pyqtSignal, QObject

class ShortcutSignals(QObject):
    resize_signal = pyqtSignal(int)
    toggle_signal = pyqtSignal()
    toggle_avatar_signal = pyqtSignal()
    toggle_mic_signal = pyqtSignal()
    toggle_camera_signal = pyqtSignal()
